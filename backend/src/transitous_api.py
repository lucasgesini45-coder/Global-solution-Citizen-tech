"""Integração acadêmica com Transitous (MOTIS v6) para traçados verificáveis.

A API pública é best-effort, destinada a projetos não comerciais open-source.
Não estimamos tarifas, segurança ou geometria quando o provedor não informar.
Fonte: https://transitous.org/api/ e https://transitous.org/sources/
"""
from __future__ import annotations

import math
import os
import re
import unicodedata
from urllib.parse import urlencode
from datetime import datetime, timezone

from fastapi import HTTPException

from .enderecos_api import _json_http

TRANSITOUS_URL = "https://api.transitous.org/api/v6/plan"
MODOS_FERROVIARIOS = {"SUBWAY", "SUBURBAN", "REGIONAL_RAIL", "RAIL", "TRAM", "METRO"}
MODOS_ONIBUS = {"BUS"}
MODOS_A_PE = {"WALK"}

# Referências cromáticas da rede metropolitana de São Paulo (não incluem
# obras futuras). A cor WALK é reservada a cinza tracejado no frontend.
CORES_LINHAS = {
    1: ("Azul", "#0455A1"), 2: ("Verde", "#008E5A"),
    3: ("Vermelha", "#ED1C24"), 4: ("Amarela", "#F9C80E"),
    5: ("Lilás", "#9B3894"), 7: ("Rubi", "#A6192E"),
    8: ("Diamante", "#8F9498"), 9: ("Esmeralda", "#008A72"),
    10: ("Turquesa", "#008F95"), 11: ("Coral", "#F36C38"),
    12: ("Safira", "#153E84"), 13: ("Jade", "#00A5A5"),
    15: ("Prata", "#8C98A3"), 17: ("Ouro", "#B89035"),
}
NOMES_LINHAS = {nome.casefold(): num for num, (nome, _) in CORES_LINHAS.items()}


def identificar_linha(item: dict) -> tuple[str | None, str | None]:
    """Identifica uma linha mesmo se o GTFS fornecer cor incorreta/ausente."""
    modo = str(item.get("mode", "")).upper()
    cor_bruta = str(item.get("routeColor") or "").lstrip("#")
    cor_provedor = ("#" + cor_bruta if len(cor_bruta) == 6
                    and all(x in "0123456789abcdefABCDEF" for x in cor_bruta) else None)
    if modo == "WALK":
        return None, None
    if modo == "BUS":
        # Dar preferência ao código que identifica a linha no ponto (ex.: 875A-10).
        codigo = str(item.get("routeShortName") or "").strip()
        nome = str(item.get("displayName") or item.get("routeLongName") or "").strip()
        return codigo or nome or None, cor_provedor
    if modo not in MODOS_FERROVIARIOS:
        return None, None
    dados = " ".join(str(item.get(k) or "") for k in (
        "routeShortName", "routeLongName", "displayName"))
    normal = unicodedata.normalize("NFKD", dados).encode("ascii", "ignore").decode().casefold()
    numero = None
    # Evitar capturar números de códigos de ônibus ou do nome de uma estação.
    for padrao in (r"(?:linha|line|metr[o]?\s*l|cptm\s*l|^l)[\s#-]*(\d{1,2})\b",
                   r"\bl\s*[- ]?\s*(\d{1,2})\b",
                   r"^\s*(\d{1,2})\s*[- ]"):
        busca = re.search(padrao, normal)
        if busca and int(busca.group(1)) in CORES_LINHAS:
            numero = int(busca.group(1))
            break
    if numero is None:
        for nome, num in NOMES_LINHAS.items():
            if re.search(r"\b" + re.escape(nome) + r"\b", normal):
                numero = num
                break
    if numero is not None:
        nome, cor = CORES_LINHAS[numero]
        return f"Linha {numero} – {nome}", cor
    return str(item.get("displayName") or item.get("routeShortName") or "") or None, cor_provedor



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


def horario_iso(valor):
    """Preserva somente horários absolutos com fuso, informados pelo provedor."""
    if not isinstance(valor, str):
        return None
    try:
        dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat() if dt.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None


