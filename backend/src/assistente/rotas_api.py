"""Endpoints FastAPI do assistente (seção 12.1), com prefixo /assistente.

Para ligar à API existente, acrescente em src/api.py (ver INTEGRACAO.md):
    from backend.src.assistente.rotas_api import roteador as roteador_assistente
    app.include_router(roteador_assistente)

O modelo é carregado uma única vez e mantido em memória. Se não puder ser carregado nem treinado,
a API continua de pé: POST /assistente/perguntar responde 503 e GET /assistente/saude informa
modelo_carregado = falso. Nenhuma pergunta é guardada ou registrada em log.
"""
import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from .config import (
    N_INTENCOES,
    PERGUNTA_MAX_CARACTERES,
    PERGUNTA_MIN_CARACTERES,
    TEXTO_ASSISTENTE_INDISPONIVEL,
)
from .modelo import carregar_ou_treinar
from .previsao import prever

roteador = APIRouter(prefix="/assistente", tags=["assistente"])

_trava = threading.Lock()
_estado = {"tentou": False, "modelo": None}


def preparar_modelo(forcar: bool = False):
    """Carrega o modelo uma vez (thread-safe). Pode ser chamada na inicialização da API."""
    with _trava:
        if forcar or not _estado["tentou"]:
            _estado["tentou"] = True
            try:
                _estado["modelo"] = carregar_ou_treinar()
            except Exception:  # noqa: BLE001 - a API não pode cair por causa do assistente
                _estado["modelo"] = None
        return _estado["modelo"]


class PerguntaEntrada(BaseModel):
    pergunta: str

    @field_validator("pergunta")
    @classmethod
    def _tamanho(cls, valor: str) -> str:
        limpa = valor.strip()
        if not PERGUNTA_MIN_CARACTERES <= len(limpa) <= PERGUNTA_MAX_CARACTERES:
            raise ValueError(
                f"A pergunta deve ter de {PERGUNTA_MIN_CARACTERES} a {PERGUNTA_MAX_CARACTERES} caracteres.")
        return limpa


class RespostaAssistente(BaseModel):
    resposta: str
    intencao_id: str | None
    tema: str | None
    confianca: float
    sugestoes: list[str]
    aviso: str | None


class SaudeAssistente(BaseModel):
    modelo_carregado: bool
    n_intencoes: int
    versao_base: str | None


@roteador.post("/perguntar", response_model=RespostaAssistente)
def perguntar(entrada: PerguntaEntrada):
    modelo = preparar_modelo()
    if modelo is None:
        raise HTTPException(status_code=503, detail=TEXTO_ASSISTENTE_INDISPONIVEL)
    return prever(entrada.pergunta, modelo).para_dict()


@roteador.get("/saude", response_model=SaudeAssistente)
def saude():
    modelo = preparar_modelo()
    return {
        "modelo_carregado": modelo is not None,
        "n_intencoes": N_INTENCOES,
        "versao_base": modelo.versao_base if modelo is not None else None,
    }
