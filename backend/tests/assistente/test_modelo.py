"""T-A07 e T-A08: reprodutibilidade e persistência do modelo."""
import json
import shutil

import numpy as np
import sklearn

from backend.src.assistente import treino
from backend.src.assistente.base import carregar_base
from backend.src.assistente.config import CAMINHO_BASE, resolver_caminho
from backend.src.assistente.modelo import carregar_ou_treinar
from backend.src.assistente.previsao import ordenar_intencoes


def test_t_a07_treino_e_reprodutivel(dados):
    base, testes = dados
    a, b = treino.treinar_a_partir_da_base(base), treino.treinar_a_partir_da_base(base)
    perguntas = [t["pergunta"] for t in testes]
    assert np.array_equal(a.predict_proba(perguntas), b.predict_proba(perguntas))
    assert [nome for nome, _ in a.steps] == ["tfidf", "clf"]


class Espiao:
    def __init__(self):
        self.chamadas = 0

    def __call__(self, dados_base):
        self.chamadas += 1
        return treino.treinar_a_partir_da_base(dados_base)


def test_t_a08_persistencia_quatro_comportamentos(tmp_path):
    caminho = tmp_path / "m.joblib"
    espiao = Espiao()

    # (a) sem arquivo: treina e salva
    m1 = carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao)
    assert m1.origem == "treinado" and espiao.chamadas == 1 and caminho.is_file()
    assert not list(tmp_path.glob("*.tmp"))            # escrita atômica não deixa temporários

    # (b) segunda inicialização: carrega sem treinar
    m2 = carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao)
    assert m2.origem == "carregado" and espiao.chamadas == 1

    # (c) base alterada: re-treina e sobrescreve
    base_copia = tmp_path / "base.json"
    shutil.copy(resolver_caminho(CAMINHO_BASE), base_copia)
    dados = json.loads(base_copia.read_text(encoding="utf-8"))
    dados["intencoes"][0]["frases_treino"][11] = "Quero entender como pedir um trajeto passo a passo"
    base_copia.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    m3 = carregar_ou_treinar(caminho_modelo=caminho, caminho_base=base_copia, funcao_treino=espiao)
    assert m3.origem == "treinado" and espiao.chamadas == 2
    m3b = carregar_ou_treinar(caminho_modelo=caminho, caminho_base=base_copia, funcao_treino=espiao)
    assert m3b.origem == "carregado" and espiao.chamadas == 2

    # (d) arquivo corrompido: re-treina
    caminho.write_bytes(b"isto nao e um joblib")
    m4 = carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao)
    assert m4.origem == "treinado" and espiao.chamadas == 3
    assert carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao).origem == "carregado"


def test_versao_diferente_do_scikit_learn_forca_retreino(tmp_path, monkeypatch):
    caminho = tmp_path / "m.joblib"
    espiao = Espiao()
    carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao)
    monkeypatch.setattr(sklearn, "__version__", "0.0.1")
    assert carregar_ou_treinar(caminho_modelo=caminho, funcao_treino=espiao).origem == "treinado"
    assert espiao.chamadas == 2


def test_modelo_carregado_preve_igual_ao_treinado(tmp_path, dados):
    caminho = tmp_path / "m.joblib"
    treinado = carregar_ou_treinar(caminho_modelo=caminho)
    carregado = carregar_ou_treinar(caminho_modelo=caminho)
    for t in dados[1]:
        assert ordenar_intencoes(treinado, t["pergunta"]) == ordenar_intencoes(carregado, t["pergunta"])
