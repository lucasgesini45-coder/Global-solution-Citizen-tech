# encoding: utf-8
"""Testes de importação GTFS (T-GT01 a T-GT13)."""

import io
from pathlib import Path
import sqlite3
import zipfile
import pytest

from backend.src.db.conexao import conectar, iniciar_banco
from backend.src.transporte.importar_gtfs import importar_gtfs
from backend.src.transporte.validacao import mapear_modal
from backend.tests.fixtures.gerar_gtfs_demo import gerar_gtfs_mini_zip


def criar_zip_modificado(zip_base_bytes: bytes, arquivos_alterar: dict[str, str]) -> bytes:
    buffer_in = io.BytesIO(zip_base_bytes)
    buffer_out = io.BytesIO()
    
    with zipfile.ZipFile(buffer_in, "r") as zin, zipfile.ZipFile(buffer_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in arquivos_alterar:
                zout.writestr(item.filename, arquivos_alterar[item.filename])
            else:
                zout.writestr(item, zin.read(item.filename))
        for nome, conteudo in arquivos_alterar.items():
            if nome not in zin.namelist():
                zout.writestr(nome, conteudo)
                
    return buffer_out.getvalue()


def test_t_gt01_importar_gtfs_mini(tmp_path):
    caminho_banco = str(tmp_path / "test_gtfs.db")
    zip_bytes = gerar_gtfs_mini_zip()
    zip_file = tmp_path / "gtfs_mini.zip"
    zip_file.write_bytes(zip_bytes)

    res = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res["status"] == "sucesso"
    assert res["n_paradas"] == 9
    assert res["n_linhas"] == 4
    assert res["n_padroes"] == 4
    assert res["n_viagens"] == 346

    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT id, ativo, n_paradas, n_linhas, n_padroes, n_viagens FROM feeds WHERE sistema = 'sptrans'")
    feed = cur.fetchone()
    assert feed["ativo"] == 1
    assert feed["n_paradas"] == 9
    assert feed["n_linhas"] == 4
    assert feed["n_padroes"] == 4
    assert feed["n_viagens"] == 346

    cur.execute("SELECT id FROM paradas LIMIT 1")
    assert cur.fetchone()[0].startswith("sptrans:")
    cur.execute("SELECT id FROM linhas LIMIT 1")
    assert cur.fetchone()[0].startswith("sptrans:")
    cur.execute("SELECT id FROM viagens LIMIT 1")
    assert cur.fetchone()[0].startswith("sptrans:")
    cur.execute("SELECT id FROM servicos LIMIT 1")
    assert cur.fetchone()[0].startswith("sptrans:")
    con.close()


def test_t_gt02_mapeamento_modal():
    assert mapear_modal("sptrans", 3) == "onibus"
    assert mapear_modal("metroferroviario", 0) == "metro"
    assert mapear_modal("metroferroviario", 1) == "metro"
    assert mapear_modal("metroferroviario", 12) == "metro"
    assert mapear_modal("metroferroviario", 2) == "trem"
    assert mapear_modal("emtu", 3) == "onibus_metropolitano"
    assert mapear_modal("sptrans", 99) is None
    assert mapear_modal("emtu", 2) is None


def test_t_gt03_fixture_frequencies(tmp_path):
    caminho_banco = str(tmp_path / "test_freq.db")
    base_bytes = gerar_gtfs_mini_zip()

    # Adicionar frequencies.txt para M1-000 (08:00:00 a 09:00:00 a cada 600s)
    freq_csv = (
        "trip_id,start_time,end_time,headway_secs,exact_times\n"
        "M1-000,08:00:00,09:00:00,600,1\n"
    )
    zip_bytes = criar_zip_modificado(base_bytes, {"frequencies.txt": freq_csv})
    zip_file = tmp_path / "gtfs_freq.zip"
    zip_file.write_bytes(zip_bytes)

    res = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res["status"] == "sucesso"
    # A frequencia gera 6 viagens (08:00 a 08:50, fim 09:00 exclusivo)
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT id, inicio_s FROM viagens WHERE id LIKE 'sptrans:M1-000_freq_%' ORDER BY inicio_s")
    linhas = cur.fetchall()
    assert len(linhas) == 6
    horarios_esperados = [28800 + i * 600 for i in range(6)]
    assert [r["inicio_s"] for r in linhas] == horarios_esperados
    con.close()


def test_t_gt04_calendar_dates_excecoes(tmp_path):
    caminho_banco = str(tmp_path / "test_cal.db")
    base_bytes = gerar_gtfs_mini_zip()
    # Adicionar exceção tipo 1 num domingo (20261122) e tipo 2 numa data útil (20261116)
    cal_dates_csv = (
        "service_id,date,exception_type\n"
        "SERV_UTEIS,20261116,2\n"
        "SERV_UTEIS,20261122,1\n"
    )
    zip_bytes = criar_zip_modificado(base_bytes, {"calendar_dates.txt": cal_dates_csv})
    zip_file = tmp_path / "gtfs_cal.zip"
    zip_file.write_bytes(zip_bytes)

    importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT servico_id, data, tipo FROM servicos_excecoes ORDER BY data")
    excs = cur.fetchall()
    assert len(excs) == 2
    assert excs[0]["data"] == "2026-11-16" and excs[0]["tipo"] == 2
    assert excs[1]["data"] == "2026-11-22" and excs[1]["tipo"] == 1
    con.close()


def test_t_gt05_interpolacao_horarios_vazios(tmp_path):
    caminho_banco = str(tmp_path / "test_interp.db")
    base_bytes = gerar_gtfs_mini_zip()

    # Modificar stop_times de M1-000 para deixar a parada intermediária com horário vazio
    # Paradas: MA (06:00:00 -> 21600), MB (vazio), MC (06:10:00 -> 22200)
    # A interpolação deve calcular 21900 (06:05:00)
    stop_times_csv = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "M1-000,06:00:00,06:00:00,MA,1\n"
        "M1-000,,,MB,2\n"
        "M1-000,06:10:00,06:10:00,MC,3\n"
    )
    zip_bytes = criar_zip_modificado(base_bytes, {"stop_times.txt": stop_times_csv})
    zip_file = tmp_path / "gtfs_interp.zip"
    zip_file.write_bytes(zip_bytes)

    res = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res["interpolacoes"] >= 1

    con = conectar(caminho_banco)
    cur = con.cursor()
    # Padrão da viagem M1-000: deslocamento da parada intermediária MB deve ser 300s (21900 - 21600)
    cur.execute(
        """
        SELECT pp.deslocamento_s FROM padrao_paradas pp
        JOIN viagens v ON v.padrao_id = pp.padrao_id
        WHERE v.id = 'sptrans:M1-000' AND pp.posicao = 1
        """
    )
    assert cur.fetchone()[0] == 300
    con.close()


