from unittest.mock import patch, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from backend.src.api import app
from backend.src import historico_ia as h

client = TestClient(app)
RESULTADO = {"resposta": "Consulte a tarifa no portal oficial.", "origem_resposta": "documento_oficial", "tema_contexto": "tarifas"}

def test_sem_consentimento_nunca_conecta():
    with patch.object(h, "conectar") as conectar:
        assert h.registrar("Qual a tarifa?", RESULTADO) == {"status": "desativado"}
        conectar.assert_not_called()

def test_sem_banco_nao_interrompe_chat(monkeypatch):
    monkeypatch.delenv("CHAT_HISTORY_DATABASE_URL", raising=False)
    r = client.post("/agente/conversar", json={"pergunta": "Oi", "consentimento_historico": True})
    assert r.status_code == 200
    assert r.json()["historico"]["status"] == "indisponivel"
    assert "Olá" in r.json()["resposta"]

def test_coleta_com_consentimento(monkeypatch):
    monkeypatch.setenv("CHAT_HISTORY_DATABASE_URL", "postgresql://teste")
    conexao = MagicMock()
    cursor = conexao.__enter__.return_value.cursor.return_value.__enter__.return_value
    sessao = uuid4()
    with patch.object(h, "conectar", return_value=conexao):
        r = h.registrar("Qual a tarifa?", RESULTADO, True, sessao)
    assert r["status"] == "salvo"
    assert r["sessao"] == str(sessao)
    assert not r["texto_omitido"]
    sql, parametros = cursor.execute.call_args.args
    assert "INSERT INTO" in sql
    assert parametros[1] == sessao
    assert parametros[2] == "Qual a tarifa?"

def test_dados_pessoais_e_rotas_nao_salvam_texto():
    for p in ["Meu CPF é 123.456.789-00", "Meu e-mail é teste@example.com", "Sou cadeirante", "Como chegar ao destino?"]:
        dados = h.dados_interacao(p, RESULTADO)
        assert dados[0:2] == (None, None)
        assert dados[-1]
    dados = h.dados_interacao("Qual linha?", {**RESULTADO, "rota": {"trajeto": [[-23.55, -46.63]]}})
    assert dados[0:2] == (None, None)

def test_falha_de_banco_nao_interrompe_chat(monkeypatch):
    monkeypatch.setenv("CHAT_HISTORY_DATABASE_URL", "postgresql://teste")
    with patch.object(h, "conectar", side_effect=RuntimeError):
        assert h.registrar("Qual a tarifa?", RESULTADO, True)["status"] == "indisponivel"

def test_admin_bloqueado_sem_token(monkeypatch):
    monkeypatch.setenv("CHAT_HISTORY_ADMIN_TOKEN", "a" * 40)
    assert client.get("/agente/historico/admin").status_code == 401
    assert client.get("/agente/historico/admin", headers={"Authorization": "Bearer errado"}).status_code == 401

def test_exclusao_por_sessao(monkeypatch):
    monkeypatch.setenv("CHAT_HISTORY_DATABASE_URL", "postgresql://teste")
    conexao = MagicMock()
    cursor = conexao.__enter__.return_value.cursor.return_value.__enter__.return_value
    sessao = uuid4()
    with patch.object(h, "conectar", return_value=conexao):
        r = client.post("/agente/historico/apagar", json={"sessao": str(sessao)})
    assert r.json()["status"] == "apagado"
    sql, parametros = cursor.execute.call_args.args
    assert "WHERE sessao = %s" in sql
    assert parametros == (sessao,)