def horarios_onibus(viagem: dict) -> list[dict]:
    """Inclui inclusive etapas de ônibus sem geometria, sem inferir horários."""
    saida = []
    for indice, item in enumerate(viagem.get("legs", []), 1):
        if str(item.get("mode", "")).upper() != "BUS":
            continue
        de, para = item.get("from") or {}, item.get("to") or {}
        linha, _ = identificar_linha(item)
        tempo_real = item.get("realTime") is True
        partida_programada = horario_iso(item.get("scheduledStartTime")) or horario_iso(de.get("scheduledDeparture"))
        chegada_programada = horario_iso(item.get("scheduledEndTime")) or horario_iso(para.get("scheduledArrival"))
        partida = horario_iso(item.get("startTime")) or horario_iso(de.get("departure"))
        chegada = horario_iso(item.get("endTime")) or horario_iso(para.get("arrival"))
        saida.append({
            "etapa": indice, "linha": linha, "sentido": item.get("headsign"),
            "operadora": item.get("agencyName"), "operadora_id": item.get("agencyId"),
            "codigo_linha": item.get("routeShortName"),
            "ponto": de.get("name"), "ponto_id": de.get("stopId"),
            "desembarque": para.get("name"), "desembarque_id": para.get("stopId"),
            "partida_programada": partida_programada, "chegada_programada": chegada_programada,
            "partida": partida or partida_programada, "chegada": chegada or chegada_programada,
            "tempo_real": tempo_real and partida is not None,
            "viagem_id": item.get("tripId"),
        })
    return saida


def etapas_completas(viagem):
    """Etapas ordenadas, inclusive sem traçado disponível."""
    etapas = []
    for i, leg in enumerate(viagem.get("legs", []), 1):
        de, para = leg.get("from") or {}, leg.get("to") or {}
        linha, cor = identificar_linha(leg)
        modo = str(leg.get("mode", "")).upper()
        duração = leg.get("duration")
        etapas.append({
            "etapa": i, "modal": modo, "linha": linha, "cor_linha": cor,
            "operadora": leg.get("agencyName"), "sentido": leg.get("headsign"),
            "de": de.get("name"), "para": para.get("name"),
            "partida": horario_iso(leg.get("startTime")) or horario_iso(de.get("departure")) or horario_iso(leg.get("scheduledStartTime")) or horario_iso(de.get("scheduledDeparture")),
            "chegada": horario_iso(leg.get("endTime")) or horario_iso(para.get("arrival")) or horario_iso(leg.get("scheduledEndTime")) or horario_iso(para.get("scheduledArrival")),
            "tempo_real": leg.get("realTime") is True,
            "tempo_min": round(duração / 60) if isinstance(duração, (int, float)) and math.isfinite(duração) and duração >= 0 else None,
            "paradas": [p.get("name") for p in leg.get("intermediateStops") or [] if isinstance(p, dict) and p.get("name")],
        })
    return etapas


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
        linha, cor_linha = identificar_linha(item)
        distancia_m = item.get("distance") if modo == "WALK" else None
        if not isinstance(distancia_m, (int, float)) or not math.isfinite(distancia_m) or distancia_m < 0:
            distancia_m = None
        trechos.append({
            "cor_linha": cor_linha,
            "distancia_m": round(distancia_m) if distancia_m is not None else None,
            "paradas": paradas,
            "modal": modo, "linha": linha,
            "destino_linha": item.get("headsign") or None,
            "de": a.get("name") or "Origem", "para": b.get("name") or "Destino",
            "tempo_min": round(float(item.get("duration", 0)) / 60),
            "trajeto": trajeto,
        })
    return trechos