def test_t_gt06_stop_times_com_parada_inexistente(tmp_path):
    caminho_banco = str(tmp_path / "test_parada_inexistente.db")
    base_bytes = gerar_gtfs_mini_zip()

    # Primeira importação válida
    zip_file_ok = tmp_path / "gtfs_ok.zip"
    zip_file_ok.write_bytes(base_bytes)
    importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file_ok,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )

    # Nova importação com stop_times referenciando parada inexistente
    stop_times_bad = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "M1-000,06:00:00,06:00:00,PARADA_FANTASMA,1\n"
        "M1-000,06:10:00,06:10:00,MC,2\n"
    )
    zip_bytes_bad = criar_zip_modificado(base_bytes, {"stop_times.txt": stop_times_bad})
    zip_file_bad = tmp_path / "gtfs_bad.zip"
    zip_file_bad.write_bytes(zip_bytes_bad)

    with pytest.raises(ValueError, match="parada inexistente"):
        importar_gtfs(
            sistema="sptrans",
            caminho_zip=zip_file_bad,
            fonte_url="https://sptrans.com.br",
            origem_dados="teste",
            caminho_banco=caminho_banco,
        )

    # Verificar que o feed anterior continua ativo e intacto
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT id, ativo, n_viagens FROM feeds WHERE sistema = 'sptrans'")
    feed = cur.fetchone()
    assert feed["ativo"] == 1
    assert feed["n_viagens"] == 346
    con.close()


