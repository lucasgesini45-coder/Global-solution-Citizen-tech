"""Análise explicativa de trechos documentados; não comprova condições reais."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from .acessibilidade import analisar_acessibilidade

router = APIRouter(prefix="/acessibilidade", tags=["Acessibilidade"])


class TrechoAcessivel(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    descricao: str = Field(min_length=1, max_length=300)
    passagem_sem_degraus: bool | None = None


class AvaliacaoPedido(BaseModel):
    trechos: list[TrechoAcessivel] = Field(max_length=100)
    precisa_sem_degraus: bool = True


@router.post("/avaliar")
def avaliar(pedido: AvaliacaoPedido):
    """Só interpreta informações fornecidas. Sem fontes, nunca equivale a rota validada."""
    resultado = analisar_acessibilidade(
        [trecho.model_dump() for trecho in pedido.trechos],
        {"precisa_sem_degraus": pedido.precisa_sem_degraus},
    )
    return {
        **resultado,
        "tipo": "analise_de_dados_fornecidos",
        "verificacao_em_campo": False,
        "aviso": (
            "Avaliação dos dados informados; não confirma acessibilidade física "
            "de estações, ruas ou elevadores. Verifique fontes oficiais atualizadas."
        ),
    }
