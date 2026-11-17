"""Orquestrador do chat: rotas reais, orientações verificadas e classificador local.

Não inventa linhas, tarifas, acessibilidade ou referências oficiais.
Não guarda mensagens, GPS ou histórico do usuário no servidor.
"""
from __future__ import annotations

import re
import unicodedata

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .core import carregar, responder
from .enderecos_api import Coordenadas, RotaRealPedido, rota_real
from .assistente.rotas_api import preparar_modelo
from .assistente.previsao import prever
from .documentos_transporte import consultar_documentos, escopo, resposta_limite, bloqueado
from .avaliacao_cidada import CASOS
import json

router = APIRouter(prefix="/agente", tags=["Agente Cidadão"])

class ConversaEntrada(BaseModel):
    pergunta: str = Field(min_length=3, max_length=300)
    origem: Coordenadas | None = None
    destino: Coordenadas | None = None
    modal: str = Field(default="todos", pattern=r"^(todos|onibus|ferroviario|ape)$")
    priorizar_menos_caminhada: bool = False
    evitar_escadas: bool = False


def normalizar(texto: str) -> str:
    simples = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in simples if not unicodedata.combining(c))


def pede_trajeto(texto: str) -> bool:
    """Somente solicitações de viagem; dúvidas de como usar o app seguem no FAQ."""
    s = normalizar(texto)
    padroes = (
        r"\bcomo (eu )?cheg(ar|o)\b", r"\bcomo ir\b", r"\bqual (onibus|metro|trem) (pego|pegar|devo pegar)\b",
        r"\b(trajeto|rota|caminho) (de .+ )?para\b", r"\bme leve\b", r"\bme mostra (a )?rota\b",
        r"\btrace (uma )?rota\b", r"\bcalcule (a |uma )?rota\b",
    )
    return any(re.search(p, s) for p in padroes)


def resumo_rota(rota: dict) -> str:
    etapas = []
    for trecho in rota.get("trechos", []):
        modo = trecho.get("modal")
        nome = trecho.get("linha")
        de, para = trecho.get("de", "Origem"), trecho.get("para", "Destino")
        if modo == "WALK":
            etapas.append(f"Caminhe de {de} até {para}.")
        elif modo == "BUS":
            etapas.append(f"Pegue o ônibus {nome or '(linha não informada)'} em {de} e desça em {para}.")
        else:
            etapas.append(f"Use {nome or 'o transporte ferroviário'} de {de} até {para}.")
    if not etapas:
        return "A rota foi consultada, mas não há instruções detalhadas disponíveis."
    return (f"Viagem estimada: {rota.get('tempo_min', '?')} minutos. "
            + " ".join(etapas[:8])
            + (" Há outras etapas no painel de trajetos." if len(etapas) > 8 else ""))


@router.get("/perguntas-academicas")
def perguntas_academicas():
    """Cenários preparados pela equipe conforme o enunciado, não questões oficiais da FIAP."""
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    return [{"numero": i, "pergunta": caso["pergunta"],
             "categoria": "Consulta" if caso["status_esperado"] == "ok" else "Limitação"}
            for i, caso in enumerate(casos, 1)]


