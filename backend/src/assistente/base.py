"""Módulo de coleta e validação da base de conhecimento do assistente (etapa 6.1).

Lê base_conhecimento.json e perguntas_teste.json e aplica as regras V-01 a V-10 e A-01 a A-06
da especificação. Qualquer violação levanta ValueError: o assistente não inicia com base inválida.
"""
import json
import re
from pathlib import Path
from typing import Any

from .config import (
    CAMINHO_BASE,
    CAMINHO_PERGUNTAS_TESTE,
    FRASES_POR_INTENCAO,
    N_INTENCOES,
    PALAVRAS_PROIBIDAS,
    RAIZ_REPOSITORIO,
    RESPOSTA_MAX_CARACTERES,
    RESPOSTA_MAX_FRASES,
    TEXTO_AVISO_TARIFAS,
    resolver_caminho,
)
from .preprocessamento import normalizar_para_comparacao

VERSAO_BASE_ESPERADA = "1.0"
N_PERGUNTAS_TESTE = 12
PREFIXO_PLANEJADA = "Ainda não está disponível nesta versão:"
EXPRESSAO_PARCIAL = "nesta versão"
STATUS_PERMITIDOS = ("implementada", "parcial", "planejada")

# Tabela 7.4 da especificação: id -> tema
TEMAS_ESPERADOS = {
    "R01": "rota", "R02": "rota", "R03": "rota", "R04": "rota", "R05": "rota",
    "T01": "tarifas", "T02": "tarifas", "T03": "tarifas", "T04": "tarifas", "T05": "tarifas",
    "H01": "historico_privacidade", "H02": "historico_privacidade", "H03": "historico_privacidade",
    "H04": "historico_privacidade", "H05": "historico_privacidade",
}
IDS_ESPERADOS = tuple(TEMAS_ESPERADOS)
CAMPOS_INTENCAO = frozenset({
    "id", "tema", "pergunta_canonica", "frases_treino", "resposta",
    "status_funcionalidade", "fontes_no_repositorio", "revisada_pela_equipe",
})


def contar_frases(texto: str) -> int:
    """Conta frases delimitadas por ponto, exclamação ou interrogação."""
    partes = re.split(r"(?<=[.!?])\s+", texto.strip())
    return len([p for p in partes if p.strip()])


def _palavra_proibida_em(texto: str):
    for proibida in PALAVRAS_PROIBIDAS:
        if re.search(rf"\b{re.escape(proibida)}\b", texto, flags=re.IGNORECASE):
            return proibida
    return None


def _validar_testes(dados_testes: Any) -> set:
    """Valida o arquivo de perguntas de teste e devolve o conjunto normalizado das perguntas."""
    if not isinstance(dados_testes, list):
        raise ValueError("O arquivo de perguntas de teste deve ser uma lista.")
    if len(dados_testes) != N_PERGUNTAS_TESTE:
        raise ValueError(f"O arquivo de perguntas de teste deve ter exatamente {N_PERGUNTAS_TESTE} itens.")
    normalizadas = set()
    for item in dados_testes:
        if not isinstance(item, dict) or set(item) != {"pergunta", "intencao_esperada"}:
            raise ValueError("Cada pergunta de teste deve ter exatamente os campos 'pergunta' e 'intencao_esperada'.")
        if not isinstance(item["pergunta"], str) or not item["pergunta"].strip():
            raise ValueError("Pergunta de teste vazia ou inválida.")
        if item["intencao_esperada"] not in TEMAS_ESPERADOS:
            raise ValueError(f"Intenção esperada desconhecida: {item['intencao_esperada']}")
        normalizadas.add(normalizar_para_comparacao(item["pergunta"]))
    return normalizadas


