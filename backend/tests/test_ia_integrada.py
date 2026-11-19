"""Regressões da integração entre o classificador e o agente cidadão."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.src.api import app
from backend.src.assistente.previsao import Previsao

client = TestClient(app)


def test_privacidade_do_app_preserva_tema_do_classificador():
    previsao = Previsao("Orientação de privacidade.", "H05", "historico_privacidade", 0.9)
    with patch("backend.src.agente_api.preparar_modelo", return_value=object()), patch(
        "backend.src.agente_api.prever", return_value=previsao
    ):
        resposta = client.post("/agente/conversar", json={"pergunta": "O app guarda minhas perguntas?"}).json()
    assert resposta["origem_resposta"] == "classificador_academico"
    assert resposta["fontes"] == []


def test_gps_e_horarios_do_app():
    for pergunta, esperado in [
        ("Como desativar GPS no app?", "Desativar GPS"),
        ("Como ativar GPS no aplicativo?", "Ativar GPS"),
        ("Como funciona o assistente de viagem?", "Assistente de viagem"),
        ("Como vejo os horários de ônibus no aplicativo?", "Horários dos ônibus"),
    ]:
        r = client.post("/agente/conversar", json={"pergunta": pergunta})
        assert r.status_code == 200
        assert r.json()["origem_resposta"] == "orientacao_do_app"
        assert esperado in r.json()["resposta"]


def test_pergunta_externa_nao_dispara_classificador_de_app():
    with patch("backend.src.agente_api.preparar_modelo") as modelo:
        r = client.post("/agente/conversar", json={"pergunta": "Qual benefício de gratuidade em outro país posso pedir no app?"})
    assert r.status_code == 200
    modelo.assert_not_called()


def test_caminhada_solicitada_no_chat():
    with patch("backend.src.agente_api.rota_real", return_value={"trechos":[]}) as motor:
        r = client.post("/agente/conversar", json={
            "pergunta":"Como chegar a pé?", "origem":{"lat":-23.55,"lon":-46.63},
            "destino":{"lat":-23.56,"lon":-46.64}})
    assert r.status_code == 200
    assert motor.call_args.args[0].modal == "ape"
