import pytest

from src.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
    Custo,
    Perfil,
    Rota,
    Trecho,
)
from src.ranking import (
    criterios_usaveis,
    escore,
    montar_aviso,
    motivo_inviabilidade,
    selecionar,
)


def criar_rota_sintetica(
    tempo_min: float,
    custo_centavos: int | None = 500,
    linhas: tuple[str, ...] = ("L1",),
    caminhada_m: int = 200,
    exposicao: float | None = None,
    acessibilidade: str = ACESS_NAO_VERIFICADA,
) -> Rota:
    t_total_s = int(round(tempo_min * 60))
    trechos: list[Trecho] = []
    if linhas:
        for idx, l in enumerate(linhas):
            trechos.append(
                Trecho(
                    tipo="transporte",
                    inicio_s=idx * 600,
                    fim_s=(idx + 1) * 600,
                    de=f"Stop{idx}",
                    para=f"Stop{idx+1}",
                    linha_id=l,
                    nome_linha=f"Linha {l}",
                    parada_de=f"S{idx}",
                    parada_para=f"S{idx+1}",
                )
            )
    if caminhada_m > 0:
        trechos.append(
            Trecho(
                tipo="caminhada",
                inicio_s=0,
                fim_s=int(round(caminhada_m / 1.2)),
                de="Origem",
                para="Stop0",
                distancia_m=float(caminhada_m),
            )
        )
    return Rota(
        trechos=trechos,
        saida_s=0,
        chegada_s=t_total_s,
        custo=Custo(
            centavos=custo_centavos, confirmado=(custo_centavos is not None)
        ),
        exposicao=exposicao,
        acessibilidade=acessibilidade,
    )


def test_t_k01_criterios_usaveis_custo_none():
    r1 = criar_rota_sintetica(20, custo_centavos=500)
    r2 = criar_rota_sintetica(25, custo_centavos=None)
    assert criterios_usaveis([r1, r2]) == ["tempo"]


def test_t_k02_criterios_usaveis_exposicao():
    r1 = criar_rota_sintetica(20, custo_centavos=500, exposicao=0.2)
    r2 = criar_rota_sintetica(25, custo_centavos=520, exposicao=0.4)
    assert criterios_usaveis([r1, r2]) == ["tempo", "custo", "exposicao"]

    r2_sem_exp = criar_rota_sintetica(25, custo_centavos=520, exposicao=None)
    assert criterios_usaveis([r1, r2_sem_exp]) == ["tempo", "custo"]


def test_t_k03_escore_calculo():
    r = criar_rota_sintetica(30.0, custo_centavos=600)
    e = escore(r, ["tempo", "custo"])
    assert abs(e - 0.388889) < 1e-5


def test_t_k04_dominancia():
    # r1 domina r_pior em todas as dimensões
    r1 = criar_rota_sintetica(20, custo_centavos=500, caminhada_m=200, linhas=("L1",))
    r_pior = criar_rota_sintetica(30, custo_centavos=600, caminhada_m=400, linhas=("L2",))
    # r_barata é melhor em custo
    r_barata = criar_rota_sintetica(25, custo_centavos=300, caminhada_m=200, linhas=("L3",))

    escolhidas, _ = selecionar([r1, r_pior, r_barata], Perfil())
    assert r_pior not in escolhidas
    assert r1 in escolhidas
    assert r_barata in escolhidas


def test_t_k05_quatro_candidatas_nao_dominadas():
    r1 = criar_rota_sintetica(20, custo_centavos=500, caminhada_m=400, linhas=("L1",))
    r2 = criar_rota_sintetica(25, custo_centavos=400, caminhada_m=350, linhas=("L2",))
    r3 = criar_rota_sintetica(30, custo_centavos=300, caminhada_m=300, linhas=("L3",))
    r4 = criar_rota_sintetica(35, custo_centavos=200, caminhada_m=250, linhas=("L4",))

    escolhidas, usar = selecionar([r1, r2, r3, r4], Perfil())
    assert len(escolhidas) == 3
    # Ordenadas por escore crescente
    escores = [escore(r, usar) for r in escolhidas]
    assert escores == sorted(escores)


def test_t_k06_duas_candidatas_distintas():
    r1 = criar_rota_sintetica(20, custo_centavos=500, linhas=("L1",))
    r2 = criar_rota_sintetica(25, custo_centavos=400, linhas=("L2",))
    escolhidas, usar = selecionar([r1, r2], Perfil())
    assert len(escolhidas) == 2
    aviso = montar_aviso(escolhidas, usar)
    assert aviso is not None
    assert "Apenas 2" in aviso


def test_t_k07_rotas_similares():
    r1 = criar_rota_sintetica(20, linhas=("L1",))
    r2 = criar_rota_sintetica(25, linhas=("L1",))
    escolhidas, _ = selecionar([r1, r2], Perfil())
    assert len(escolhidas) == 1


def test_t_k08_aviso_sem_exposicao():
    r1 = criar_rota_sintetica(20, exposicao=None)
    r2 = criar_rota_sintetica(25, exposicao=None)
    r3 = criar_rota_sintetica(30, exposicao=None)
    escolhidas, usar = selecionar([r1, r2, r3], Perfil())
    aviso = montar_aviso(escolhidas, usar)
    assert aviso is not None
    assert "dados de segurança insuficientes" in aviso


def test_t_k09_motivos_inviabilidade():
    perfil = Perfil(
        caminhada_max_m=300,
        baldeacoes_max=0,
        orcamento_max_centavos=550,
    )

    r_caminhada = criar_rota_sintetica(20, caminhada_m=301)
    assert motivo_inviabilidade(r_caminhada, perfil) == "caminhada_acima_do_limite"

    r_baldeacao = criar_rota_sintetica(20, caminhada_m=200, linhas=("L1", "L2"))
    assert motivo_inviabilidade(r_baldeacao, perfil) == "baldeacoes_acima_do_limite"

    r_orcamento = criar_rota_sintetica(20, caminhada_m=200, custo_centavos=551, linhas=("L1",))
    assert motivo_inviabilidade(r_orcamento, perfil) == "orcamento_excedido"

    r_acess = criar_rota_sintetica(
        20, caminhada_m=200, custo_centavos=500, linhas=("L1",), acessibilidade=ACESS_INCOMPATIVEL
    )
    assert motivo_inviabilidade(r_acess, perfil) == "acessibilidade_incompativel"


def test_t_k10_tarifa_none_com_orcamento():
    perfil = Perfil(orcamento_max_centavos=100)
    r = criar_rota_sintetica(20, custo_centavos=None, caminhada_m=200, linhas=("L1",))
    assert motivo_inviabilidade(r, perfil) is None


def test_t_k11_acessibilidade_ordenacao():
    perfil = Perfil(acessibilidade=frozenset({"sem_degraus"}))
    r_rapida = criar_rota_sintetica(
        15, linhas=("L1",), acessibilidade=ACESS_NAO_VERIFICADA
    )
    r_lenta = criar_rota_sintetica(
        30, linhas=("L2",), acessibilidade=ACESS_COMPATIVEL
    )

    escolhidas, _ = selecionar([r_rapida, r_lenta], perfil)
    assert len(escolhidas) == 2
    assert escolhidas[0] is r_lenta
    assert escolhidas[1] is r_rapida
