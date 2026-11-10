from datetime import datetime
import pytest

from src.contratos import Parada, Perfil, Rede, Restricoes, Viagem, fmt_hora
from src.rede_demo import criar_rede_demo, ponto
from src.rotas import Navegador, buscar_rotas

O = ponto(0.0, -100.0)
D1 = ponto(4000.0, 300.0)
D3 = ponto(2000.0, 2100.0)
PARTIDA_PADRAO = datetime(2026, 11, 9, 8, 0, 0)


@pytest.fixture(scope="module")
def rede_demo():
    return criar_rede_demo()


@pytest.fixture(scope="module")
def nav_demo(rede_demo):
    return Navegador(rede_demo)


def test_t_r01_o_para_d1_linhas(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil())
    assert len(rotas) == 3
    conjunto_linhas = {r.linhas for r in rotas}
    assert conjunto_linhas == {("M1",), ("L100",), ("L200",)}


def test_t_r02_rota_m1(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil())
    r_m1 = next(r for r in rotas if r.linhas == ("M1",))
    assert r_m1.tempo_total_s == 1450
    assert r_m1.espera_s == 517
    assert r_m1.caminhada_m == 400
    assert r_m1.baldeacoes == 0
    assert fmt_hora(r_m1.chegada_s) == "08:24"


def test_t_r03_rota_l100(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil())
    r_l100 = next(r for r in rotas if r.linhas == ("L100",))
    assert r_l100.tempo_total_s == 1967
    assert r_l100.espera_s == 133
    assert r_l100.caminhada_m == 400


def test_t_r04_rota_l200(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil())
    r_l200 = next(r for r in rotas if r.linhas == ("L200",))
    assert r_l200.tempo_total_s == 2200
    assert r_l200.espera_s == 233
    assert r_l200.caminhada_m == 200


def test_t_r05_componentes_somam(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil())
    for r in rotas:
        assert r.componentes_somam() is True


def test_t_r06_o_para_d3(nav_demo):
    rotas = buscar_rotas(nav_demo, O, D3, PARTIDA_PADRAO, Perfil())
    assert len(rotas) == 1
    r = rotas[0]
    assert r.linhas == ("M1", "L300")
    assert r.tempo_total_s == 2243
    assert r.espera_s == 794
    assert r.caminhada_m == 300
    assert r.baldeacoes == 1


def test_t_r07_o_para_d3_sem_baldeacao(nav_demo):
    rotas = buscar_rotas(
        nav_demo, O, D3, PARTIDA_PADRAO, Perfil(baldeacoes_max=0)
    )
    assert rotas == []


def test_t_r08_caminhada_150(nav_demo):
    rotas = buscar_rotas(
        nav_demo, O, D1, PARTIDA_PADRAO, Perfil(caminhada_max_m=150)
    )
    assert rotas == []


def test_t_r09_caminhada_250(nav_demo):
    rotas = buscar_rotas(
        nav_demo, O, D1, PARTIDA_PADRAO, Perfil(caminhada_max_m=250)
    )
    assert len(rotas) > 0
    for r in rotas:
        for t in r.trechos:
            if t.tipo == "caminhada":
                assert t.distancia_m <= 250


def test_t_r10_linhas_bloqueadas(nav_demo):
    restr = Restricoes(linhas_bloqueadas=frozenset({"M1"}))
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil(), restricoes=restr)
    conjunto_linhas = {r.linhas for r in rotas}
    assert conjunto_linhas == {("L100",), ("L200",)}


def test_t_r11_paradas_bloqueadas_ma(nav_demo):
    restr = Restricoes(paradas_bloqueadas=frozenset({"MA"}))
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil(), restricoes=restr)
    for r in rotas:
        assert "M1" not in r.linhas


def test_t_r12_paradas_bloqueadas_ma_ba(nav_demo):
    restr = Restricoes(paradas_bloqueadas=frozenset({"MA", "BA"}))
    rotas = buscar_rotas(nav_demo, O, D1, PARTIDA_PADRAO, Perfil(), restricoes=restr)
    assert rotas == []


