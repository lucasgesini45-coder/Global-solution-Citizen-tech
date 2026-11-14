"""Etapa de previsão (6.4 e seção 8.4): probabilidades, limiar, resposta ou fallback.

IMPORTANTE (privacidade, decisão D-15): este módulo NÃO guarda, NÃO imprime e NÃO registra
em log o texto das perguntas. Nenhuma pergunta de usuário é armazenada em lugar nenhum.
"""
from dataclasses import dataclass, field

from .config import (
    LIMIAR_CONFIANCA,
    MAX_SUGESTOES,
    PERGUNTA_MAX_CARACTERES,
    PERGUNTA_MIN_CARACTERES,
    TEXTO_AVISO_TARIFAS,
    TEXTO_FALLBACK,
    TEXTO_PERGUNTA_INVALIDA,
)


@dataclass
class Previsao:
    resposta: str
    intencao_id: str | None
    tema: str | None
    confianca: float
    sugestoes: list = field(default_factory=list)
    aviso: str | None = None

    def para_dict(self) -> dict:
        return {
            "resposta": self.resposta,
            "intencao_id": self.intencao_id,
            "tema": self.tema,
            "confianca": self.confianca,
            "sugestoes": list(self.sugestoes),
            "aviso": self.aviso,
        }


def validar_pergunta(pergunta) -> str:
    """Remove espaços das pontas e confere o tamanho. A mensagem de erro nunca traz a pergunta."""
    if not isinstance(pergunta, str):
        raise ValueError(TEXTO_PERGUNTA_INVALIDA)
    limpa = pergunta.strip()
    if not PERGUNTA_MIN_CARACTERES <= len(limpa) <= PERGUNTA_MAX_CARACTERES:
        raise ValueError(TEXTO_PERGUNTA_INVALIDA)
    return limpa


def ordenar_intencoes(modelo, pergunta_limpa: str) -> list:
    """[(id, probabilidade)] da maior para a menor; em empate, ID em ordem alfabética."""
    probabilidades = modelo.pipeline.predict_proba([pergunta_limpa])[0]
    pares = [(str(id_), float(p)) for id_, p in zip(modelo.pipeline.classes_, probabilidades)]
    pares.sort(key=lambda par: (-par[1], par[0]))
    return pares


def prever(pergunta, modelo, limiar: float | None = None) -> Previsao:
    """Passos 1 a 5 da seção 8.4."""
    limpa = validar_pergunta(pergunta)                       # passo 1
    ordenadas = ordenar_intencoes(modelo, limpa)             # passo 2 (e 5: desempate)
    melhor_id, melhor_prob = ordenadas[0]
    corte = LIMIAR_CONFIANCA if limiar is None else limiar
    confianca = round(melhor_prob, 4)

    if melhor_prob >= corte:                                 # passo 3
        intencao = modelo.intencoes[melhor_id]
        aviso = TEXTO_AVISO_TARIFAS if intencao["tema"] == "tarifas" else None
        return Previsao(intencao["resposta"], melhor_id, intencao["tema"], confianca, [], aviso)

    sugestoes = [modelo.intencoes[id_]["pergunta_canonica"] for id_, _ in ordenadas[:MAX_SUGESTOES]]
    return Previsao(TEXTO_FALLBACK, None, None, confianca, sugestoes, None)   # passo 4
