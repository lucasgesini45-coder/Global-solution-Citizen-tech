"""Busca de endereços e rotas reais de caminhada, com limites explícitos.

Photon é um servidor de demonstração com limite de uso; produção exige
instância própria/provedor contratado. A rota a pé necessita ORS_API_KEY.
"""
from __future__ import annotations

import json
import math
import os
import time
from functools import lru_cache
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(tags=["Endereços e rotas reais"])
PHOTON_URL = os.getenv("PHOTON_API_URL", "https://photon.komoot.io/api").strip()
ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"
AGENTE = "CitizenMobilidadeFIAP/0.2 (prototipo-academico)"
_lock = Lock()
_ultima_busca = 0.0


def _json_http(url: str, *, payload: dict | None = None, headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    h = {"User-Agent": AGENTE, "Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = Request(url, data=body, headers=h, method="POST" if body is not None else "GET")
    tentativas = 2 if payload is None else 1
    for indice in range(tentativas):
        try:
            with urlopen(req, timeout=12) as response:
                return json.loads(response.read(400_000).decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                if indice + 1 < tentativas:
                    time.sleep(2)
                    continue
                raise HTTPException(status_code=503, detail="O serviço de busca de endereços atingiu seu limite temporário de consultas (Photon). Tente novamente em alguns instantes.") from exc
            if exc.code in (502, 503, 504) and indice + 1 < tentativas:
                time.sleep(1)
                continue
            raise HTTPException(status_code=503, detail=f"O serviço de endereços Photon respondeu HTTP {exc.code}. Verifique a conexão com photon.komoot.io.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            if indice + 1 < tentativas:
                time.sleep(1)
                continue
            raise HTTPException(status_code=503, detail="Não foi possível conectar ao Photon. Verifique a internet do computador onde roda o backend e o acesso a photon.komoot.io.") from exc
        except (ValueError, UnicodeError) as exc:
            raise HTTPException(status_code=503, detail="O serviço de endereços respondeu com dados inválidos.") from exc
    raise HTTPException(status_code=503, detail="Busca de endereços indisponível.")


@lru_cache(maxsize=128)
def _buscar_cache(consulta: str) -> list[dict]:
    global _ultima_busca
    # Somente consultas nao encontradas no cache precisam aguardar o provedor.
    with _lock:
        espera = 1.1 - (time.monotonic() - _ultima_busca)
        if espera > 0:
            time.sleep(espera)
        _ultima_busca = time.monotonic()
    # Não enviar lang=pt: algumas instâncias Photon rejeitam idioma não indexado com HTTP 400.
    # O idioma é opcional; nomes locais são preservados sem o parâmetro.
    params = urlencode({"q": consulta, "limit": 10, "lat": -23.55, "lon": -46.63})
    dados = _json_http(PHOTON_URL + "?" + params)
    resultados = []
    vistos = set()
    for item in dados.get("features", []):
        props = item.get("properties", {})
        coords = item.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue
        lon, lat = coords[:2]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (lat, lon)):
            continue
        # Priorizar a região metropolitana de São Paulo e evitar propostas em outros países.
        if not (-24.2 <= lat <= -23.0 and -47.4 <= lon <= -45.8):
            continue
        rua = props.get("street")
        nome_local = props.get("name")
        numero = props.get("housenumber")
        partes = []
        if nome_local:
            partes.append(str(nome_local))
        if rua and str(rua).casefold() != str(nome_local or "").casefold():
            partes.append(str(rua))
        if numero:
            partes.append(str(numero))
        for campo in ("district", "city", "state"):
            valor = props.get(campo)
            if valor and str(valor).casefold() not in {parte.casefold() for parte in partes}:
                partes.append(str(valor))
        nome = ", ".join(partes)
        chave = (round(lat, 6), round(lon, 6), nome.casefold())
        if nome and chave not in vistos:
            vistos.add(chave)
            resultados.append({"nome": nome, "lat": lat, "lon": lon,
                               "fonte": "OpenStreetMap/Photon"})
    return resultados


@router.get("/enderecos/sugestoes")
def sugestoes(q: str = Query(min_length=4, max_length=120)):
    global _ultima_busca
    consulta = " ".join(q.strip().split())
    if len(consulta) < 4:
        return {"resultados": [], "fonte": "OpenStreetMap/Photon"}
    return {"resultados": _buscar_cache(consulta), "fonte": "OpenStreetMap/Photon"}


class Coordenadas(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class RotaRealPedido(BaseModel):
    origem: Coordenadas
    destino: Coordenadas
    modal: str = "ape"


@router.post("/rotas/reais")
def rota_real(pedido: RotaRealPedido):
    if pedido.modal != "ape":
        raise HTTPException(
            status_code=422,
            detail="Rotas reais de ônibus, metrô e trem exigem integração com dados operacionais/GTFS; ainda não disponíveis."
        )
    key = os.getenv("ORS_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Rota real a pé não configurada: defina ORS_API_KEY no backend.")
    a, b = pedido.origem, pedido.destino
    dados = _json_http(ORS_URL,
                       payload={"coordinates": [[a.lon, a.lat], [b.lon, b.lat]]},
                       headers={"Authorization": key})
    features = dados.get("features", [])
    if not features:
        raise HTTPException(status_code=404, detail="Não foi encontrada rota a pé.")
    feature = features[0]
    geometry = feature.get("geometry", {}).get("coordinates", [])
    summary = feature.get("properties", {}).get("summary", {})
    return {
        "tipo": "rota_real", "fonte": "openrouteservice / OpenStreetMap",
        "modal": "ape", "tempo_min": round(summary.get("duration", 0)/60),
        "distancia_m": round(summary.get("distance", 0)),
        "tarifa_centavos": 0,
        "seguranca": {"status": "nao_verificada", "exposicao": None},
        "trajeto": [[float(lat), float(lon)] for lon, lat in geometry],
        "aviso": "Tempo estimado para caminhada; não representa condições de segurança.",
    }
