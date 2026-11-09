from __future__ import annotations

import datetime
import sqlite3
from typing import Any

from src.config import RETENCAO_HISTORICO_DIAS


def _conectar(banco: str) -> sqlite3.Connection:
    conn = sqlite3.connect(banco)
    conn.row_factory = sqlite3.Row
    return conn


def iniciar_banco(caminho: str) -> None:
    with _conectar(caminho) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_buscas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessao_id TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                origem_lat REAL NOT NULL,
                origem_lon REAL NOT NULL,
                destino_lat REAL NOT NULL,
                destino_lon REAL NOT NULL,
                partida TEXT NOT NULL,
                n_rotas INTEGER NOT NULL,
                erro_codigo TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_historico_sessao
            ON historico_buscas(sessao_id)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_geocodificacao (
                consulta TEXT PRIMARY KEY,
                resposta_json TEXT NOT NULL,
                obtido_em TEXT NOT NULL
            )
            """
        )
        conn.commit()


def registrar_busca(
    banco: str,
    sessao_id: str,
    pedido: dict[str, Any],
    resposta: dict[str, Any],
    agora: datetime.datetime | None = None,
) -> int:
    if agora is None:
        agora = datetime.datetime.now()
    criado_em = agora.isoformat()

    origem = pedido.get("origem", {})
    destino = pedido.get("destino", {})
    origem_lat = float(origem.get("lat", 0.0))
    origem_lon = float(origem.get("lon", 0.0))
    destino_lat = float(destino.get("lat", 0.0))
    destino_lon = float(destino.get("lon", 0.0))
    partida = str(pedido.get("partida", ""))

    n_rotas = int(resposta.get("n_rotas", len(resposta.get("rotas", []))))
    erro_codigo = None
    if n_rotas == 0 and resposta.get("erro"):
        erro_codigo = resposta["erro"].get("codigo")

    with _conectar(banco) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_buscas (
                sessao_id, criado_em, origem_lat, origem_lon,
                destino_lat, destino_lon, partida, n_rotas, erro_codigo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sessao_id,
                criado_em,
                origem_lat,
                origem_lon,
                destino_lat,
                destino_lon,
                partida,
                n_rotas,
                erro_codigo,
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def listar_historico(
    banco: str, sessao_id: str, limite: int = 20
) -> list[dict[str, Any]]:
    with _conectar(banco) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, sessao_id, criado_em, origem_lat, origem_lon,
                   destino_lat, destino_lon, partida, n_rotas, erro_codigo
            FROM historico_buscas
            WHERE sessao_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (sessao_id, limite),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def apagar_historico(banco: str, sessao_id: str) -> int:
    with _conectar(banco) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM historico_buscas WHERE sessao_id = ?",
            (sessao_id,),
        )
        removidos = cursor.rowcount
        conn.commit()
        return int(removidos)


def purgar_expirados(
    banco: str, agora: datetime.datetime | None = None
) -> int:
    if agora is None:
        agora = datetime.datetime.now()
    limite = agora - datetime.timedelta(days=RETENCAO_HISTORICO_DIAS)
    limite_str = limite.isoformat()

    with _conectar(banco) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM historico_buscas WHERE criado_em < ?",
            (limite_str,),
        )
        removidos = cursor.rowcount
        conn.commit()
        return int(removidos)
