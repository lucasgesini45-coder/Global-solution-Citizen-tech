"""Partidas de ônibus por parada, linha, operador e sentido do itinerário."""
from datetime import datetime, timezone, date, time, timedelta
from zoneinfo import ZoneInfo
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
    dia: date | None = None


def normalizar(v):
    return " ".join(str(v or "").casefold().split())


@router.post("/onibus")
def proximas_partidas(pedido: ConsultaPartidas):
    agora = datetime.now(timezone.utc)
    fuso = ZoneInfo("America/Sao_Paulo")
    dia = pedido.dia or agora.astimezone(fuso).date()
    hoje = agora.astimezone(fuso).date()
    if not hoje <= dia <= hoje + timedelta(days=1):
        raise HTTPException(422, "Selecione hoje ou amanhã.")
    inicio = datetime.combine(dia, time.min, fuso).astimezone(timezone.utc)
    fim = datetime.combine(dia + timedelta(days=1), time.min, fuso).astimezone(timezone.utc)
    params = {"stopId": pedido.ponto_id, "time": inicio.isoformat(),
              "window": int((fim-inicio).total_seconds()), "mode": "BUS",
              "arriveBy": "false", "fetchStops": "true", "withAlerts": "false"}

    dados = _json_http(URL + "?" + urlencode(params), max_bytes=24_000_000,
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
        if not partida or not inicio <= datetime.fromisoformat(partida) < fim:
            continue
        chave = (evento.get("tripId"), partida)
        if chave in vistos:
            continue
        vistos.add(chave)
        partidas.append({"partida": partida, "programada": programada,
                         "tempo_real": tempo_real, "viagem_id": evento.get("tripId")})
    partidas.sort(key=lambda p: p["partida"])
    proxima = next((p for p in partidas if datetime.fromisoformat(p["partida"]) >= agora), None)
    return {"partidas": partidas, "proxima": proxima, "dia": dia.isoformat(), "consultado_em": agora.isoformat(),
            "fonte": "Transitous / MOTIS (GTFS e dados em tempo real quando disponíveis)",
            "aviso": "Horários de passagem retornados pelo provedor para o dia selecionado, no ponto e sentido do trajeto. A cobertura pode ser incompleta. Horários passados são referências, não confirmação de passagem."}