@router.post("/conversar")
def conversar(body: ConversaEntrada):
    pergunta = body.pergunta.strip()
    if len(pergunta) < 3:
        raise HTTPException(status_code=422, detail="Digite uma pergunta com pelo menos 3 caracteres.")

    # Recusa explícita fora do escopo antes de executar ferramentas de rota.
    # Consultas sobre o próprio aplicativo continuam disponíveis.
    if bloqueado(pergunta) or (not escopo(pergunta) and not pede_trajeto(pergunta) and not re.search(r"\b(aplicativo|app|planejador)\b", normalizar(pergunta))):
        return resposta_limite("Meu atendimento é exclusivo para transporte público, mobilidade urbana, tarifas, benefícios e acessibilidade.", "fora_escopo")

    if pede_trajeto(pergunta):
        if body.origem is None or body.destino is None:
            return {
                "resposta": "Para calcular a viagem, selecione a origem e o destino nos campos do planejador (ou use Minha localização), escolha o transporte e pergunte novamente.",
                "origem_resposta": "orientacao_do_app", "fontes": [],
                "sugestoes": ["Como escolher meu ponto de partida?", "Como marcar o destino no mapa?"],
                "aviso": "Ainda não foi calculada uma rota.",
                "rota": None,
            }
        pergunta_normal = normalizar(pergunta)
        modal_pergunta = (
            "onibus" if re.search(r"\b(onibus|busao)\b", pergunta_normal) else
            "ferroviario" if re.search(r"\b(metro|trem)\b", pergunta_normal) else
            body.modal
        )
        try:
            rota = rota_real(RotaRealPedido(
                origem=body.origem, destino=body.destino, modal=modal_pergunta,
                priorizar_menos_caminhada=body.priorizar_menos_caminhada,
                evitar_escadas=body.evitar_escadas,
            ))
        except HTTPException as exc:
            return {
                "resposta": "Não encontrei um itinerário real para esses pontos e esse transporte. Experimente outro modal ou revise os endereços selecionados.",
                "origem_resposta": "rota_indisponivel", "fontes": [],
                "sugestoes": ["Como escolher outro transporte?"],
                "aviso": str(exc.detail), "rota": None,
            }
        return {
            "resposta": resumo_rota(rota), "origem_resposta": "motor_rotas",
            "fontes": [{"referencia": rota.get("fonte", "Serviço de roteamento"), "data_verificacao": ""}],
            "sugestoes": [], "aviso": rota.get("aviso"), "rota": rota,
        }

    # O núcleo acadêmico permanece independente para preservar a avaliação A/B.
    # A interface livre pesquisa também a coleção documental complementar.
    try:
        registros = carregar()
        resultado = consultar_documentos(pergunta, registros)
        if resultado["origem_resposta"] in {"documento_oficial", "ambiguo"}:
            return resultado
        # Preservar o contrato de resposta verificada do núcleo para consultas
        # sem desambiguação documental suficiente.
        verificada = responder(pergunta, registros, "B")
        if verificada["status"] == "ok" and escopo(pergunta):
            return {
                "resposta": verificada["resposta"], "origem_resposta": "base_verificada",
                "fontes": verificada["fontes"], "sugestoes": [],
                "aviso": None, "rota": None,
            }
    except ValueError:
        return resposta_limite("A base de orientações está indisponível. Consulte os canais oficiais.")

    # O classificador de funcionalidades só recebe perguntas sobre o app;
    # nunca é usado para inventar informações sobre operadores.
    if not re.search(r"\b(aplicativo|app|planejador)\b", normalizar(pergunta)):
        return resultado

    modelo = preparar_modelo()
    if modelo is None:
        return {
            "resposta": "O agente está temporariamente indisponível. Você ainda pode calcular rotas pelo planejador.",
            "origem_resposta": "indisponivel", "fontes": [], "sugestoes": [],
            "aviso": "O modelo local não pôde ser carregado.", "rota": None,
        }
    p = prever(pergunta, modelo)
    # A base do classificador explica funcionalidades do app, não regras
    # oficiais. Nunca apresentar classificação como fonte de direitos/tarifas.
    if p.intencao_id is None:
        return {
            "resposta": p.resposta, "origem_resposta": "sem_resposta_verificada",
            "fontes": [], "sugestoes": p.sugestoes, "aviso": None, "rota": None,
        }
    if p.tema not in {"rota", "tarifas", "historico", "privacidade"}:
        return {
            "resposta": "Não encontrei informação cidadã verificada para essa pergunta. Consulte o órgão responsável.",
            "origem_resposta": "sem_resposta_verificada",
            "fontes": [], "sugestoes": p.sugestoes, "aviso": None, "rota": None,
        }
    return {
        "resposta": p.resposta,
        "origem_resposta": "classificador_academico",
        "fontes": [],
        "sugestoes": p.sugestoes,
        "aviso": "Informação sobre o protótipo acadêmico; não é orientação oficial nem tarifa confirmada.",
        "rota": None,
    }
