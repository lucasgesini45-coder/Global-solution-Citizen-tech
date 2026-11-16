"""T-A14 a T-A16: API, privacidade e terminal."""
import logging
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.assistente import rotas_api
from backend.src.assistente.cli import executar_conversa
from backend.src.assistente.config import (RAIZ_REPOSITORIO, TEXTO_AVISO_TARIFAS, TEXTO_BOAS_VINDAS_TERMINAL,
                                   TEXTO_ENTRADA_INVALIDA_TERMINAL, TEXTO_FALLBACK)
from backend.src.assistente.modelo import carregar_ou_treinar


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    """API de teste com o modelo em pasta temporária e estado limpo."""
    monkeypatch.setattr(rotas_api, "carregar_ou_treinar",
                        lambda: carregar_ou_treinar(caminho_modelo=tmp_path / "m.joblib"))
    monkeypatch.setitem(rotas_api._estado, "tentou", False)
    monkeypatch.setitem(rotas_api._estado, "modelo", None)
    app = FastAPI()
    app.include_router(rotas_api.roteador)
    return TestClient(app)


def test_t_a14_perguntar_valido_devolve_seis_campos(cliente):
    r = cliente.post("/assistente/perguntar", json={"pergunta": "Onde vejo o custo da rota?"})
    assert r.status_code == 200
    corpo = r.json()
    assert set(corpo) == {"resposta", "intencao_id", "tema", "confianca", "sugestoes", "aviso"}
    assert corpo["intencao_id"] == "T01" and corpo["aviso"] == TEXTO_AVISO_TARIFAS


def test_t_a14_perguntas_invalidas_dao_422(cliente):
    assert cliente.post("/assistente/perguntar", json={"pergunta": ""}).status_code == 422
    assert cliente.post("/assistente/perguntar", json={"pergunta": "a" * 301}).status_code == 422
    assert cliente.post("/assistente/perguntar", json={"pergunta": "  ab  "}).status_code == 422
    assert cliente.post("/assistente/perguntar", json={}).status_code == 422


def test_t_a14_saude(cliente):
    r = cliente.get("/assistente/saude")
    assert r.status_code == 200
    assert r.json() == {"modelo_carregado": True, "n_intencoes": 15, "versao_base": "1.0"}


def test_t_a14_modelo_indisponivel_da_503_e_api_continua_de_pe(cliente, monkeypatch):
    def quebrar():
        raise RuntimeError("falha simulada")
    monkeypatch.setattr(rotas_api, "carregar_ou_treinar", quebrar)
    r = cliente.post("/assistente/perguntar", json={"pergunta": "Como peço uma rota?"})
    assert r.status_code == 503 and r.json()["detail"] == "Assistente indisponível."
    s = cliente.get("/assistente/saude")
    assert s.status_code == 200 and s.json()["modelo_carregado"] is False


def test_t_a14_rotas_aparecem_na_documentacao(cliente):
    caminhos = cliente.get("/openapi.json").json()["paths"]
    assert "/assistente/perguntar" in caminhos and "/assistente/saude" in caminhos


def _arquivos_do_backend():
    raiz = RAIZ_REPOSITORIO / "backend"
    return {p for p in raiz.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts}


def test_t_a15_nenhuma_pergunta_e_guardada_em_log_ou_arquivo(cliente, caplog):
    perguntas = ["Pergunta secreta numero um sobre rotas", "Segunda dúvida confidencial de tarifas",
                 "Terceira pergunta privada sobre histórico", "Quarta consulta reservada do usuário",
                 "Quinta pergunta pessoal sobre o aplicativo"]
    antes = _arquivos_do_backend()
    caplog.set_level(logging.DEBUG)
    for p in perguntas:
        assert cliente.post("/assistente/perguntar", json={"pergunta": p}).status_code == 200
    depois = _arquivos_do_backend()
    assert depois == antes, f"arquivos novos: {depois - antes}"
    for p in perguntas:
        assert p not in caplog.text and p.lower() not in caplog.text.lower()


def test_t_a15_pacote_nao_usa_banco_de_dados():
    pacote = Path(rotas_api.__file__).parent
    for arquivo in pacote.glob("*.py"):
        assert "sqlite3" not in arquivo.read_text(encoding="utf-8"), arquivo.name


def test_t_a16_terminal_conversa_completa(modelo):
    entradas = iter(["como peço uma rota?", "xqzv plkm", "ab", "Onde vejo o custo da rota?", "SAIR  ", "NUNCA_LIDA"])
    saidas = []
    executar_conversa(modelo, entrada=lambda _="": next(entradas), saida=saidas.append)
    assert saidas[0] == TEXTO_BOAS_VINDAS_TERMINAL
    assert TEXTO_FALLBACK in saidas
    i = saidas.index(TEXTO_FALLBACK)
    assert saidas[i + 1] == "Você quis dizer:"
    assert [s[:3] for s in saidas[i + 2:i + 5]] == ["1. ", "2. ", "3. "]
    assert TEXTO_ENTRADA_INVALIDA_TERMINAL in saidas
    j = saidas.index(modelo.intencoes["T01"]["resposta"])
    assert saidas[j + 1] == TEXTO_AVISO_TARIFAS                 # aviso em linha separada, logo abaixo
    assert next(entradas) == "NUNCA_LIDA"                        # encerrou ao receber "sair"


def test_t_a16_terminal_encerra_em_fim_de_entrada(modelo):
    def fim(_=""):
        raise EOFError
    saidas = []
    executar_conversa(modelo, entrada=fim, saida=saidas.append)
    assert saidas == [TEXTO_BOAS_VINDAS_TERMINAL]
