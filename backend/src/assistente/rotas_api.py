"""Endpoints FastAPI do assistente (seção 12.1), com prefixo /assistente.

Para ligar à API existente, acrescente em src/api.py (ver INTEGRACAO.md):
<<<<<<< HEAD
    from src.assistente.rotas_api import roteador as roteador_assistente
    app.include_router(roteador_assistente)

Também pode ser executado diretamente via Uvicorn:
    uvicorn backend.src.assistente.rotas_api:app --reload
    (ou a partir de backend/src: uvicorn assistente.rotas_api:app --reload)

=======
    from backend.src.assistente.rotas_api import roteador as roteador_assistente
    app.include_router(roteador_assistente)

>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e
O modelo é carregado uma única vez e mantido em memória. Se não puder ser carregado nem treinado,
a API continua de pé: POST /assistente/perguntar responde 503 e GET /assistente/saude informa
modelo_carregado = falso. Nenhuma pergunta é guardada ou registrada em log.
"""
<<<<<<< HEAD
import sys
import threading
from pathlib import Path

# Garante que a raiz do projeto, backend/ e backend/src/ estejam no sys.path
# independentemente de qual pasta o comando uvicorn ou python foi executado.
_ARQUIVO_ATUAL = Path(__file__).resolve()
_PASTA_SRC = _ARQUIVO_ATUAL.parents[1]
_PASTA_BACKEND = _ARQUIVO_ATUAL.parents[2]
_PASTA_RAIZ = _ARQUIVO_ATUAL.parents[3]
for _caminho in (_PASTA_SRC, _PASTA_BACKEND, _PASTA_RAIZ):
    if str(_caminho) not in sys.path:
        sys.path.insert(0, str(_caminho))

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
=======
import threading

from fastapi import APIRouter, HTTPException
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e
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
<<<<<<< HEAD


# Aplicação ASGI standalone para permitir execução direta com Uvicorn
app = FastAPI(
    title="Assistente de Dúvidas - Citizen Mobilidade",
    description="API do assistente de dúvidas sobre rotas, tarifas e histórico/privacidade.",
    version="1.0.0",
)
app.include_router(roteador)


@app.get("/", include_in_schema=False)
def raiz():
    """Redireciona a raiz para a documentação interativa (/docs)."""
    return RedirectResponse(url="/docs")
=======
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e