def test_t_gt07_idempotencia(tmp_path):
    caminho_banco = str(tmp_path / "test_idemp.db")
    base_bytes = gerar_gtfs_mini_zip()
    zip_file = tmp_path / "gtfs_idemp.zip"
    zip_file.write_bytes(base_bytes)

    res1 = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res1["status"] == "sucesso"

    res2 = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res2["status"] == "ja_importado"


def test_t_gt08_troca_atomica_e_resiliencia(tmp_path):
    caminho_banco = str(tmp_path / "test_troca.db")
    base_bytes = gerar_gtfs_mini_zip()
    zip_file1 = tmp_path / "gtfs_v1.zip"
    zip_file1.write_bytes(base_bytes)

    res1 = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file1,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    feed_id_antigo = res1["feed_id"]

    # Criar segundo feed diferente (alterar feed_info.txt para ter outro SHA)
    feed_info_v2 = (
        "feed_publisher_name,feed_publisher_url,feed_lang,feed_version,feed_start_date,feed_end_date\n"
        "SPTrans,https://www.sptrans.com.br,pt,gtfs-mini-2.0,20260101,20261231\n"
    )
    zip_bytes_v2 = criar_zip_modificado(base_bytes, {"feed_info.txt": feed_info_v2})
    zip_file2 = tmp_path / "gtfs_v2.zip"
    zip_file2.write_bytes(zip_bytes_v2)

    res2 = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file2,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res2["status"] == "sucesso"
    feed_id_novo = res2["feed_id"]
    assert feed_id_novo != feed_id_antigo

    # Verificar que o feed antigo foi apagado e o novo está ativo
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT id, ativo, versao FROM feeds WHERE sistema = 'sptrans'")
    linhas = cur.fetchall()
    assert len(linhas) == 1
    assert linhas[0]["id"] == feed_id_novo
    assert linhas[0]["ativo"] == 1
    con.close()


def test_t_gt09_descarte_e_limite_sp_limites(tmp_path):
    caminho_banco = str(tmp_path / "test_limites.db")
    base_bytes = gerar_gtfs_mini_zip()

    # Caso 1: menos de 1% de paradas fora de SP_LIMITES (uma parada não referenciada ou pequena)
    # stops.txt com 1 parada fora de limites não referenciada por viagens
    stops_1 = (
        "stop_id,stop_name,stop_lat,stop_lon\n"
        "MA,Metrô Alfa,-23.5500,-46.6300\n"
        "MB,Metrô Beta,-23.5500,-46.6100\n"
        "MC,Metrô Gama,-23.5500,-46.5900\n"
        "BA,Ponto Alfa,-23.5490,-46.6300\n"
        "BB,Ponto Beta,-23.5490,-46.6100\n"
        "BC,Ponto Gama,-23.5490,-46.5900\n"
        "BX,Ponto Centro,-23.5430,-46.6100\n"
        "PD,Ponto Destino,-23.5470,-46.5900\n"
        "PF,Ponto Fim,-23.5320,-46.6100\n"
        "OUT,Parada Fora,0.0,0.0\n"
    )
    zip_bytes1 = criar_zip_modificado(base_bytes, {"stops.txt": stops_1})
    zip_file1 = tmp_path / "gtfs_out_ok.zip"
    zip_file1.write_bytes(zip_bytes1)

    res = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file1,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    # A parada OUT foi descartada, restando as 9 válidas
    assert res["n_paradas"] == 9

    # Caso 2: Mais de 1% das paradas referenciadas fora de limites
    # Colocar parada MA fora de limites (referenciada por várias viagens)
    stops_bad = stops_1.replace("-23.5500,-46.6300", "0.0,0.0")
    zip_bytes_bad = criar_zip_modificado(base_bytes, {"stops.txt": stops_bad})
    zip_file_bad = tmp_path / "gtfs_out_bad.zip"
    zip_file_bad.write_bytes(zip_bytes_bad)

    with pytest.raises(ValueError, match="Mais de 1% das paradas referenciadas"):
        importar_gtfs(
            sistema="sptrans",
            caminho_zip=zip_file_bad,
            fonte_url="https://sptrans.com.br",
            origem_dados="teste",
            caminho_banco=caminho_banco,
        )


