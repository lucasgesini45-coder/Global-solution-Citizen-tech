# encoding: utf-8
"""Gerenciamento de conexões, inicialização, purga e exclusão no SQLite."""

from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

from backend.src.config_app import (
    obter_caminho_banco,
    RETENCAO_CONVERSAS_DIAS,
    RETENCAO_PERGUNTAS_SEM_RESPOSTA_DIAS,
    INTERVALO_PURGA_H,
)
from backend.src.rotas.config import RETENCAO_HISTORICO_DIAS
from .migracoes import aplicar_migracoes


def conectar(caminho: str | Path | None = None) -> sqlite3.Connection:
    """Abre uma conexão isolada com o banco SQLite aplicando as regras de DB-03."""
    if caminho is None:
        caminho = obter_caminho_banco()
    caminho_str = str(caminho)
    
    if caminho_str != ":memory:":
        Path(caminho_str).parent.mkdir(parents=True, exist_ok=True)
        
    con = sqlite3.connect(caminho_str, timeout=5.0)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA busy_timeout = 5000;")
    con.row_factory = sqlite3.Row
    return con


def iniciar_banco(caminho: str | Path | None = None) -> sqlite3.Connection:
    """Único ponto de criação, migração e inicialização do banco de dados (DB-09)."""
    con = conectar(caminho)
    aplicar_migracoes(con)
    return con


def purgar_expirados(banco: sqlite3.Connection, agora: datetime | None = None) -> None:
    """Remove registros fora da janela de retenção (DB-11 e DB-12)."""
    if agora is None:
        agora = datetime.now()
        
    limite_buscas = (agora - timedelta(days=RETENCAO_HISTORICO_DIAS)).isoformat()
    limite_conversas = (agora - timedelta(days=RETENCAO_CONVERSAS_DIAS)).isoformat()
    limite_perguntas = (agora - timedelta(days=RETENCAO_PERGUNTAS_SEM_RESPOSTA_DIAS)).isoformat()
    
    with banco:
        banco.execute(
            "DELETE FROM historico_buscas WHERE criado_em < ?",
            (limite_buscas,),
        )
        banco.execute(
            "DELETE FROM conversas WHERE atualizado_em < ?",
            (limite_conversas,),
        )
        banco.execute(
            "DELETE FROM perguntas_sem_resposta WHERE criado_em < ?",
            (limite_perguntas,),
        )
        banco.execute(
            "INSERT OR REPLACE INTO meta (chave, valor) VALUES ('ultima_purga', ?)",
            (agora.isoformat(),),
        )


def verificar_e_purgar_preguicoso(banco: sqlite3.Connection, agora: datetime | None = None) -> None:
    """Executa a purga se passou mais de INTERVALO_PURGA_H desde a última (DB-12)."""
    if agora is None:
        agora = datetime.now()
        
    cur = banco.cursor()
    cur.execute("SELECT valor FROM meta WHERE chave = 'ultima_purga'")
    row = cur.fetchone()
    if row:
        try:
            ultima_purga = datetime.fromisoformat(row["valor"])
            if (agora - ultima_purga) < timedelta(hours=INTERVALO_PURGA_H):
                return
        except (ValueError, TypeError):
            pass
            
    purgar_expirados(banco, agora)


def apagar_tudo(banco: sqlite3.Connection, usuario_id: str) -> dict[str, int]:
    """Apaga todos os dados de um usuário em uma transação atômica (DB-13).
    
    Retorna a contagem de registros apagados por categoria.
    """
    with banco:
        cur = banco.cursor()
        
        # Contagem de rotas antes da deleção em cascata
        cur.execute(
            """
            SELECT COUNT(*) FROM historico_rotas hr
            JOIN historico_buscas hb ON hr.busca_id = hb.id
            WHERE hb.sessao_id = ?
            """,
            (usuario_id,),
        )
        n_rotas = cur.fetchone()[0]
        
        # Contagem de buscas
        cur.execute(
            "SELECT COUNT(*) FROM historico_buscas WHERE sessao_id = ?",
            (usuario_id,),
        )
        n_buscas = cur.fetchone()[0]
        
        # Contagem de conversas
        cur.execute(
            "SELECT COUNT(*) FROM conversas WHERE usuario_id = ?",
            (usuario_id,),
        )
        n_conversas = cur.fetchone()[0]
        
        # Contagem de mensagens
        cur.execute(
            """
            SELECT COUNT(*) FROM mensagens m
            JOIN conversas c ON m.conversa_id = c.id
            WHERE c.usuario_id = ?
            """,
            (usuario_id,),
        )
        n_mensagens = cur.fetchone()[0]
        
        # Deleção (linhas em rotas, rotas_linhas, conversas, mensagens, etc. saem por cascade)
        cur.execute("DELETE FROM historico_buscas WHERE sessao_id = ?", (usuario_id,))
        cur.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        
    return {
        "buscas": n_buscas,
        "rotas": n_rotas,
        "conversas": n_conversas,
        "mensagens": n_mensagens,
    }
