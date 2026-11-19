"""Histórico opcional de interações, separado do motor acadêmico.

Sem configuração de PostgreSQL ou sem consentimento, nenhuma gravação.
Não registra IP, GPS ou outros campos do pedido.
"""
from __future__ import annotations

import hmac
import os
import re
import unicodedata
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/agente/historico", tags=["Histórico IA"])
RETENCAO_DIAS = 30
POSITIVOS = {"base_verificada", "documento_oficial", "motor_rotas", "orientacao_do_app", "classificador_academico"}

# Texto livre pode conter informações inesperadas. Se houver indícios de dados
# pessoais/sensíveis, retém somente estatística; não promete anonimização.
SENSIVEL = re.compile(
    r"\b(cpf|rg|cnpj|email|e-mail|telefone|celular|whatsapp|senha|cep|endereco|"
    r"moro|resido|minha casa|meu nome|nome completo|diagnostico|doenca|laudo|"
    r"prontuario|medicamento|deficiencia|cadeirante|pcd|saude|autismo|cid|"
    r"rua|avenida|travessa|alameda|numero da casa|localizacao|gps)\b|"
    r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|\d{3}\.?\d{3}\.?\d{3}-?\d{2}|"
    r"(?:\+?55\s*)?(?:\(?\d{2}\)?[\s.-]*)?\d{4,5}[\s.-]*\d{4}|"
    r"-?\d{1,3}\.\d{3,}\s*[,; ]\s*-?\d{1,3}\.\d{3,}", re.I
)
ROTA_PRIVADA = re.compile(r"\b(como (?:eu )?(?:ir|chegar)|me leve|rota|trajeto|caminho|"
                          r"de onde|partindo|ponto de partida|destino)\b", re.I)

def normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.casefold()) if not unicodedata.combining(c))

def database_url():
    return os.environ.get("CHAT_HISTORY_DATABASE_URL", "").strip()

def conectar():
    # Import tardio: testes e execução sem banco continuam funcionando.
    import psycopg
    return psycopg.connect(database_url(), connect_timeout=4,
                           options="-c statement_timeout=4000 -c lock_timeout=2000")

def preparar(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS citizen_ia_interacoes (
            id UUID PRIMARY KEY,
            sessao UUID NOT NULL,
            pergunta TEXT,
            resposta TEXT,
            categoria VARCHAR(40),
            origem_resposta VARCHAR(50) NOT NULL,
            respondida BOOLEAN NOT NULL,
            texto_omitido BOOLEAN NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS citizen_ia_data_idx ON citizen_ia_interacoes(criado_em)")
    cur.execute("CREATE INDEX IF NOT EXISTS citizen_ia_sessao_idx ON citizen_ia_interacoes(sessao)")

def purgar(cur):
    cur.execute("DELETE FROM citizen_ia_interacoes WHERE criado_em < NOW() - INTERVAL '30 days'")

def dados_interacao(pergunta, resultado):
    origem = str(resultado.get("origem_resposta") or "desconhecida")[:50]
    resposta = str(resultado.get("resposta") or "")
    categoria = resultado.get("tema_contexto")
    categorias = {"rota", "gratuidade", "gratuidade_pcd", "cartoes", "acessibilidade", "tarifas", "direitos", "servicos", "integracao", "privacidade"}
    categoria = categoria if categoria in categorias else None
    # Não persistir endereços possíveis de rotas, inclusive dados vindos do provedor.
    omitido = bool(resultado.get("rota") or origem in {"motor_rotas", "rota_indisponivel"}
                    or categoria == "rota" or ROTA_PRIVADA.search(normalizar(pergunta))
                    or SENSIVEL.search(normalizar(pergunta + " " + resposta)))
    return (None if omitido else pergunta[:300], None if omitido else resposta[:8000],
            categoria, origem, origem in POSITIVOS, omitido)

def registrar(pergunta, resultado, consentimento=False, sessao=None):
    if not consentimento:
        return {"status": "desativado"}
    if not database_url():
        return {"status": "indisponivel"}
    sessao = sessao or uuid4()
    dados = dados_interacao(pergunta, resultado)
    try:
        with conectar() as conn:
            with conn.cursor() as cur:
                preparar(cur)
                purgar(cur)
                cur.execute("""
                    INSERT INTO citizen_ia_interacoes
                    (id, sessao, pergunta, resposta, categoria, origem_resposta, respondida, texto_omitido)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (uuid4(), sessao, *dados))
        return {"status": "salvo", "sessao": str(sessao), "texto_omitido": dados[-1]}
    except Exception:
        # Nunca registrar texto da interação, credenciais ou erro detalhado.
        return {"status": "indisponivel"}

class SessaoEntrada(BaseModel):
    sessao: UUID

@router.post("/apagar")
def apagar(entrada: SessaoEntrada):
    if not database_url():
        raise HTTPException(503, "Histórico indisponível.")
    try:
        with conectar() as conn:
            with conn.cursor() as cur:
                preparar(cur)
                cur.execute("DELETE FROM citizen_ia_interacoes WHERE sessao = %s", (entrada.sessao,))
        return {"status": "apagado"}
    except Exception:
        raise HTTPException(503, "Não foi possível excluir o histórico.") from None

def autorizar(authorization):
    token = os.environ.get("CHAT_HISTORY_ADMIN_TOKEN", "").strip()
    if len(token) < 32 or not authorization or not hmac.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(401, "Acesso não autorizado.")
    if not database_url():
        raise HTTPException(503, "Histórico indisponível.")

@router.get("/admin")
def consultar_admin(limit: int = 100, offset: int = 0, authorization: str | None = Header(default=None)):
    autorizar(authorization)
    limit, offset = max(1, min(500, limit)), max(0, offset)
    try:
        from psycopg.rows import dict_row
        with conectar() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                preparar(cur)
                purgar(cur)
                cur.execute("""SELECT count(*) AS total, count(*) FILTER (WHERE respondida) AS respondidas,
                    count(*) FILTER (WHERE texto_omitido) AS textos_omitidos FROM citizen_ia_interacoes""")
                resumo = cur.fetchone()
                cur.execute("""SELECT coalesce(categoria, 'sem_categoria') AS categoria, count(*) AS total
                    FROM citizen_ia_interacoes GROUP BY 1 ORDER BY 2 DESC, 1""")
                categorias = cur.fetchall()
                cur.execute("""SELECT id, sessao, pergunta, resposta, categoria, origem_resposta,
                    respondida, texto_omitido, criado_em FROM citizen_ia_interacoes
                    ORDER BY criado_em DESC, id DESC LIMIT %s OFFSET %s""", (limit, offset))
                return {"resumo": resumo, "categorias": categorias, "interacoes": cur.fetchall(),
                        "limit": limit, "offset": offset, "retencao_dias": RETENCAO_DIAS}
    except Exception:
        raise HTTPException(503, "Não foi possível consultar o histórico.") from None

def limpar_expirados():
    if database_url():
        with conectar() as conn:
            with conn.cursor() as cur:
                preparar(cur)
                purgar(cur)

if __name__ == "__main__":
    limpar_expirados()
