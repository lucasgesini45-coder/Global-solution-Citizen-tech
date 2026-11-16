# encoding: utf-8
"""Configurações gerais da aplicação Citizen Mobilidade."""

import os
from pathlib import Path

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]

MODOS_VALIDOS = ("desenvolvimento", "producao", "teste")
RETENCAO_CONVERSAS_DIAS = 90
RETENCAO_PERGUNTAS_SEM_RESPOSTA_DIAS = 180
INTERVALO_PURGA_H = 24
LIMITE_PERGUNTAS_POR_MINUTO = 20
LIMITE_ROTAS_POR_MINUTO = 30
CONSENTIMENTO_TEXTO_VERSAO = "2026-11-v1"
FINALIDADES = (
    "historico_buscas",
    "conversa_assistente",
    "localizacao",
    "melhoria_assistente",
)


def obter_modo() -> str:
    modo = os.environ.get("CITIZEN_MODO", "desenvolvimento")
    if modo not in MODOS_VALIDOS:
        raise ValueError(
            f"CITIZEN_MODO inválido: '{modo}'. Valores permitidos: {MODOS_VALIDOS}"
        )
    return modo


def obter_caminho_banco() -> str:
    caminho = os.environ.get("CITIZEN_DB", "backend/data/citizen.db")
    caminho_path = Path(caminho)
    if not caminho_path.is_absolute():
        return str(RAIZ_REPOSITORIO / caminho_path)
    return str(caminho_path)


def obter_ors_api_key() -> str:
    return os.environ.get("ORS_API_KEY", "")


def obter_rotaviva_user_agent() -> str:
    return os.environ.get("ROTAVIVA_USER_AGENT", "")
