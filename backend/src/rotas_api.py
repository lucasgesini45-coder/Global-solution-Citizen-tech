"""Adaptador HTTP para o motor de rotas demonstrativo (integrante 2).

Os trajetos, horários e tarifas deste endpoint são SIMULADOS.
"""
import math
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Rotas e tarifas"])

# O módulo legado importa "src.*". Preserve sua estrutura sem copiar algoritmos.
RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
PASTA_MODULO = RAIZ_REPOSITORIO / "global solution part2 - tarifas"
if not (PASTA_MODULO / "src" / "recomendar.py").is_file():
    raise RuntimeError("Modulo de rotas ausente: global solution part2 - tarifas/src/recomendar.py")
if str(PASTA_MODULO) not in sys.path:
    sys.path.insert(0, str(PASTA_MODULO))

from src.recomendar import processar_pedido
from src.rede_demo import criar_rede_demo, ponto
from src.tarifas import carregar_regras


class Coordenadas(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class PedidoRota(BaseModel):
    origem: Coordenadas
    destino: Coordenadas
    partida: str = Field(min_length=1, max_length=50)
    necessidades: dict[str, Any] = Field(default_factory=dict)


@lru_cache(maxsize=1)
def dados_demo():
    rede = criar_rede_demo()
    regras = carregar_regras(str(PASTA_MODULO / "data" / "tarifas_demo.json"))
    return rede, regras


@router.post("/rotas")
def calcular_rotas(pedido: PedidoRota):
    try:
        dados = pedido.model_dump()
        # Pydantic aceita NaN/Infinity em algumas configurações; a API não.
        for local in ("origem", "destino"):
            if not all(math.isfinite(v) for v in dados[local].values()):
                raise ValueError("Coordenadas devem ser numeros finitos.")
        rede, regras = dados_demo()
        resultado = processar_pedido(dados, rede, regras)
        return {
            "modo": "demonstracao",
            "origem_dados": "rede, horarios e tarifas ficticios",
            "aviso": "Nao utilizar como informacao real de transporte publico.",
            "resultado": resultado,
        }
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/rotas/exemplo")
def exemplo_rotas():
    """Cenário fixo da rede fictícia para demonstrar o módulo 2.

    Não representa um percurso real de São Paulo nem tarifas oficiais.
    """
    origem = ponto(0.0, -100.0)
    destino = ponto(4000.0, 300.0)
    pedido = PedidoRota(
        origem={"lat": origem[0], "lon": origem[1]},
        destino={"lat": destino[0], "lon": destino[1]},
        partida="2026-11-09T08:00:00",
    )
    resposta = calcular_rotas(pedido)
    return {
        **resposta,
        "cenario": "Exemplo acadêmico com paradas, linhas, horários e tarifas simulados",
        "partida_exemplo": pedido.partida,
    }
