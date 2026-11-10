from __future__ import annotations

import datetime
import json
import os
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

from src.config import (
    GEOCODIFICACAO_INTERVALO_MIN_S,
    GEOCODIFICACAO_MAX_RESULTADOS,
    GEOCODIFICACAO_TIMEOUT_S,
    TTL_CACHE_GEOCODIFICACAO_DIAS,
)

_lock = threading.Lock()
_ultimo_acesso = 0.0
_time_monotonic = time.monotonic
_time_sleep = time.sleep


def _esperar_intervalo() -> None:
    global _ultimo_acesso
    with _lock:
        agora_m = _time_monotonic()
        passado = agora_m - _ultimo_acesso
        if passado < GEOCODIFICACAO_INTERVALO_MIN_S:
            espera = GEOCODIFICACAO_INTERVALO_MIN_S - passado
            _time_sleep(espera)
        _ultimo_acesso = _time_monotonic()


def buscar_endereco(
    texto: str,
    banco: str,
    limites: tuple[float, float, float, float],
    cliente_http: Callable[..., Any] | None = None,
    agora: datetime.datetime | None = None,
) -> dict[str, Any]:
    if agora is None:
        agora = datetime.datetime.now()

    if not isinstance(texto, str):
        return {
            "erro": {
                "codigo": "consulta_invalida",
                "mensagem": "A consulta deve ser um texto.",
            }
        }

    consulta = " ".join(texto.strip().lower().split())
    if not (3 <= len(consulta) <= 200):
        return {
            "erro": {
                "codigo": "consulta_invalida",
                "mensagem": "A consulta deve ter entre 3 e 200 caracteres.",
            }
        }

    # Verificar cache em SQLite
    dados = None
    with sqlite3.connect(banco) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT resposta_json, obtido_em FROM cache_geocodificacao WHERE consulta = ?",
            (consulta,),
        )
        row = cursor.fetchone()
        if row:
            resposta_json, obtido_em_str = row
            try:
                obtido_em = datetime.datetime.fromisoformat(obtido_em_str)
                limite_cache = agora - datetime.timedelta(
                    days=TTL_CACHE_GEOCODIFICACAO_DIAS
                )
                if obtido_em >= limite_cache:
                    dados = json.loads(resposta_json)
            except Exception:
                dados = None

    if dados is None:
        user_agent = os.environ.get("ROTAVIVA_USER_AGENT")
        if not user_agent or not user_agent.strip():
            return {
                "erro": {
                    "codigo": "user_agent_ausente",
                    "mensagem": "Variável de ambiente ROTAVIVA_USER_AGENT não definida ou vazia.",
                }
            }

        _esperar_intervalo()

        params = urllib.parse.urlencode(
            {
                "q": consulta,
                "format": "jsonv2",
                "limit": GEOCODIFICACAO_MAX_RESULTADOS,
                "countrycodes": "br",
            }
        )
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        headers = {"User-Agent": user_agent}

        try:
            if cliente_http is not None:
                try:
                    res_raw = cliente_http(
                        url, headers=headers, timeout=GEOCODIFICACAO_TIMEOUT_S
                    )
                except TypeError:
                    try:
                        res_raw = cliente_http(
                            url, headers, GEOCODIFICACAO_TIMEOUT_S
                        )
                    except TypeError:
                        res_raw = cliente_http(url)

                if isinstance(res_raw, tuple):
                    status, body = res_raw
                elif hasattr(res_raw, "status") and hasattr(res_raw, "read"):
                    status = res_raw.status
                    body = res_raw.read().decode("utf-8")
                elif isinstance(res_raw, (list, dict)):
                    status = 200
                    body = json.dumps(res_raw)
                elif isinstance(res_raw, str):
                    status = 200
                    body = res_raw
                else:
                    status = 200
                    body = str(res_raw)

                if status != 200:
                    return {
                        "erro": {
                            "codigo": "geocodificacao_indisponivel",
                            "mensagem": "Serviço de geocodificação indisponível.",
                        }
                    }
                dados = json.loads(body)
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(
                    req, timeout=GEOCODIFICACAO_TIMEOUT_S
                ) as resp:
                    if resp.status != 200:
                        return {
                            "erro": {
                                "codigo": "geocodificacao_indisponivel",
                                "mensagem": "Serviço de geocodificação indisponível.",
                            }
                        }
                    dados = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {
                "erro": {
                    "codigo": "geocodificacao_indisponivel",
                    "mensagem": "Serviço de geocodificação indisponível.",
                }
            }

        # Salvar no cache apenas em caso de sucesso
        with sqlite3.connect(banco) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cache_geocodificacao (consulta, resposta_json, obtido_em)
                VALUES (?, ?, ?)
                ON CONFLICT(consulta) DO UPDATE SET
                    resposta_json = excluded.resposta_json,
                    obtido_em = excluded.obtido_em
                """,
                (consulta, json.dumps(dados), agora.isoformat()),
            )
            conn.commit()

    # Filtrar resultados locais por limites
    lat_min, lon_min, lat_max, lon_max = limites
    candidatos = []
    if isinstance(dados, list):
        for item in dados:
            try:
                lat = float(item["lat"])
                lon = float(item["lon"])
                nome = str(item.get("display_name", ""))
            except (KeyError, ValueError, TypeError):
                continue
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                candidatos.append({"nome": nome, "lat": lat, "lon": lon})

    if not candidatos:
        return {
            "erro": {
                "codigo": "sem_resultado_na_area_piloto",
                "mensagem": "Nenhum resultado encontrado dentro da área piloto.",
            }
        }

    return {
        "candidatos": candidatos,
        "atribuicao": "Dados de endereço © colaboradores do OpenStreetMap",
    }
