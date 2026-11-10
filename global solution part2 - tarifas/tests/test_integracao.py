import copy
import json
import re
import pytest

from src.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_VERIFICADA,
    SEG_SUFICIENTE,
)
from src.rede_demo import criar_rede_demo, ponto
from src.recomendar import processar_pedido
from src.tarifas import carregar_regras

O = ponto(0.0, -100.0)
D1 = ponto(4000.0, 300.0)
D3 = ponto(2000.0, 2100.0)
PARTIDA_ISO = "2026-11-09T08:00:00"

PALAVRAS_PROIBIDAS = re.compile(
    r"\b(segura|seguro|garantida|garantido|pontual|sem risco)\b", re.IGNORECASE
)


@pytest.fixture(scope="module")
def rede_demo():
    return criar_rede_demo()


@pytest.fixture(scope="module")
def regras_demo():
    return carregar_regras("data/tarifas_demo.json")


def test_t_i01_o_para_d1_sucesso(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert resp["erro"] is None
    assert resp["n_rotas"] == 3
    ordens = [r["ordem"] for r in resp["rotas"]]
    assert ordens == [1, 2, 3]

    r1 = resp["rotas"][0]
    assert r1["custo"]["centavos"] == 520
    assert r1["tempo_total_min"] == 24
    assert r1["fontes"][0]["rotulo"] == "planejado"
    assert r1["fontes"][0]["origem_dados"] == "simulado"


def test_t_i02_aviso_seguranca(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert "segurança insuficientes" in resp["aviso"]
    for r in resp["rotas"]:
        assert r["seguranca"] == {"status": "indisponivel", "exposicao": None}
    assert resp["criterios_usados"] == ["tempo", "custo"]


def test_t_i03_gancho_exposicao_valido(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    avaliar_exp = lambda rota: (0.2, SEG_SUFICIENTE)
    resp = processar_pedido(
        pedido, rede_demo, regras_demo, avaliar_exposicao=avaliar_exp
    )
    assert resp["criterios_usados"] == ["tempo", "custo", "exposicao"]
    assert resp["aviso"] is None


def test_t_i04_gancho_exposicao_invalido(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    avaliar_exp = lambda rota: (7.5, SEG_SUFICIENTE)
    resp = processar_pedido(
        pedido, rede_demo, regras_demo, avaliar_exposicao=avaliar_exp
    )
    assert "exposicao" not in resp["criterios_usados"]


def test_t_i05_orcamento_max_510(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
        "necessidades": {"orcamento_max_centavos": 510},
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    custos = [r["custo"]["centavos"] for r in resp["rotas"]]
    assert custos == [500, 500]
    assert resp["descartes"] == {"orcamento_excedido": 1}


def test_t_i06_origem_fora_da_area(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": -22.9, "lon": -43.2},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert resp["rotas"] == []
    assert resp["erro"]["codigo"] == "origem_fora_da_area_piloto"


def test_t_i07_erros_validacao_pedido(rede_demo, regras_demo):
    # Pedido vazio
    resp1 = processar_pedido({}, rede_demo, regras_demo)
    assert resp1["erro"]["codigo"] == "origem_invalida"

    # Partida textual não-ISO
    resp2 = processar_pedido(
        {
            "origem": {"lat": O[0], "lon": O[1]},
            "destino": {"lat": D1[0], "lon": D1[1]},
            "partida": "ontem de manhã",
        },
        rede_demo,
        regras_demo,
    )
    assert resp2["erro"]["codigo"] == "partida_invalida"

    # Preferências inválidas
    resp3 = processar_pedido(
        {
            "origem": {"lat": O[0], "lon": O[1]},
            "destino": {"lat": D1[0], "lon": D1[1]},
            "partida": PARTIDA_ISO,
            "necessidades": {"caminhada_max_m": 99999},
        },
        rede_demo,
        regras_demo,
    )
    assert resp3["erro"]["codigo"] == "preferencias_invalidas"


def test_t_i08_madrugada_sem_trajeto(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": "2026-11-10T00:40:00",
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert resp["rotas"] == []
    assert resp["erro"]["codigo"] == "sem_trajeto"


def test_t_i09_acessibilidade_gancho_padrao(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
        "necessidades": {"acessibilidade": ["sem_degraus"]},
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert resp["n_rotas"] == 3
    for r in resp["rotas"]:
        assert r["acessibilidade"] == ACESS_NAO_VERIFICADA
        assert any("NÃO verificada" in m for m in r["motivos"])


def test_t_i10_acessibilidade_filtro_m1(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
        "necessidades": {"acessibilidade": ["sem_degraus"]},
    }

    def gancho(rota, nec):
        if "M1" in rota.linhas:
            return ACESS_INCOMPATIVEL
        return ACESS_COMPATIVEL

    resp = processar_pedido(pedido, rede_demo, regras_demo, verificar_acessibilidade=gancho)
    assert resp["n_rotas"] == 2
    for r in resp["rotas"]:
        assert r["acessibilidade"] == ACESS_COMPATIVEL
    assert resp["descartes"] == {"acessibilidade_incompativel": 1}


def test_t_i11_acessibilidade_resposta_desconhecida(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
        "necessidades": {"acessibilidade": ["sem_degraus"]},
    }
    gancho = lambda rota, nec: "TALVEZ"
    resp = processar_pedido(pedido, rede_demo, regras_demo, verificar_acessibilidade=gancho)
    for r in resp["rotas"]:
        assert r["acessibilidade"] == ACESS_NAO_VERIFICADA


def test_t_i12_acessibilidade_todas_incompativeis(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
        "necessidades": {"acessibilidade": ["sem_degraus"]},
    }
    gancho = lambda rota, nec: ACESS_INCOMPATIVEL
    resp = processar_pedido(pedido, rede_demo, regras_demo, verificar_acessibilidade=gancho)
    assert resp["rotas"] == []
    assert resp["erro"]["codigo"] == "nenhuma_rota_atende"


def test_t_i13_o_para_d3_integracao(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D3[0], "lon": D3[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    assert resp["n_rotas"] == 1
    r = resp["rotas"][0]
    assert r["baldeacoes"] == 1
    assert r["custo"]["centavos"] == 520


def test_t_i14_o_para_d3_sem_regra_metro_onibus(rede_demo, regras_demo):
    regras_sem_chave = copy.deepcopy(regras_demo)
    regras_sem_chave[0]["integracao_adicional"].pop("metro>onibus", None)
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D3[0], "lon": D3[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_sem_chave)
    assert resp["n_rotas"] == 1
    r = resp["rotas"][0]
    assert r["custo"]["centavos"] is None
    assert r["custo"]["confirmado"] is False
    assert any("Tarifa não confirmada" in m for m in r["motivos"])
    assert "tarifa não confirmada" in resp["aviso"].lower()


def test_t_i15_json_dumps(rede_demo, regras_demo):
    pedido = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    resp = processar_pedido(pedido, rede_demo, regras_demo)
    serializado = json.dumps(resp)
    assert isinstance(serializado, str)


def test_t_i16_fuso_horario(rede_demo, regras_demo):
    pedido_utc = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": "2026-11-09T11:00:00+00:00",
    }
    pedido_local = {
        "origem": {"lat": O[0], "lon": O[1]},
        "destino": {"lat": D1[0], "lon": D1[1]},
        "partida": PARTIDA_ISO,
    }
    resp_utc = processar_pedido(pedido_utc, rede_demo, regras_demo)
    resp_local = processar_pedido(pedido_local, rede_demo, regras_demo)
    assert resp_utc["n_rotas"] == resp_local["n_rotas"]
    assert resp_utc["rotas"][0]["saida"] == resp_local["rotas"][0]["saida"]


def test_t_i17_nenhuma_palavra_proibida(rede_demo, regras_demo):
    cenarios = [
        {"origem": {"lat": O[0], "lon": O[1]}, "destino": {"lat": D1[0], "lon": D1[1]}, "partida": PARTIDA_ISO},
        {"origem": {"lat": O[0], "lon": O[1]}, "destino": {"lat": D3[0], "lon": D3[1]}, "partida": PARTIDA_ISO},
        {
            "origem": {"lat": O[0], "lon": O[1]},
            "destino": {"lat": D1[0], "lon": D1[1]},
            "partida": PARTIDA_ISO,
            "necessidades": {"acessibilidade": ["sem_degraus"]},
        },
    ]
    for pedido in cenarios:
        resp = processar_pedido(pedido, rede_demo, regras_demo)
        if resp.get("aviso"):
            assert not PALAVRAS_PROIBIDAS.search(resp["aviso"])
        for r in resp.get("rotas", []):
            for m in r.get("motivos", []):
                assert not PALAVRAS_PROIBIDAS.search(m)
