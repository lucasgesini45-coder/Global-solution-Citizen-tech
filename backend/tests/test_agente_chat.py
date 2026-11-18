"""Integração chat -> classificador -> roteamento real, sem afirmações inventadas."""
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.src.api import app
from backend.src.agente_api import pede_trajeto

client = TestClient(app)


def test_detecta_pedido_de_viagem_mas_nao_duvida_de_uso():
    assert pede_trajeto("Qual metrô pegar para chegar na Paulista?")
    assert pede_trajeto("Como chegar à Avenida Paulista?")
    assert not pede_trajeto("Como peço uma rota no app?")
    assert not pede_trajeto("Como funciona o cartão de transporte?")


def test_chat_pede_pontos_antes_de_consultar_rota():
    r = client.post("/agente/conversar", json={"pergunta": "Como chegar à Paulista?"})
    assert r.status_code == 200
    assert r.json()["rota"] is None
    assert r.json()["origem_resposta"] == "orientacao_do_app"


def test_chat_rota_respeita_metro_e_retorna_geometria():
    rota = {
        "tipo": "rota_real", "fonte": "Transitous", "tempo_min": 29,
        "trechos": [{"modal": "SUBWAY", "linha": "Linha 2 – Verde",
                    "de": "Paraíso", "para": "Consolação",
                    "trajeto": [[-23.55,-46.63],[-23.56,-46.64]]}],
        "trajeto": [[-23.55,-46.63],[-23.56,-46.64]],
        "aviso": "Tempo sujeito a mudanças",
    }
    payload = {
        "pergunta": "Qual metrô pegar para a Paulista?",
        "origem": {"lat": -23.55, "lon": -46.63},
        "destino": {"lat": -23.56, "lon": -46.64},
        "modal": "todos",
        "priorizar_menos_caminhada": True,
    }
    with patch("backend.src.agente_api.rota_real", return_value=rota) as motor:
        r = client.post("/agente/conversar", json=payload)
    assert r.status_code == 200
    assert r.json()["origem_resposta"] == "motor_rotas"
    assert r.json()["rota"]["trechos"][0]["linha"] == "Linha 2 – Verde"
    assert motor.call_args.args[0].modal == "ferroviario"
    assert motor.call_args.args[0].priorizar_menos_caminhada


def test_sem_informacao_verificada_nao_inventa_direitos():
    with patch("backend.src.agente_api.carregar", return_value=[]), patch(
        "backend.src.agente_api.responder",
        return_value={"status": "sem_resposta", "fontes": []}
    ), patch("backend.src.agente_api.preparar_modelo") as modelo:
        r = client.post("/agente/conversar",
                        json={"pergunta": "Quem tem direito à gratuidade?"})
    assert r.status_code == 200
    assert not r.json()["fontes"]
    assert r.json()["origem_resposta"] == "sem_resposta_verificada"
    modelo.assert_not_called()


def test_resposta_verificada_mantem_referencia():
    with patch("backend.src.agente_api.carregar", return_value=[]), patch(
        "backend.src.agente_api.responder",
        return_value={"status": "ok", "resposta": "Resposta revisada.",
                      "fontes": [{"referencia": "Fonte oficial",
                                  "data_verificacao": "2026-11-15"}]}
    ):
        r = client.post("/agente/conversar",
                        json={"pergunta": "Como solicitar cartão?"})
    assert r.status_code == 200
    assert r.json()["origem_resposta"] == "base_verificada"
    assert r.json()["fontes"][0]["referencia"] == "Fonte oficial"


def test_modelo_indisponivel_nao_interrompe_chat():
    with patch("backend.src.agente_api.carregar", return_value=[]), patch(
        "backend.src.agente_api.responder",
        return_value={"status": "sem_resposta", "fontes": []}
    ), patch("backend.src.agente_api.preparar_modelo", return_value=None):
        r = client.post("/agente/conversar",
                        json={"pergunta": "Como usar o aplicativo?"})
    assert r.status_code == 200
    assert r.json()["origem_resposta"] == "indisponivel"


def test_entrada_grande_ou_modal_invalido_retorna_422():
    assert client.post("/agente/conversar", json={"pergunta": "a"*301}).status_code == 422
    assert client.post("/agente/conversar",
                       json={"pergunta": "Como usar?", "modal":"invalido"}).status_code == 422
