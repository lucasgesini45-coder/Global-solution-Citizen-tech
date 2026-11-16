# encoding: utf-8
"""Testes do banco de dados SQL único (T-DB01 a T-DB10)."""

from datetime import datetime, timedelta
import sqlite3
import pytest

from backend.src.db.conexao import (
    conectar,
    iniciar_banco,
    purgar_expirados,
    apagar_tudo,
)
from backend.src.db.documentar import main as documentar_main, gerar_documentacao


def test_t_db01_iniciar_banco_idempotente(tmp_path):
    caminho = str(tmp_path / "test_citizen.db")
    con1 = iniciar_banco(caminho)
    con1.close()
    
    # Segunda chamada não deve falhar
    con2 = iniciar_banco(caminho)
    cur = con2.cursor()
    cur.execute("SELECT versao, nome FROM schema_versao ORDER BY versao")
    linhas = cur.fetchall()
    con2.close()
    
    assert len(linhas) == 6
    assert [row["versao"] for row in linhas] == [1, 2, 3, 4, 5, 6]


def test_t_db02_pragmas_conexao(tmp_path):
    caminho = str(tmp_path / "test_pragmas.db")
    iniciar_banco(caminho).close()
    
    con = conectar(caminho)
    cur = con.cursor()
    
    cur.execute("PRAGMA foreign_keys")
    fk = cur.fetchone()[0]
    
    cur.execute("PRAGMA journal_mode")
    jm = cur.fetchone()[0].lower()
    
    cur.execute("PRAGMA busy_timeout")
    bt = cur.fetchone()[0]
    
    con.close()
    
    assert fk == 1
    assert jm == "wal"
    assert bt == 5000


def test_t_db03_check_origem_dados(tmp_path):
    caminho = str(tmp_path / "test_check.db")
    con = iniciar_banco(caminho)
    
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            """
            INSERT INTO feeds (sistema, fonte_url, arquivo_nome, arquivo_sha256, versao, origem_dados, importado_em, n_paradas, n_linhas, n_padroes, n_viagens)
            VALUES ('sptrans', 'http://exemplo.com', 'feed.zip', 'hash1', 'v1', 'simulado', '2026-11-15T00:00:00', 10, 2, 2, 20)
            """
        )
        
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            """
            INSERT INTO tarifas_regras (versao, fonte_descricao, fonte_url, confirmada, origem_dados, vigencia_inicio, janela_s, max_embarques_por_janela)
            VALUES ('v1', 'fonte', 'http://sp.gov.br', 0, 'simulado', '2026-01-01', 7200, 2)
            """
        )
    con.close()


def test_t_db04_check_tarifas_regras_confirmada(tmp_path):
    caminho = str(tmp_path / "test_tarifas_confirmada.db")
    con = iniciar_banco(caminho)
    
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            """
            INSERT INTO tarifas_regras (versao, fonte_descricao, fonte_url, verificada_em, confirmada, origem_dados, vigencia_inicio, janela_s, max_embarques_por_janela)
            VALUES ('v1', 'fonte', 'http://sp.gov.br', NULL, 1, 'real', '2026-01-01', 7200, 2)
            """
        )
        
    with pytest.raises(sqlite3.IntegrityError):
        con.execute(
            """
            INSERT INTO tarifas_regras (versao, fonte_descricao, fonte_url, verificada_em, confirmada, origem_dados, vigencia_inicio, janela_s, max_embarques_por_janela)
            VALUES ('v2', 'fonte', '', '2026-11-15', 1, 'real', '2026-01-01', 7200, 2)
            """
        )
    con.close()