def validar_base(dados_base: Any, dados_testes: Any, raiz_repositorio: Path | None = None) -> None:
    """Aplica V-01 a V-10 e A-01 a A-06. Levanta ValueError na primeira violação."""
    raiz = Path(raiz_repositorio) if raiz_repositorio is not None else RAIZ_REPOSITORIO
    testes_normalizados = _validar_testes(dados_testes)

    # V-01: estrutura geral, 15 intenções, IDs exatamente os esperados e sem repetição
    if not isinstance(dados_base, dict):
        raise ValueError("A base deve ser um dicionário JSON.")
    if dados_base.get("versao") != VERSAO_BASE_ESPERADA:
        raise ValueError(f"A base deve ter o campo 'versao' igual a '{VERSAO_BASE_ESPERADA}'.")
    intencoes = dados_base.get("intencoes")
    if not isinstance(intencoes, list):
        raise ValueError("O campo 'intencoes' deve ser uma lista.")
    if len(intencoes) != N_INTENCOES:
        raise ValueError(f"V-01: a base deve ter exatamente {N_INTENCOES} intenções, mas tem {len(intencoes)}.")
    for item in intencoes:
        if not isinstance(item, dict) or set(item) != CAMPOS_INTENCAO:
            raise ValueError(f"V-01: cada intenção deve ter exatamente os campos {sorted(CAMPOS_INTENCAO)}.")
    ids = [item["id"] for item in intencoes]
    if len(set(ids)) != len(ids) or set(ids) != set(IDS_ESPERADOS):
        raise ValueError("V-01: os IDs das intenções devem ser exatamente R01-R05, T01-T05 e H01-H05, sem repetição.")

    # V-02: 5 intenções por tema e tema coerente com o ID
    contagem_temas: dict = {}
    for item in intencoes:
        if item["tema"] != TEMAS_ESPERADOS[item["id"]]:
            raise ValueError(f"V-02: tema incorreto para {item['id']}: esperado '{TEMAS_ESPERADOS[item['id']]}'.")
        contagem_temas[item["tema"]] = contagem_temas.get(item["tema"], 0) + 1
    if any(qtd != 5 for qtd in contagem_temas.values()) or len(contagem_temas) != 3:
        raise ValueError("V-02: cada tema deve ter exatamente 5 intenções.")

    vistas: set = set()
    for item in intencoes:
        id_ = item["id"]
        frases = item["frases_treino"]

        # V-03: exatamente 12 frases
        if not isinstance(frases, list) or len(frases) != FRASES_POR_INTENCAO:
            raise ValueError(f"V-03: {id_} deve ter exatamente {FRASES_POR_INTENCAO} frases de treino.")
        # V-06: pergunta canônica é a primeira frase
        if item["pergunta_canonica"] != frases[0]:
            raise ValueError(f"V-06: a pergunta canônica de {id_} deve ser igual à primeira frase de treino.")
        for frase in frases:
            if not isinstance(frase, str):
                raise ValueError(f"V-03: frase de treino inválida em {id_}.")
            # V-04: entre 3 e 20 palavras
            if not 3 <= len(frase.split()) <= 20:
                raise ValueError(f"V-04: a frase de {id_} deve ter entre 3 e 20 palavras: '{frase}'")
            normalizada = normalizar_para_comparacao(frase)
            # V-05: únicas dentro da intenção e entre intenções
            if normalizada in vistas:
                raise ValueError(f"V-05: frase duplicada após normalização em {id_}: '{frase}'")
            vistas.add(normalizada)
            # V-07: nenhuma frase igual a uma pergunta de teste
            if normalizada in testes_normalizados:
                raise ValueError(f"V-07: frase de treino coincide com pergunta de teste em {id_}: '{frase}'")

        # V-08 / A-01 a A-06: regras da resposta
        resposta = item["resposta"]
        if not isinstance(resposta, str) or not resposta.strip():
            raise ValueError(f"V-08: resposta vazia em {id_}.")
        if not 1 <= contar_frases(resposta) <= RESPOSTA_MAX_FRASES:
            raise ValueError(f"A-01: a resposta de {id_} deve ter de 1 a {RESPOSTA_MAX_FRASES} frases.")
        if len(resposta) > RESPOSTA_MAX_CARACTERES:
            raise ValueError(f"A-01: a resposta de {id_} excede {RESPOSTA_MAX_CARACTERES} caracteres.")
        proibida = _palavra_proibida_em(resposta)
        if proibida:
            raise ValueError(f"A-02: a resposta de {id_} contém a palavra proibida '{proibida}'.")
        if item["tema"] == "tarifas":
            if "R$" in resposta or re.search(r"\d+[.,]\d{2}", resposta):
                raise ValueError(f"A-03: a resposta de tarifas {id_} não pode conter valor monetário.")
            if TEXTO_AVISO_TARIFAS in resposta:
                raise ValueError(f"A-06: a resposta de {id_} não pode conter o aviso de tarifas dentro do texto.")
        if id_ == "H05":
            minuscula = resposta.lower()
            if "não guarda" not in minuscula and "não são guardadas" not in minuscula:
                raise ValueError("A-05: a resposta H05 deve afirmar que as perguntas não são guardadas.")

        # V-09: status e regras de texto por status
        status = item["status_funcionalidade"]
        if status not in STATUS_PERMITIDOS:
            raise ValueError(f"V-09: status inválido em {id_}: '{status}'.")
        if status == "planejada" and not resposta.startswith(PREFIXO_PLANEJADA):
            raise ValueError(f"V-09: a resposta planejada de {id_} deve começar com '{PREFIXO_PLANEJADA}'.")
        if status == "parcial" and EXPRESSAO_PARCIAL not in resposta.lower():
            raise ValueError(f"V-09: a resposta parcial de {id_} deve conter '{EXPRESSAO_PARCIAL}'.")
        fontes = item["fontes_no_repositorio"]
        if not isinstance(fontes, list) or not fontes or not all(isinstance(f, str) for f in fontes):
            raise ValueError(f"V-09: {id_} deve ter ao menos 1 fonte no repositório.")
        for fonte in fontes:
            if not (raiz / fonte).exists():
                raise ValueError(f"V-09: fonte referenciada em {id_} não existe no repositório: '{fonte}'")

        # V-10: revisada_pela_equipe
        if not isinstance(item["revisada_pela_equipe"], bool):
            raise ValueError(f"V-10: 'revisada_pela_equipe' de {id_} deve ser verdadeiro ou falso.")


