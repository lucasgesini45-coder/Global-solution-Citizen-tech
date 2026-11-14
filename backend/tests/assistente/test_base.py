"""T-A01 a T-A06 e testes negativos da validação (V-01 a V-10, A-01 a A-06)."""
import re

import pytest

from backend.src.assistente import base as b
from backend.src.assistente.config import PALAVRAS_PROIBIDAS, RAIZ_REPOSITORIO, RESPOSTA_MAX_CARACTERES, TEXTO_AVISO_TARIFAS
from backend.src.assistente.preprocessamento import normalizar_para_comparacao


def test_t_a01_base_real_valida_e_completa(dados):
    base, testes = dados
    intencoes = base["intencoes"]
    assert len(intencoes) == 15
    assert [i["id"] for i in intencoes] == list(b.IDS_ESPERADOS)
    contagem = {}
    for i in intencoes:
        contagem[i["tema"]] = contagem.get(i["tema"], 0) + 1
        assert len(i["frases_treino"]) == 12
        assert i["pergunta_canonica"] == i["frases_treino"][0]
        assert i["revisada_pela_equipe"] is False
    assert contagem == {"rota": 5, "tarifas": 5, "historico_privacidade": 5}
    todas = [normalizar_para_comparacao(f) for i in intencoes for f in i["frases_treino"]]
    assert len(todas) == 180 and len(set(todas)) == 180
    b.validar_base(base, testes)  # não levanta


def test_t_a02_nenhuma_frase_de_treino_vaza_para_o_teste(dados):
    base, testes = dados
    teste = {normalizar_para_comparacao(t["pergunta"]) for t in testes}
    treino = {normalizar_para_comparacao(f) for i in base["intencoes"] for f in i["frases_treino"]}
    assert teste.isdisjoint(treino)


def test_t_a03_respostas_de_tarifas_sem_valor_monetario(dados):
    for i in dados[0]["intencoes"]:
        if i["tema"] == "tarifas":
            assert "R$" not in i["resposta"]
            assert TEXTO_AVISO_TARIFAS not in i["resposta"]


def test_t_a04_respostas_sem_palavra_proibida_e_dentro_dos_limites(dados):
    for i in dados[0]["intencoes"]:
        r = i["resposta"]
        for proibida in PALAVRAS_PROIBIDAS:
            assert not re.search(rf"\b{re.escape(proibida)}\b", r, flags=re.IGNORECASE), (i["id"], proibida)
        assert 1 <= b.contar_frases(r) <= 3
        assert len(r) <= RESPOSTA_MAX_CARACTERES


def test_t_a05_status_texto_e_fontes_existentes(dados):
    for i in dados[0]["intencoes"]:
        r = i["resposta"]
        if i["status_funcionalidade"] == "planejada":
            assert r.startswith("Ainda não está disponível nesta versão:")
        if i["status_funcionalidade"] == "parcial":
            assert "nesta versão" in r.lower()
        assert i["revisada_pela_equipe"] is False
        assert len(i["fontes_no_repositorio"]) >= 1
        for fonte in i["fontes_no_repositorio"]:
            assert (RAIZ_REPOSITORIO / fonte).exists(), fonte


def test_t_a06_normalizacao_ignora_acento_caixa_e_espacos():
    assert normalizar_para_comparacao("Como  PESQUISO endereço?") == normalizar_para_comparacao("como pesquiso endereco")


def test_pergunta_de_teste_tem_12_itens_e_cobre_4_por_tema(dados):
    _, testes = dados
    assert len(testes) == 12
    temas = [b.TEMAS_ESPERADOS[t["intencao_esperada"]] for t in testes]
    assert {t: temas.count(t) for t in set(temas)} == {"rota": 4, "tarifas": 4, "historico_privacidade": 4}
    assert {t["intencao_esperada"] for t in testes}.isdisjoint({"R02", "T05", "H05"})


# ----------------------- testes negativos: a validação precisa barrar bases erradas
def _quebrar(copia_dados, mutacao):
    base, testes = copia_dados
    mutacao(base, testes)
    with pytest.raises(ValueError) as erro:
        b.validar_base(base, testes)
    return str(erro.value)


def test_v01_barra_quantidade_errada_de_intencoes(copia_dados):
    assert "V-01" in _quebrar(copia_dados, lambda base, t: base["intencoes"].pop())


def test_v03_barra_numero_errado_de_frases(copia_dados):
    assert "V-03" in _quebrar(copia_dados, lambda base, t: base["intencoes"][0]["frases_treino"].pop())


def test_v04_barra_frase_com_menos_de_3_palavras(copia_dados):
    def m(base, t):
        base["intencoes"][0]["frases_treino"][5] = "Oi tudo"
    assert "V-04" in _quebrar(copia_dados, m)


def test_v05_barra_frase_duplicada_entre_intencoes(copia_dados):
    def m(base, t):
        base["intencoes"][1]["frases_treino"][3] = base["intencoes"][0]["frases_treino"][4].upper()
    assert "V-05" in _quebrar(copia_dados, m)


def test_v06_barra_canonica_diferente_da_primeira_frase(copia_dados):
    def m(base, t):
        base["intencoes"][0]["pergunta_canonica"] = "Outra pergunta qualquer aqui"
    assert "V-06" in _quebrar(copia_dados, m)


def test_v07_barra_vazamento_do_teste_para_o_treino(copia_dados):
    def m(base, t):
        base["intencoes"][2]["frases_treino"][7] = t[0]["pergunta"].lower()
    assert "V-07" in _quebrar(copia_dados, m)


def test_a02_barra_palavra_proibida(copia_dados):
    def m(base, t):
        base["intencoes"][0]["resposta"] = "Nesta versão, a rota é segura para você."
    assert "A-02" in _quebrar(copia_dados, m)


def test_a02_nao_confunde_seguranca_com_segura(copia_dados):
    base, testes = copia_dados
    base["intencoes"][0]["resposta"] = "Nesta versão, a segurança e a pontualidade não são tratadas aqui."
    b.validar_base(base, testes)   # não levanta


def test_a03_barra_valor_monetario_em_tarifas(copia_dados):
    def m(base, t):
        base["intencoes"][5]["resposta"] = "Nesta versão, o custo da viagem é R$ 5,00 por trecho."
    assert "A-03" in _quebrar(copia_dados, m)


def test_v09_barra_planejada_sem_prefixo(copia_dados):
    def m(base, t):
        base["intencoes"][1]["resposta"] = "Esta função está prevista."
    assert "V-09" in _quebrar(copia_dados, m)


def test_v09_barra_parcial_sem_expressao(copia_dados):
    def m(base, t):
        base["intencoes"][0]["resposta"] = "Você informa origem e destino."
    assert "V-09" in _quebrar(copia_dados, m)


def test_v09_barra_fonte_inexistente(copia_dados):
    def m(base, t):
        base["intencoes"][0]["fontes_no_repositorio"] = ["arquivo/que/nao/existe.py"]
    assert "V-09" in _quebrar(copia_dados, m)


def test_v10_barra_revisada_nao_booleana(copia_dados):
    def m(base, t):
        base["intencoes"][0]["revisada_pela_equipe"] = "não"
    assert "V-10" in _quebrar(copia_dados, m)