def test_t_db05_indice_unico_parcial_feeds_ativos(tmp_path):
    caminho = str(tmp_path / "test_feeds_ativos.db")
    con = iniciar_banco(caminho)
    
    with con:
        con.execute(
            """
            INSERT INTO feeds (sistema, fonte_url, arquivo_nome, arquivo_sha256, versao, origem_dados, importado_em, ativo, n_paradas, n_linhas, n_padroes, n_viagens)
            VALUES ('sptrans', 'http://exemplo.com/1', 'f1.zip', 'hash1', 'v1', 'real', '2026-11-15T00:00:00', 1, 10, 2, 2, 20)
            """
        )
        # Outro sistema ativo: deve ser aceito
        con.execute(
            """
            INSERT INTO feeds (sistema, fonte_url, arquivo_nome, arquivo_sha256, versao, origem_dados, importado_em, ativo, n_paradas, n_linhas, n_padroes, n_viagens)
            VALUES ('metroferroviario', 'http://exemplo.com/2', 'f2.zip', 'hash2', 'v2', 'real', '2026-11-15T00:00:00', 1, 15, 3, 3, 30)
            """
        )
        
    # Segundo feed ativo do mesmo sistema 'sptrans': deve ser rejeitado pelo índice parcial único
    with pytest.raises(sqlite3.IntegrityError):
        with con:
            con.execute(
                """
                INSERT INTO feeds (sistema, fonte_url, arquivo_nome, arquivo_sha256, versao, origem_dados, importado_em, ativo, n_paradas, n_linhas, n_padroes, n_viagens)
                VALUES ('sptrans', 'http://exemplo.com/3', 'f3.zip', 'hash3', 'v3', 'real', '2026-11-15T00:00:00', 1, 10, 2, 2, 20)
                """
            )
            
    # Segundo feed do mesmo sistema com ativo=0: deve ser aceito
    with con:
        con.execute(
            """
            INSERT INTO feeds (sistema, fonte_url, arquivo_nome, arquivo_sha256, versao, origem_dados, importado_em, ativo, n_paradas, n_linhas, n_padroes, n_viagens)
            VALUES ('sptrans', 'http://exemplo.com/3', 'f3.zip', 'hash3', 'v3', 'real', '2026-11-15T00:00:00', 0, 10, 2, 2, 20)
            """
        )
    con.close()