def test_t_r13_sabado(nav_demo):
    partida_sab = datetime(2026, 11, 7, 8, 0, 0)
    rotas = buscar_rotas(nav_demo, O, D1, partida_sab, Perfil())
    linhas_encontradas = {r.linhas for r in rotas}
    assert ("L100",) not in linhas_encontradas
    assert ("M1",) in linhas_encontradas


def test_t_r14_excecao(nav_demo):
    partida_exc = datetime(2026, 11, 20, 8, 0, 0)
    rotas = buscar_rotas(nav_demo, O, D1, partida_exc, Perfil())
    linhas_encontradas = {r.linhas for r in rotas}
    assert ("L100",) not in linhas_encontradas


def test_t_r15_quase_meia_noite(nav_demo):
    partida_noite = datetime(2026, 11, 9, 23, 50, 0)
    rotas = buscar_rotas(nav_demo, O, D1, partida_noite, Perfil())
    assert len(rotas) == 1
    assert rotas[0].linhas == ("M1",)
    assert fmt_hora(rotas[0].chegada_s) == "00:14 (+1d)"


def test_t_r16_madrugada(nav_demo):
    partida_madrugada = datetime(2026, 11, 10, 0, 20, 0)
    rotas = buscar_rotas(nav_demo, O, D1, partida_madrugada, Perfil())
    assert len(rotas) == 1
    assert rotas[0].linhas == ("M1",)
    assert rotas[0].tempo_total_s == 1450


def test_t_r17_madrugada_sem_servico(nav_demo):
    partida_tarde = datetime(2026, 11, 10, 0, 40, 0)
    rotas = buscar_rotas(nav_demo, O, D1, partida_tarde, Perfil())
    assert rotas == []


def test_t_r18_rota_so_a_pe(nav_demo):
    destino_pe = ponto(0.0, 600.0)
    rotas = buscar_rotas(nav_demo, O, destino_pe, PARTIDA_PADRAO, Perfil())
    rotas_a_pe = [r for r in rotas if len(r.transportes) == 0]
    assert len(rotas_a_pe) == 1
    assert rotas_a_pe[0].caminhada_m == 700
    assert rotas_a_pe[0].tempo_total_s == 583


def test_t_r19_rede_mini():
    s1_coord = ponto(0.0, 0.0)
    s2_coord = ponto(1000.0, 0.0)
    s3_coord = ponto(2000.0, 0.0)

    paradas = {
        "S1": Parada(id="S1", nome="S1", lat=s1_coord[0], lon=s1_coord[1]),
        "S2": Parada(id="S2", nome="S2", lat=s2_coord[0], lon=s2_coord[1]),
        "S3": Parada(id="S3", nome="S3", lat=s3_coord[0], lon=s3_coord[1]),
    }

    viagens = [
        Viagem(
            id="A-0",
            linha_id="A",
            nome_linha="Linha A",
            operador="Op",
            modal="onibus",
            sentido="ida",
            paradas=("S1", "S2"),
            horarios=(28900, 29500),
        ),
        Viagem(
            id="B-0",
            linha_id="B",
            nome_linha="Linha B",
            operador="Op",
            modal="onibus",
            sentido="ida",
            paradas=("S2", "S3"),
            horarios=(29530, 30130),
        ),
        Viagem(
            id="B-1",
            linha_id="B",
            nome_linha="Linha B",
            operador="Op",
            modal="onibus",
            sentido="ida",
            paradas=("S2", "S3"),
            horarios=(30130, 30730),
        ),
    ]

    rede_mini = Rede(paradas=paradas, viagens=viagens)
    nav_mini = Navegador(rede_mini)

    rotas = buscar_rotas(
        nav_mini,
        s1_coord,
        s3_coord,
        PARTIDA_PADRAO,
        Perfil(caminhada_max_m=100),
    )
    assert len(rotas) == 1
    r = rotas[0]
    assert r.linhas == ("A", "B")
    assert r.tempo_total_s == 1930
    assert r.componentes_somam() is True
    assert r.transportes[1].viagem_id == "B-1"
