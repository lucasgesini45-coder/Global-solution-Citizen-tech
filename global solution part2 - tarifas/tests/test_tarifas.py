import copy
from datetime import date
import pytest

from src.tarifas import calcular_tarifa, carregar_regras

DATA_PADRAO = date(2026, 11, 9)


@pytest.fixture(scope="module")
def regras_demo():
    return carregar_regras("data/tarifas_demo.json")


def test_t_t01_onibus(regras_demo):
    custo = calcular_tarifa([("onibus", 28800)], DATA_PADRAO, "padrao", regras_demo)
    assert custo.centavos == 500


def test_t_t02_metro(regras_demo):
    custo = calcular_tarifa([("metro", 28800)], DATA_PADRAO, "padrao", regras_demo)
    assert custo.centavos == 520


def test_t_t03_sem_embarque(regras_demo):
    custo = calcular_tarifa([], DATA_PADRAO, "padrao", regras_demo)
    assert custo.centavos == 0
    assert custo.confirmado is True


def test_t_t04_onibus_onibus(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 28800), ("onibus", 30000)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 500


def test_t_t05_onibus_metro(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 28800), ("metro", 30000)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 820


def test_t_t06_metro_onibus(regras_demo):
    custo = calcular_tarifa(
        [("metro", 28800), ("onibus", 30000)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 520


def test_t_t07_janela_expirada(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 0), ("onibus", 10801)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 1000


def test_t_t08_janela_limite(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 0), ("onibus", 10800)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 500


def test_t_t09_atravessa_meia_noite(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 84600), ("onibus", 88200)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 500


def test_t_t10_cinco_embarques(regras_demo):
    embarques = [("onibus", 28800 + i * 600) for i in range(5)]
    custo = calcular_tarifa(embarques, DATA_PADRAO, "padrao", regras_demo)
    assert custo.centavos == 1000


def test_t_t11_metro_metro_sem_regra(regras_demo):
    custo = calcular_tarifa(
        [("metro", 28800), ("metro", 30000)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos is None
    assert custo.confirmado is False
    assert any("metro>metro" in d for d in custo.detalhe)


def test_t_t12_modal_desconhecido(regras_demo):
    custo = calcular_tarifa([("balsa", 28800)], DATA_PADRAO, "padrao", regras_demo)
    assert custo.centavos is None


def test_t_t13_regra_nao_confirmada(regras_demo):
    regras_mod = copy.deepcopy(regras_demo)
    regras_mod[0]["confirmada"] = False
    custo = calcular_tarifa([("onibus", 28800)], DATA_PADRAO, "padrao", regras_mod)
    assert custo.centavos is None


def test_t_t14_data_sem_vigencia(regras_demo):
    data_antiga = date(2025, 12, 31)
    custo = calcular_tarifa([("onibus", 28800)], data_antiga, "padrao", regras_demo)
    assert custo.centavos is None


def test_t_t15_estudante_um_embarque(regras_demo):
    custo = calcular_tarifa([("onibus", 28800)], DATA_PADRAO, "estudante", regras_demo)
    assert custo.centavos == 250


def test_t_t16_estudante_integracao(regras_demo):
    custo = calcular_tarifa(
        [("onibus", 28800), ("metro", 30000)], DATA_PADRAO, "estudante", regras_demo
    )
    assert custo.centavos == 410


def test_t_t17_perfil_sem_regra(regras_demo):
    custo = calcular_tarifa([("onibus", 28800)], DATA_PADRAO, "idoso", regras_demo)
    assert custo.centavos is None


def test_t_t18_fora_de_ordem(regras_demo):
    custo = calcular_tarifa(
        [("metro", 30000), ("onibus", 28800)], DATA_PADRAO, "padrao", regras_demo
    )
    assert custo.centavos == 820
