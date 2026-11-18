"""T-A09 a T-A13: previsão, fallback, tema/aviso e confiança."""
import pytest

from src.assistente.config import LIMIAR_CONFIANCA, TEXTO_AVISO_TARIFAS, TEXTO_FALLBACK
from src.assistente.previsao import ordenar_intencoes, prever


def test_t_a09_cada_pergunta_canonica_preve_a_propria_intencao(modelo):
    for id_, intencao in modelo.intencoes.items():
        assert ordenar_intencoes(modelo, intencao["pergunta_canonica"])[0][0] == id_


def test_t_a10_pergunta_sem_sentido_cai_no_fallback_com_tres_sugestoes(modelo):
    r = prever("xqzv plkm wrtyu", modelo)
    assert r.intencao_id is None and r.tema is None and r.aviso is None
    assert r.resposta == TEXTO_FALLBACK
    esperadas = [modelo.intencoes[i]["pergunta_canonica"] for i, _ in ordenar_intencoes(modelo, "xqzv plkm wrtyu")[:3]]
    assert r.sugestoes == esperadas and len(r.sugestoes) == 3
    probs = [p for _, p in ordenar_intencoes(modelo, "xqzv plkm wrtyu")]
    assert probs == sorted(probs, reverse=True)


@pytest.mark.parametrize("pergunta", ["", "   ", "ab", "x" * 301])
def test_t_a11_pergunta_invalida_levanta_valueerror_sem_vazar_texto(modelo, pergunta):
    with pytest.raises(ValueError) as erro:
        prever(pergunta, modelo)
    assert str(erro.value) == "Pergunta inválida."
    assert "xxx" not in str(erro.value)


def test_t_a12_tema_correto_e_aviso_somente_em_tarifas(modelo):
    for id_, tema, com_aviso in (("R01", "rota", False), ("T01", "tarifas", True), ("H01", "historico_privacidade", False)):
        r = prever(modelo.intencoes[id_]["pergunta_canonica"], modelo)
        assert r.intencao_id == id_ and r.tema == tema
        assert r.aviso == (TEXTO_AVISO_TARIFAS if com_aviso else None)
        assert r.sugestoes == []
        assert r.resposta == modelo.intencoes[id_]["resposta"]


def test_t_a13_confianca_valida_e_respeita_o_limiar(modelo, dados):
    perguntas = [t["pergunta"] for t in dados[1]] + ["xqzv plkm wrtyu"]
    for pergunta in perguntas:
        r = prever(pergunta, modelo)
        assert 0 <= r.confianca <= 1 and round(r.confianca, 4) == r.confianca
        if r.intencao_id is not None:
            assert r.confianca >= LIMIAR_CONFIANCA


def test_limiar_pode_ser_sobrescrito_apenas_por_parametro(modelo):
    pergunta = modelo.intencoes["R01"]["pergunta_canonica"]
    assert prever(pergunta, modelo, limiar=0.999).intencao_id is None
    assert prever(pergunta, modelo, limiar=0.0).intencao_id == "R01"


def test_para_dict_tem_os_seis_campos(modelo):
    d = prever("Como peço uma rota?", modelo).para_dict()
    assert set(d) == {"resposta", "intencao_id", "tema", "confianca", "sugestoes", "aviso"}