def _ler_json(caminho: Path, descricao: str):
    if not caminho.is_file():
        raise ValueError(f"Arquivo {descricao} não encontrado: {caminho}")
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - qualquer erro de leitura/JSON vira ValueError claro
        raise ValueError(f"Erro ao ler {descricao}: {exc}") from exc


def carregar_base(caminho_base=None, caminho_testes=None, validar: bool = True, raiz_repositorio=None):
    """Etapa de coleta: lê os dois JSON e (por padrão) valida. Devolve (dados_base, dados_testes)."""
    p_base = resolver_caminho(caminho_base or CAMINHO_BASE)
    p_testes = resolver_caminho(caminho_testes or CAMINHO_PERGUNTAS_TESTE)
    dados_base = _ler_json(p_base, "da base de conhecimento")
    dados_testes = _ler_json(p_testes, "de perguntas de teste")
    if validar:
        validar_base(dados_base, dados_testes, raiz_repositorio)
    return dados_base, dados_testes


def obter_pares_treino(dados_base: dict):
    """Devolve (frases, rotulos): cada frase de treino com o ID da sua intenção."""
    frases, rotulos = [], []
    for item in dados_base["intencoes"]:
        for frase in item["frases_treino"]:
            frases.append(frase)
            rotulos.append(item["id"])
    return frases, rotulos


def obter_intencoes_por_id(dados_base: dict) -> dict:
    return {item["id"]: item for item in dados_base["intencoes"]}
