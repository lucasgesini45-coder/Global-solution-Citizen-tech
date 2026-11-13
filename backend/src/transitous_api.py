"""Integração acadêmica com Transitous (MOTIS v6) para traçados verificáveis.

A API pública é best-effort, destinada a projetos não comerciais open-source.
Não estimamos tarifas, segurança ou geometria quando o provedor não informar.
Fonte: https://transitous.org/api/ e https://transitous.org/sources/
"""
from __future__ import annotations

import math
import os
from urllib.parse import urlencode

from fastapi import HTTPException

from .enderecos_api import _json_http

TRANSITOUS_URL = "https://api.transitous.org/api/v6/plan"
MODOS_FERROVIARIOS = {"SUBWAY", "SUBURBAN", "REGIONAL_RAIL", "RAIL", "TRAM", "METRO"}
MODOS_ONIBUS = {"BUS"}
MODOS_A_PE = {"WALK"}


def decodificar_polilinha(geometry: dict) -> list[list[float]]:
    """Decodifica coordenadas MOTIS (Google Encoded Polyline, precisão declarada)."""
    points = geometry.get("points", "") if isinstance(geometry, dict) else ""
    precision = geometry.get("precision", 6) if isinstance(geometry, dict) else 6
    if not isinstance(points, str) or not points or not isinstance(precision, int) or precision < 0 or precision > 7:
        return []
    coords, index, lat, lon = [], 0, 0, 0
    try:
        while index < len(points) and len(coords) < 12000:
            deltas = []
            for _ in range(2):
                shift, value = 0, 0
                while True:
                    if index >= len(points):
                        return []
                    byte = ord(points[index]) - 63
                    index += 1
                    if byte < 0 or byte > 63 or shift > 35:
                        return []
                    value |= (byte & 31) << shift
                    shift += 5
                    if byte < 32:
                        break
                deltas.append(~(value >> 1) if value & 1 else value >> 1)
            lat += deltas[0]
            lon += deltas[1]
            a, b = lat / (10 ** precision), lon / (10 ** precision)
            if not (-90 <= a <= 90 and -180 <= b <= 180):
                return []
            coords.append([a, b])
    except (OverflowError, ValueError):
        return []
    return coords


def _trechos_viagem(viagem: dict) -> list[dict]:
    trechos = []
    for item in viagem.get("legs", []):
        modo = str(item.get("mode", "")).upper()
        trajeto = decodificar_polilinha(item.get("legGeometry") or {})
        if len(trajeto) < 2:
            # Só desenhamos geometria confirmada pelo provedor, nunca reta inventada.
            continue
        a, b = item.get("from") or {}, item.get("to") or {}
        paradas = []
        if modo in MODOS_FERROVIARIOS or modo in MODOS_ONIBUS:
            for place in [a, *(item.get("intermediateStops") or []), b]:
                if not isinstance(place, dict):
                    continue
                lat, lon = place.get("lat"), place.get("lon")
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and math.isfinite(lat) and math.isfinite(lon):
                    paradas.append({"nome": str(place.get("name") or "Estação / parada"), "lat": lat, "lon": lon})
        cor_bruta = str(item.get("routeColor") or "").lstrip("#")
        cor_linha = "#" + cor_bruta if len(cor_bruta) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in cor_bruta) else None
        trechos.append({
            "cor_linha": cor_linha,
            "paradas": paradas,
            "modal": modo, "linha": item.get("displayName") or item.get("routeShortName") or None,
            "destino_linha": item.get("headsign") or None,
            "de": a.get("name") or "Origem", "para": b.get("name") or "Destino",
            "tempo_min": round(float(item.get("duration", 0)) / 60),
            "trajeto": trajeto,
        })
    return trechos


def consultar_transitous(origem, destino, modal: str) -> dict:
    if modal not in {"ape", "onibus", "ferroviario", "todos"}:
        raise HTTPException(status_code=422, detail="Modal inválido.")
    modos = {
        "ape": "",
        "onibus": "BUS",
        "ferroviario": "SUBWAY,SUBURBAN,REGIONAL_RAIL,RAIL",
        "todos": "BUS,SUBWAY,SUBURBAN,REGIONAL_RAIL",
    }
    params = {
        "fromPlace": f"{origem.lat:.7f},{origem.lon:.7f}",
        "toPlace": f"{destino.lat:.7f},{destino.lon:.7f}",
        "transitModes": modos[modal],
        "detailedLegs": "true",
        "detailedTransfers": "true",
        "maxTransfers": 3,
        "searchWindow": 3600,
    }
    # Para caminhada, solicitar rota direta; para transporte público desabilitar
    # rotas diretas que poderiam descartar opções de ônibus/ferrovia.
    if modal == "ape":
        params["directModes"] = "WALK"
    else:
        # Sem directModes vazio (pode invalidar array MOTIS); remove a viagem
        # direta para evitar o corte das conexões de transporte público.
        params["maxDirectTime"] = 0
    url = TRANSITOUS_URL + "?" + urlencode(params)
    try:
        resposta = _json_http(url, max_bytes=3_000_000, headers={
            "User-Agent": os.getenv(
                "CITIZEN_TRANSIT_USER_AGENT",
                "CitizenTechFIAP/0.3 (https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech)"
            )
        })
    except HTTPException as exc:
        raise HTTPException(status_code=503, detail=(
            "Não foi possível calcular a rota pelo Transitous: "
            + str(exc.detail) + " Nenhuma linha fictícia foi desenhada."
        )) from exc
    viagens = resposta.get("direct", []) if modal == "ape" else resposta.get("itineraries", [])
    if not isinstance(viagens, list):
        viagens = []
    # Filtra para garantir que o modo escolhido de fato seja utilizado.
    permitidos = MODOS_ONIBUS if modal == "onibus" else MODOS_FERROVIARIOS
    if modal in {"onibus", "ferroviario"}:
        viagens = [v for v in viagens if any(
            str(leg.get("mode", "")).upper() in permitidos for leg in v.get("legs", [])
        )]
    opcoes = []
    for v in viagens[:8]:
        trechos = _trechos_viagem(v)
        if not trechos:
            continue
        if modal in {"onibus", "ferroviario"} and not any(
            t["modal"] in permitidos for t in trechos
        ):
            continue
        if modal == "ape" and not any(t["modal"] in MODOS_A_PE for t in trechos):
            continue
        opcoes.append((v, trechos))
    if not opcoes:
        raise HTTPException(status_code=404, detail=(
            "Não foram encontradas viagens com geometria disponível para esse modal, "
            "local e horário no Transitous. Tente outro horário ou local."
        ))
    v, trechos = min(opcoes, key=lambda item: float(item[0].get("duration", 1e9)))
    trajeto = [pt for t in trechos for pt in t["trajeto"]]
    # A distância só é exibida quando a API informa seus valores.
    distancias = [float(leg["distance"]) for leg in v.get("legs", []) if isinstance(leg.get("distance"), (int,float))]
    distancia = round(sum(distancias)) if len(distancias) == len(v.get("legs", [])) else None
    return {
        "tipo": "rota_real", "fonte": "Transitous / MOTIS (dados GTFS e OpenStreetMap)",
        "modal": modal, "tempo_min": round(float(v.get("duration", 0)) / 60),
        "distancia_m": distancia, "tarifa_centavos": None,
        "seguranca": {"status": "nao_verificada", "exposicao": None},
        "trajeto": trajeto, "trechos": trechos,
        "aviso": ("Rota informada pelo Transitous. Horários podem mudar e não há "
                  "validação de tarifa, acessibilidade ou segurança. "
                  "Dados de transporte: https://transitous.org/sources/"),
    }
