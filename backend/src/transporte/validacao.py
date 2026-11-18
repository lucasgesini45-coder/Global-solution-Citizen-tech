# encoding: utf-8
"""Validações e regras de negócio de importação GTFS."""

from typing import Any
from backend.src.rotas.config import SP_LIMITES


def mapear_modal(sistema: str, route_type_val: Any) -> str | None:
    """Mapeia o route_type do GTFS para os modais suportados (Seção 7.3)."""
    try:
        rt = int(route_type_val)
    except (ValueError, TypeError):
        return None
        
    if sistema == "emtu":
        if rt == 3:
            return "onibus_metropolitano"
        return None
        
    if rt == 3:
        return "onibus"
    elif rt in (0, 1, 12):
        return "metro"
    elif rt == 2:
        return "trem"
    return None


def ponto_em_sp_limites(lat: float, lon: float) -> bool:
    """Verifica se as coordenadas estão dentro dos limites geográficos de SP (GT-06)."""
    lat_min, lon_min, lat_max, lon_max = SP_LIMITES
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def parse_hhmmss_para_segundos(texto: str) -> int:
    """Converte HH:MM:SS para segundos desde 00:00 (podendo passar de 86400)."""
    partes = texto.strip().split(":")
    if len(partes) != 3:
        raise ValueError(f"Formato de horário inválido: '{texto}'")
    h, m, s = int(partes[0]), int(partes[1]), int(partes[2])
    return h * 3600 + m * 60 + s