def consultar_transitous(origem, destino, modal: str, priorizar_menos_caminhada: bool = False) -> dict:
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
        "maxPreTransitTime": 1800,
        "maxPostTransitTime": 1800,
        "maxMatchingDistance": 500,
    }
    # Para caminhada, solicitar rota direta; para transporte público desabilitar
    # rotas diretas que poderiam descartar opções de ônibus/ferrovia.
    if modal == "ape":
        params["directModes"] = "WALK"
    else:
        # Sem directModes vazio (pode invalidar array MOTIS); remove a viagem
        # direta para evitar o corte das conexões de transporte público.
        params["maxDirectTime"] = 0
    headers = {"User-Agent": os.getenv(
        "CITIZEN_TRANSIT_USER_AGENT",
        "CitizenTechFIAP/0.3 (https://github.com/lucasgesini45-coder/Global-solution-Citizen-tech)"
    )}
    def buscar(parametros):
        try:
            return _json_http(TRANSITOUS_URL + "?" + urlencode(parametros),
                              max_bytes=3_000_000, headers=headers)
        except HTTPException as exc:
            raise HTTPException(status_code=503, detail=(
                "Não foi possível calcular a rota pelo Transitous: "
                + str(exc.detail) + " Nenhuma linha fictícia foi desenhada."
            )) from exc

    resposta = buscar(params)
    viagens = resposta.get("direct", []) if modal == "ape" else resposta.get("itineraries", [])
    if not isinstance(viagens, list):
        viagens = []
    busca_ampliada = False
    # A segunda tentativa usa apenas paradas reais dentro de um raio de 1 km.
    # Esse modo pode não entregar caminhada detalhada: jamais inventar o caminho.
    if not viagens and modal != "ape":
        params_ampliados = {**params, "radius": 1000}
        resposta = buscar(params_ampliados)
        viagens = resposta.get("itineraries", [])
        if not isinstance(viagens, list):
            viagens = []
        busca_ampliada = True
    # Filtra para garantir que o modo escolhido de fato seja utilizado.
    permitidos = MODOS_ONIBUS if modal == "onibus" else MODOS_FERROVIARIOS
    if modal in {"onibus", "ferroviario"}:
        viagens = [v for v in viagens if any(
            str(leg.get("mode", "")).upper() in permitidos for leg in v.get("legs", [])
        )]
    opcoes = []
    for v in viagens[:16]:
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
    if not opcoes and not busca_ampliada and modal != "ape":
        params_ampliados = {**params, "radius": 1000}
        resposta = buscar(params_ampliados)
        viagens = resposta.get("itineraries", [])
        if not isinstance(viagens, list):
            viagens = []
        busca_ampliada = True
        if modal in {"onibus", "ferroviario"}:
            viagens = [v for v in viagens if any(
                str(leg.get("mode", "")).upper() in permitidos for leg in v.get("legs", [])
            )]
        for v in viagens[:16]:
            t = _trechos_viagem(v)
            if t and (modal == "todos" or any(item["modal"] in permitidos for item in t)):
                opcoes.append((v, t))
    if not opcoes:
        raise HTTPException(status_code=404, detail=(
            "Não foram encontradas viagens com geometria disponível para esse modal, "
            "local e horário no Transitous. Tente outro horário ou local."
        ))
    # Preferir uma opção com menos deslocamento a pé, desde que a duração
    # não aumente desproporcionalmente. Distâncias desconhecidas não viram 0.
    def caminhar_metros(viagem):
        valores = [leg.get("distance") for leg in viagem.get("legs", [])
                   if str(leg.get("mode", "")).upper() == "WALK"]
        if any(not isinstance(d, (int, float)) or not math.isfinite(d) or d < 0 for d in valores):
            return None
        return round(sum(valores))
    def pontuacao(opcao):
        viagem, _ = opcao
        caminhada = caminhar_metros(viagem)
        tempo = float(viagem.get("duration") or 999999) / 60
        if modal == "ape":
            return tempo
        # Evita escolher a viagem mais rápida quando ela exige caminhar muitos km.
        # Equivale a penalizar caminhada superior a 1,2 km com 1 min/100m extra.
        limite = 400 if priorizar_menos_caminhada else 1200
        penalidade = max(0, (caminhada - limite) / (35 if priorizar_menos_caminhada else 100)) if caminhada is not None else 0
        return tempo + penalidade
    from .economia import estimar
    ordenadas = sorted(opcoes, key=pontuacao)
    v, trechos = ordenadas[0]
    def resumir_alternativa(opcao, indice):
        viagem, partes = opcao
        etapas = etapas_completas(viagem)
        return {
            "id": indice, "tempo_min": round(float(viagem.get("duration", 0)) / 60),
            "caminhada_m": caminhar_metros(viagem),
            "etapas_viagem": etapas,
            "horarios_onibus": horarios_onibus(viagem),
            "custo": estimar(etapas),
            "trajeto": [pt for t in partes for pt in t["trajeto"]],
            "trechos": partes,
            "modal": modal,
        }
    alternativas = [resumir_alternativa(o, i) for i, o in enumerate(ordenadas[:5], 1)]

    caminhada_m = caminhar_metros(v)
    caminhada_longa = caminhada_m is not None and caminhada_m > 1500
    faltam_trechos = len(trechos) < len(v.get("legs", []))
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
        "horarios_onibus": horarios_onibus(v),
        "etapas_viagem": etapas_completas(v),
        "economia": alternativas[0]["custo"],
        "alternativas_economicas": alternativas,
        "busca_ampliada": busca_ampliada,
        "caminhada_m": caminhada_m,
        "caminhada_longa": caminhada_longa,
        "priorizou_menos_caminhada": priorizar_menos_caminhada,
        "aviso": ("Rota informada pelo Transitous. Horários podem mudar e não há "
                  "validação de tarifa, acessibilidade ou segurança. "
                  + (f"Atenção: esta rota exige cerca de {caminhada_m} metros a pé. Avalie outra opção de transporte. " if caminhada_longa else "")
                  + ("Busca ampliada para pontos próximos (até 1 km). " if busca_ampliada else "")
                  + ("Parte do acesso a pé não tem traçado disponível; verifique como chegar à estação ou parada. " if faltam_trechos else "")
                  + "Dados de transporte: https://transitous.org/sources/"),
    }
