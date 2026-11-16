# encoding: utf-8
"""Gera docs/esquema_banco.md a partir da introspecção real do SQLite (DB-10)."""

import argparse
from pathlib import Path
import sqlite3

from backend.src.config_app import RAIZ_REPOSITORIO
from .conexao import iniciar_banco


def gerar_documentacao(banco: sqlite3.Connection) -> str:
    """Gera documentação em Markdown inspecionando tabelas, colunas, chaves e índices."""
    cur = banco.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tabelas = [row[0] for row in cur.fetchall()]
    
    linhas = [
        "# Esquema do Banco de Dados SQL Único (Citizen Mobilidade)",
        "",
        "Documento gerado automaticamente por introspecção do banco SQLite (`PRAGMA table_info`, `foreign_key_list`, `index_list`).",
        "",
        "---",
        "",
    ]
    
    for tabela in tabelas:
        linhas.append(f"## Tabela `{tabela}`")
        linhas.append("")
        
        # Colunas
        cur.execute(f"PRAGMA table_info({tabela})")
        colunas = cur.fetchall()
        linhas.append("### Colunas")
        linhas.append("| Nome | Tipo | Não Nulo? | Valor Padrão | Chave Primária |")
        linhas.append("|---|---|---|---|---|")
        for col in colunas:
            pk = "Sim" if col[5] > 0 else "Não"
            notnull = "Sim" if col[3] else "Não"
            dflt = col[4] if col[4] is not None else "-"
            linhas.append(f"| `{col[1]}` | `{col[2]}` | {notnull} | `{dflt}` | {pk} |")
        linhas.append("")
        
        # Chaves Estrangeiras
        cur.execute(f"PRAGMA foreign_key_list({tabela})")
        fks = cur.fetchall()
        if fks:
            linhas.append("### Chaves Estrangeiras")
            linhas.append("| Coluna Local | Tabela Destino | Coluna Destino | ON DELETE |")
            linhas.append("|---|---|---|---|")
            for fk in fks:
                linhas.append(f"| `{fk[3]}` | `{fk[2]}` | `{fk[4]}` | `{fk[6]}` |")
            linhas.append("")
            
        # Índices
        cur.execute(f"PRAGMA index_list({tabela})")
        indices = cur.fetchall()
        indices_usuario = [idx for idx in indices if not idx[1].startswith("sqlite_autoindex_")]
        if indices_usuario:
            linhas.append("### Índices")
            linhas.append("| Nome do Índice | Único? | Parcial? |")
            linhas.append("|---|---|---|")
            for idx in indices_usuario:
                unico = "Sim" if idx[2] else "Não"
                parcial = "Sim" if idx[4] else "Não"
                linhas.append(f"| `{idx[1]}` | {unico} | {parcial} |")
            linhas.append("")
            
        linhas.append("---")
        linhas.append("")
        
    return "\n".join(linhas)


def main(caminho_saida: Path | str | None = None, caminho_banco: str | None = None) -> None:
    if caminho_saida is None:
        caminho_saida = RAIZ_REPOSITORIO / "docs" / "esquema_banco.md"
    saida_path = Path(caminho_saida)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    
    con = iniciar_banco(caminho_banco or ":memory:")
    doc = gerar_documentacao(con)
    con.close()
    
    with open(saida_path, "w", encoding="utf-8") as fp:
        fp.write(doc)
    print(f"Esquema documentado com sucesso em: {saida_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Documentar esquema do banco SQLite.")
    parser.add_argument("--saida", type=str, default=None, help="Caminho do arquivo markdown de saída.")
    parser.add_argument("--banco", type=str, default=None, help="Caminho do banco a ser inspecionado.")
    args = parser.parse_args()
    main(args.saida, args.banco)
