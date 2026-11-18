# encoding: utf-8
"""Gerenciamento e aplicação de migrações SQL numeradas."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

PASTA_MIGRACOES = Path(__file__).resolve().parent / "migracoes"


def aplicar_migracoes(con: sqlite3.Connection) -> int:
    """Aplica todas as migrações pendentes em ordem crescente de versão.
    
    Retorna o número de migrações aplicadas.
    """
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versao (
            versao INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            aplicada_em TEXT NOT NULL
        )
        """
    )
    
    cur = con.cursor()
    cur.execute("SELECT versao FROM schema_versao")
    versoes_aplicadas = {row[0] for row in cur.fetchall()}
    
    arquivos = sorted(PASTA_MIGRACOES.glob("*.sql"))
    aplicadas = 0
    
    for arquivo in arquivos:
        nome_arquivo = arquivo.name
        partes = nome_arquivo.split("_", 1)
        if not partes[0].isdigit():
            continue
        versao = int(partes[0])
        nome = partes[1].rsplit(".", 1)[0] if len(partes) > 1 else partes[0]
        
        if versao in versoes_aplicadas:
            continue
            
        with open(arquivo, "r", encoding="utf-8") as fp:
            sql = fp.read()
            
        agora_iso = datetime.now(timezone.utc).isoformat()
        with con:
            con.executescript(sql)
            con.execute(
                "INSERT INTO schema_versao (versao, nome, aplicada_em) VALUES (?, ?, ?)",
                (versao, nome, agora_iso),
            )
        versoes_aplicadas.add(versao)
        aplicadas += 1
        
    return aplicadas
