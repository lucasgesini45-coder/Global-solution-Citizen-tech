import datetime
import pytest

from src.historico import (
    apagar_historico,
    iniciar_banco,
    listar_historico,
    purgar_expirados,
    registrar_busca,
)


@pytest.fixture
def banco_teste(tmp_path):
    caminho = str(tmp_path / "teste_historico.sqlite")
    iniciar_banco(caminho)
    return caminho


def test_t_h01_idempotencia(banco_teste):
    # Executar iniciar_banco duas vezes
    iniciar_banco(banco_teste)
    iniciar_banco(banco_teste)


def test_t_h02_registrar_e_listar(banco_teste):
    pedido = {
        "origem": {"lat": -23.55, "lon": -46.63},
        "destino": {"lat": -23.56, "lon": -46.64},
        "partida": "2026-11-09T08:00:00",
    }
    resposta = {"n_rotas": 3, "rotas": [{}, {}, {}], "erro": None}

    id_inserido = registrar_busca(banco_teste, "sessao-1", pedido, resposta)
    assert id_inserido > 0

    itens = listar_historico(banco_teste, "sessao-1")
    assert len(itens) == 1
    item = itens[0]
    assert item["origem_lat"] == -23.55
    assert item["origem_lon"] == -46.63
    assert item["destino_lat"] == -23.56
    assert item["destino_lon"] == -46.64
    assert item["n_rotas"] == 3
    assert item["erro_codigo"] is None


def test_t_h03_duas_sessoes_apagar_uma(banco_teste):
    pedido = {
        "origem": {"lat": -23.55, "lon": -46.63},
        "destino": {"lat": -23.56, "lon": -46.64},
        "partida": "2026-11-09T08:00:00",
    }
    resp = {"n_rotas": 1, "rotas": [{}]}

    registrar_busca(banco_teste, "sessao-A", pedido, resp)
    registrar_busca(banco_teste, "sessao-A", pedido, resp)
    registrar_busca(banco_teste, "sessao-B", pedido, resp)

    removidos = apagar_historico(banco_teste, "sessao-A")
    assert removidos == 2

    assert len(listar_historico(banco_teste, "sessao-A")) == 0
    assert len(listar_historico(banco_teste, "sessao-B")) == 1


def test_t_h04_purgar_expirados(banco_teste):
    agora = datetime.datetime(2026, 11, 9, 12, 0, 0)
    data_91_dias = agora - datetime.timedelta(days=91)
    data_89_dias = agora - datetime.timedelta(days=89)

    pedido = {
        "origem": {"lat": -23.55, "lon": -46.63},
        "destino": {"lat": -23.56, "lon": -46.64},
        "partida": "2026-11-09T08:00:00",
    }
    resp = {"n_rotas": 1}

    registrar_busca(banco_teste, "s1", pedido, resp, agora=data_91_dias)
    registrar_busca(banco_teste, "s1", pedido, resp, agora=data_89_dias)

    removidos = purgar_expirados(banco_teste, agora=agora)
    assert removidos == 1

    restantes = listar_historico(banco_teste, "s1")
    assert len(restantes) == 1
    assert restantes[0]["criado_em"] == data_89_dias.isoformat()


def test_t_h05_sql_injection(banco_teste):
    sessao_maliciosa = "'; DROP TABLE historico_buscas; --"
    pedido = {
        "origem": {"lat": -23.55, "lon": -46.63},
        "destino": {"lat": -23.56, "lon": -46.64},
        "partida": "2026-11-09T08:00:00",
    }
    resp = {"n_rotas": 0, "erro": {"codigo": "sem_trajeto"}}

    id_ins = registrar_busca(banco_teste, sessao_maliciosa, pedido, resp)
    assert id_ins > 0

    itens = listar_historico(banco_teste, sessao_maliciosa)
    assert len(itens) == 1
    assert itens[0]["sessao_id"] == sessao_maliciosa
    assert itens[0]["erro_codigo"] == "sem_trajeto"