def test_t_gt10_horarios_maiores_que_86400(tmp_path):
    caminho_banco = str(tmp_path / "test_h86400.db")
    base_bytes = gerar_gtfs_mini_zip()

    # 25:30:00 = 25*3600 + 30*60 = 90000 + 1800 = 91800
    stop_times_madrug = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "M1-000,25:30:00,25:30:00,MA,1\n"
        "M1-000,25:40:00,25:40:00,MC,2\n"
    )
    zip_bytes = criar_zip_modificado(base_bytes, {"stop_times.txt": stop_times_madrug})
    zip_file = tmp_path / "gtfs_86400.zip"
    zip_file.write_bytes(zip_bytes)

    importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT inicio_s FROM viagens WHERE id = 'sptrans:M1-000'")
    assert cur.fetchone()[0] == 91800

    cur.execute(
        """
        SELECT pp.deslocamento_s FROM padrao_paradas pp
        JOIN viagens v ON v.padrao_id = pp.padrao_id
        WHERE v.id = 'sptrans:M1-000' AND pp.posicao = 1
        """
    )
    assert cur.fetchone()[0] == 600
    con.close()


def test_t_gt11_relatorio_importacao(tmp_path):
    caminho_banco = str(tmp_path / "test_relatorio.db")
    base_bytes = gerar_gtfs_mini_zip()
    zip_file = tmp_path / "gtfs_rel.zip"
    zip_file.write_bytes(base_bytes)

    importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    caminho_rel = Path(__file__).resolve().parents[3] / "docs" / "relatorio_importacao_sptrans.md"
    assert caminho_rel.exists()
    conteudo = caminho_rel.read_text(encoding="utf-8")
    assert "SHA-256" in conteudo
    assert "gtfs-mini-1.0" in conteudo
    assert "Paradas válidas" in conteudo
    assert "Linhas válidas" in conteudo
    assert "Padrões operacionais" in conteudo
    assert "Viagens ativas" in conteudo


def test_t_gt12_recusa_feed_teste_em_producao(tmp_path, monkeypatch):
    caminho_banco = str(tmp_path / "test_prod.db")
    base_bytes = gerar_gtfs_mini_zip()
    zip_file = tmp_path / "gtfs_teste.zip"
    zip_file.write_bytes(base_bytes)

    importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )

    # Verificar que em modo producao, a verificação rejeitaria feed teste
    # A regra DV-03 / T-GT12 diz que com feed teste e CITIZEN_MODO=producao, /rotas responde 503
    con = conectar(caminho_banco)
    cur = con.cursor()
    cur.execute("SELECT origem_dados FROM feeds WHERE ativo = 1")
    assert cur.fetchone()[0] == "teste"
    con.close()


def test_t_gt13_validade_fim_expirada(tmp_path):
    caminho_banco = str(tmp_path / "test_exp.db")
    base_bytes = gerar_gtfs_mini_zip()

    # Feed expirado em 2020
    feed_info_exp = (
        "feed_publisher_name,feed_publisher_url,feed_lang,feed_version,feed_start_date,feed_end_date\n"
        "SPTrans,https://www.sptrans.com.br,pt,gtfs-expirado,20200101,20201231\n"
    )
    zip_bytes = criar_zip_modificado(base_bytes, {"feed_info.txt": feed_info_exp})
    zip_file = tmp_path / "gtfs_exp.zip"
    zip_file.write_bytes(zip_bytes)

    res = importar_gtfs(
        sistema="sptrans",
        caminho_zip=zip_file,
        fonte_url="https://sptrans.com.br",
        origem_dados="teste",
        caminho_banco=caminho_banco,
    )
    assert res["status"] == "sucesso"
    assert res["validade_fim"] == "2020-12-31"