def test_t_db06_cascade_delete_usuario(tmp_path):
    caminho = str(tmp_path / "test_cascade.db")
    con = iniciar_banco(caminho)
    
    uid = "usr-1234"
    cid = "conv-5678"
    
    with con:
        con.execute(
            "INSERT INTO usuarios (id, token_hash, criado_em, ultimo_acesso_em) VALUES (?, ?, ?, ?)",
            (uid, "thash", "2026-11-15T00:00:00", "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO consentimentos (usuario_id, finalidade, concedido, texto_versao, atualizado_em) VALUES (?, ?, 1, 'v1', ?)",
            (uid, "historico_buscas", "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO preferencias (usuario_id, atualizado_em) VALUES (?, ?)",
            (uid, "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em, titulo) VALUES (?, ?, ?, ?, 'Conversa 1')",
            (cid, uid, "2026-11-15T00:00:00", "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO mensagens (id, conversa_id, papel, texto, criado_em) VALUES (10, ?, 'usuario', 'Olá', ?)",
            (cid, "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO conversas_contexto (conversa_id, atualizado_em) VALUES (?, ?)",
            (cid, "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO feedback_mensagens (mensagem_id, util, criado_em) VALUES (10, 1, ?)",
            ("2026-11-15T00:00:00",),
        )
        
    # Verificar inserção
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM consentimentos WHERE usuario_id = ?", (uid,))
    assert cur.fetchone()[0] == 1
    
    # Deletar usuário direto no SQL
    with con:
        con.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
        
    cur.execute("SELECT count(*) FROM consentimentos WHERE usuario_id = ?", (uid,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM preferencias WHERE usuario_id = ?", (uid,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM conversas WHERE usuario_id = ?", (uid,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM mensagens WHERE conversa_id = ?", (cid,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM conversas_contexto WHERE conversa_id = ?", (cid,))
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM feedback_mensagens WHERE mensagem_id = 10")
    assert cur.fetchone()[0] == 0
    con.close()


def test_t_db07_sql_injection_seguranca(tmp_path):
    caminho = str(tmp_path / "test_sqli.db")
    con = iniciar_banco(caminho)
    
    payload = "'; DROP TABLE usuarios; --"
    uid = "usr-inj"
    
    with con:
        con.execute(
            "INSERT INTO usuarios (id, token_hash, criado_em, ultimo_acesso_em) VALUES (?, ?, ?, ?)",
            (uid, "thash", "2026-11-15T00:00:00", "2026-11-15T00:00:00"),
        )
        con.execute(
            "INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em, titulo) VALUES (?, ?, ?, ?, ?)",
            ("cid-inj", uid, "2026-11-15T00:00:00", "2026-11-15T00:00:00", payload),
        )
        con.execute(
            "INSERT INTO mensagens (conversa_id, papel, texto, criado_em) VALUES (?, 'usuario', ?, ?)",
            ("cid-inj", payload, "2026-11-15T00:00:00"),
        )
        con.execute(
            """
            INSERT INTO historico_buscas (sessao_id, criado_em, origem_lat, origem_lon, destino_lat, destino_lon, partida, n_rotas, origem_nome)
            VALUES (?, ?, -23.5, -46.6, -23.6, -46.7, '2026-11-15T08:00:00', 1, ?)
            """,
            (uid, "2026-11-15T00:00:00", payload),
        )
        
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM usuarios")
    assert cur.fetchone()[0] == 1
    
    cur.execute("SELECT titulo FROM conversas WHERE id = 'cid-inj'")
    assert cur.fetchone()[0] == payload
    
    cur.execute("SELECT texto FROM mensagens WHERE conversa_id = 'cid-inj'")
    assert cur.fetchone()[0] == payload
    
    cur.execute("SELECT origem_nome FROM historico_buscas WHERE sessao_id = ?", (uid,))
    assert cur.fetchone()[0] == payload
    con.close()


def test_t_db08_purga_expirados(tmp_path):
    caminho = str(tmp_path / "test_purga.db")
    con = iniciar_banco(caminho)
    
    agora = datetime(2026, 11, 15, 12, 0, 0)
    d91 = (agora - timedelta(days=91)).isoformat()
    d89 = (agora - timedelta(days=89)).isoformat()
    d181 = (agora - timedelta(days=181)).isoformat()
    d179 = (agora - timedelta(days=179)).isoformat()
    
    with con:
        con.execute(
            "INSERT INTO usuarios (id, token_hash, criado_em, ultimo_acesso_em) VALUES ('u1', 'th', '2026-01-01', '2026-01-01')"
        )
        # Buscas: 91 dias (deve sair) e 89 dias (deve ficar)
        con.execute(
            "INSERT INTO historico_buscas (id, sessao_id, criado_em, origem_lat, origem_lon, destino_lat, destino_lon, partida, n_rotas) VALUES (1, 'u1', ?, 0, 0, 0, 0, 'part', 1)",
            (d91,),
        )
        con.execute(
            "INSERT INTO historico_buscas (id, sessao_id, criado_em, origem_lat, origem_lon, destino_lat, destino_lon, partida, n_rotas) VALUES (2, 'u1', ?, 0, 0, 0, 0, 'part', 1)",
            (d89,),
        )
        # Conversas: 91 dias (deve sair) e 89 dias (deve ficar)
        con.execute(
            "INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em, titulo) VALUES ('c91', 'u1', ?, ?, 'Antiga')",
            (d91, d91),
        )
        con.execute(
            "INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em, titulo) VALUES ('c89', 'u1', ?, ?, 'Recente')",
            (d89, d89),
        )
        # Perguntas sem resposta: 181 dias (deve sair) e 179 dias (deve ficar)
        con.execute(
            "INSERT INTO perguntas_sem_resposta (id, texto, criado_em, confianca) VALUES (1, 'antiga', ?, 0.2)",
            (d181,),
        )
        con.execute(
            "INSERT INTO perguntas_sem_resposta (id, texto, criado_em, confianca) VALUES (2, 'recente', ?, 0.2)",
            (d179,),
        )
        
    purgar_expirados(con, agora)
    
    cur = con.cursor()
    cur.execute("SELECT id FROM historico_buscas")
    assert [r[0] for r in cur.fetchall()] == [2]
    
    cur.execute("SELECT id FROM conversas")
    assert [r[0] for r in cur.fetchall()] == ["c89"]
    
    cur.execute("SELECT id FROM perguntas_sem_resposta")
    assert [r[0] for r in cur.fetchall()] == [2]
    
    cur.execute("SELECT valor FROM meta WHERE chave = 'ultima_purga'")
    assert cur.fetchone()[0] == agora.isoformat()
    con.close()


def test_t_db09_apagar_tudo_isolamento(tmp_path):
    caminho = str(tmp_path / "test_apagar_tudo.db")
    con = iniciar_banco(caminho)
    
    with con:
        con.execute("INSERT INTO usuarios (id, token_hash, criado_em, ultimo_acesso_em) VALUES ('usr-A', 'hA', '2026-11-01', '2026-11-01')")
        con.execute("INSERT INTO usuarios (id, token_hash, criado_em, ultimo_acesso_em) VALUES ('usr-B', 'hB', '2026-11-01', '2026-11-01')")
        
        # Dados de A
        con.execute("INSERT INTO historico_buscas (id, sessao_id, criado_em, origem_lat, origem_lon, destino_lat, destino_lon, partida, n_rotas) VALUES (10, 'usr-A', '2026-11-01', 0, 0, 0, 0, 'p', 1)")
        con.execute("INSERT INTO historico_rotas (id, busca_id, ordem, saida_s, chegada_s, tempo_total_s, espera_s, caminhada_m, baldeacoes, custo_confirmado) VALUES (100, 10, 1, 0, 100, 100, 0, 50, 0, 1)")
        con.execute("INSERT INTO historico_rota_linhas (rota_id, posicao, linha_id, nome_linha, modal, operador) VALUES (100, 1, 'L1', 'Linha 1', 'onibus', 'SPTrans')")
        con.execute("INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em) VALUES ('cA', 'usr-A', '2026-11-01', '2026-11-01')")
        con.execute("INSERT INTO mensagens (id, conversa_id, papel, texto, criado_em) VALUES (1, 'cA', 'usuario', 'Msg A', '2026-11-01')")
        
        # Dados de B
        con.execute("INSERT INTO historico_buscas (id, sessao_id, criado_em, origem_lat, origem_lon, destino_lat, destino_lon, partida, n_rotas) VALUES (20, 'usr-B', '2026-11-01', 0, 0, 0, 0, 'p', 1)")
        con.execute("INSERT INTO historico_rotas (id, busca_id, ordem, saida_s, chegada_s, tempo_total_s, espera_s, caminhada_m, baldeacoes, custo_confirmado) VALUES (200, 20, 1, 0, 200, 200, 0, 80, 0, 1)")
        con.execute("INSERT INTO historico_rota_linhas (rota_id, posicao, linha_id, nome_linha, modal, operador) VALUES (200, 1, 'L2', 'Linha 2', 'metro', 'Metro')")
        con.execute("INSERT INTO conversas (id, usuario_id, criado_em, atualizado_em) VALUES ('cB', 'usr-B', '2026-11-01', '2026-11-01')")
        con.execute("INSERT INTO mensagens (id, conversa_id, papel, texto, criado_em) VALUES (2, 'cB', 'usuario', 'Msg B', '2026-11-01')")
        
        # Perguntas sem resposta (anonimizada)
        con.execute("INSERT INTO perguntas_sem_resposta (id, texto, criado_em, confianca) VALUES (99, 'sem resposta', '2026-11-01', 0.1)")
        
    contagens = apagar_tudo(con, "usr-A")
    assert contagens == {
        "buscas": 1,
        "rotas": 1,
        "conversas": 1,
        "mensagens": 1,
    }
    
    cur = con.cursor()
    # Verifica que dados de A sumiram
    cur.execute("SELECT count(*) FROM usuarios WHERE id = 'usr-A'")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM historico_buscas WHERE sessao_id = 'usr-A'")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM historico_rotas WHERE busca_id = 10")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM historico_rota_linhas WHERE rota_id = 100")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM conversas WHERE usuario_id = 'usr-A'")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT count(*) FROM mensagens WHERE conversa_id = 'cA'")
    assert cur.fetchone()[0] == 0
    
    # Verifica que dados de B e perguntas_sem_resposta estão intactos
    cur.execute("SELECT count(*) FROM usuarios WHERE id = 'usr-B'")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM historico_buscas WHERE sessao_id = 'usr-B'")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM historico_rotas WHERE busca_id = 20")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM historico_rota_linhas WHERE rota_id = 200")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM conversas WHERE usuario_id = 'usr-B'")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM mensagens WHERE conversa_id = 'cB'")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM perguntas_sem_resposta WHERE id = 99")
    assert cur.fetchone()[0] == 1
    con.close()


def test_t_db10_documentar(tmp_path):
    saida = tmp_path / "esquema_banco.md"
    documentar_main(caminho_saida=saida)
    assert saida.exists()
    
    conteudo = saida.read_text(encoding="utf-8")
    tabelas_obrigatorias = [
        "schema_versao",
        "meta",
        "feeds",
        "paradas",
        "linhas",
        "servicos",
        "servicos_excecoes",
        "padroes",
        "padrao_paradas",
        "viagens",
        "tarifas_regras",
        "tarifas_base",
        "tarifas_integracao",
        "tarifas_perfis",
        "usuarios",
        "consentimentos",
        "preferencias",
        "preferencias_acessibilidade",
        "historico_buscas",
        "historico_rotas",
        "historico_rota_linhas",
        "cache_geocodificacao",
        "conversas",
        "mensagens",
        "conversas_contexto",
        "feedback_mensagens",
        "perguntas_sem_resposta",
    ]
    for tab in tabelas_obrigatorias:
        assert f"`{tab}`" in conteudo
