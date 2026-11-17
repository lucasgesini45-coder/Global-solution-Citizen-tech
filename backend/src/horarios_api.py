"""Partidas de ônibus por parada, linha, operador e sentido do itinerário."""
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .enderecos_api import _json_http
from .transitous_api import horario_iso

router = APIRouter(prefix="/horarios", tags=["Horários de ônibus"])
URL = "https://api.transitous.org/api/v6/stoptimes"


class ConsultaPartidas(BaseModel):
    ponto_id: str = Field(min_length=1, max_length=250)
    codigo_linha: str = Field(min_length=1, max_length=100)
    operadora_id: str = Field(min_length=1, max_length=250)
    sentido: str = Field(min_length=1, max_length=250)
    desembarque_id: str = Field(min_length=1, max_length=250)


def normalizar(v):
    return " ".join(str(v or "").casefold().split())


@router.post("/onibus")
def proximas_partidas(pedido: ConsultaPartidas):
    agora = datetime.now(timezone.utc)
    params = {"stopId": pedido.ponto_id, "time": agora.isoformat(),
              "n": 50, "mode": "BUS", "arriveBy": "false", "fetchStops": "true"}
    dados = _json_http(URL + "?" + urlencode(params), max_bytes=3_000_000,
                       headers={"User-Agent": "CitizenTechFIAP/0.3 (https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech)"})
    if not isinstance(dados, dict) or not isinstance(dados.get("stopTimes"), list):
        raise HTTPException(503, "Horários indisponíveis no provedor.")
    partidas = []
    vistos = set()
    for evento in dados["stopTimes"]:
        if not isinstance(evento, dict) or evento.get("mode") != "BUS":
            continue
        if evento.get("cancelled") or evento.get("tripCancelled"):
            continue
        if evento.get("pickupDropoffType") in {"NONE", "NOT_AVAILABLE", "NO_PICKUP", "NOT_ALLOWED"}:
            continue
        ponto = evento.get("place") or {}
        if (ponto.get("stopId") != pedido.ponto_id
                or evento.get("agencyId") != pedido.operadora_id
                or normalizar(evento.get("routeShortName")) != normalizar(pedido.codigo_linha)
                or normalizar(evento.get("headsign")) != normalizar(pedido.sentido)):
            continue
        # Verificar se o ônibus passa no ponto de desembarque, não só na mesma linha.
        seguintes = evento.get("nextStops") or []
        if not any(isinstance(s, dict) and s.get("stopId") == pedido.desembarque_id
                   and not s.get("cancelled") and s.get("dropoffType") != "NOT_ALLOWED" for s in seguintes):
            continue
        programada = horario_iso(ponto.get("scheduledDeparture"))
        estimada = horario_iso(ponto.get("departure"))
        tempo_real = evento.get("realTime") is True and estimada is not None
        partida = estimada if tempo_real else programada or estimada
        if not partida or datetime.fromisoformat(partida) < agora:
            continue
        chave = (evento.get("tripId"), partida)
        if chave in vistos:
            continue
        vistos.add(chave)
        partidas.append({"partida": partida, "programada": programada,
                         "tempo_real": tempo_real, "viagem_id": evento.get("tripId")})
    partidas.sort(key=lambda p: p["partida"])
    return {"partidas": partidas[:8], "consultado_em": agora.isoformat(),
            "fonte": "Transitous / MOTIS (GTFS e dados em tempo real quando disponíveis)",
            "aviso": "Consulta limitada às partidas retornadas pelo provedor nesta janela, com desembarque confirmado. A ausência de horários não significa ausência de serviço."}
