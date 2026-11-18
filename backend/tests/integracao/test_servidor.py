"""Servidor local (app.py): montagem, contratos de rota, CORS e linha de comando."""
import pytest
from fastapi import FastAPI

import app as servidor
from backend.src.sessoes import router as router_sessoes


def test_health_responde_ok(cliente):
    assert cliente.get("/health").json() == {"status": "ok"}


def test_status_integracao_lista_os_cinco_modulos_e_esta_ok(cliente):
    corpo = cliente.get("/integracao/status").json()
    assert corpo["ok"] is True
    assert len(corpo["modulos"]) == 5
    assert all(m["ok"] for m in corpo["modulos"])
    assert corpo["modo"] == "teste"
    assert corpo["sessoes_ativas"] == 0
    assert "não é canal oficial" in corpo["aviso"]


def test_todos_os_endpoints_do_contrato_estao_no_openapi(cliente):
    esquema = cliente.get("/openapi.json").json()["paths"]
    for modulo, endpoints in servidor.CONTRATOS.items():
        for metodo, caminho in endpoints:
            assert caminho in esquema, f"{modulo}: {caminho} ausente"
            assert metodo.lower() in esquema[caminho], f"{modulo}: {metodo} {caminho} ausente"


def test_verificar_contratos_detecta_endpoint_ausente():
    vazio = FastAPI()
    resultado = servidor.verificar_contratos(vazio)
    assert resultado["ok"] is False
    assert not any(m["ok"] for m in resultado["modulos"])


def test_criar_app_e_idempotente():
    antes = servidor._rotas_registradas(servidor.app)
    assert servidor.criar_app() is servidor.app
    assert servidor._rotas_registradas(servidor.app) == antes
    assert len(antes) == len(set(antes))


def test_sessoes_usam_somente_post_para_respeitar_o_cors_da_api():
    """api.py libera apenas GET e POST e o cabeçalho Content-Type."""
    metodos = {m for r in router_sessoes.routes for m in r.methods}
    assert metodos == {"POST"}


def test_preflight_cors_do_frontend_expo_e_aceito(cliente):
    r = cliente.options("/sessoes/ABC234/estado", headers={
        "Origin": "http://localhost:8081",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_origem_desconhecida_nao_recebe_cors(cliente):
    r = cliente.options("/sessoes", headers={
        "Origin": "https://site-qualquer.example",
        "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in r.headers


def test_documentacao_interativa_disponivel(cliente):
    assert cliente.get("/docs").status_code == 200


# --------------------------------------------------------- linha de comando
def test_verificar_retorna_zero_e_imprime_resumo(capsys):
    assert servidor.main(["--verificar"]) == 0
    saida = capsys.readouterr().out
    assert saida.count("[OK]") >= 6
    assert "FALHA" not in saida


def test_verificar_retorna_um_se_o_contrato_quebrar(monkeypatch, capsys):
    monkeypatch.setitem(servidor.CONTRATOS, "9 - Teste", [("GET", "/nao-existe")])
    assert servidor.main(["--verificar"]) == 1
    assert "ausente: GET /nao-existe" in capsys.readouterr().out


@pytest.mark.parametrize("porta", ["0", "70000", "abc"])
def test_porta_invalida_e_recusada(porta):
    with pytest.raises(SystemExit) as e:
        servidor.main(["--porta", porta])
    assert e.value.code == 2


def test_modo_invalido_da_erro_claro(monkeypatch, capsys):
    monkeypatch.setenv("CITIZEN_MODO", "qualquer")
    assert servidor.main([]) == 2
    assert "CITIZEN_MODO inválido" in capsys.readouterr().err


@pytest.fixture
def uvicorn_falso(monkeypatch):
    chamadas = []
    monkeypatch.setattr(servidor.uvicorn, "run", lambda *a, **k: chamadas.append((a, k)))
    monkeypatch.setattr("backend.src.assistente.rotas_api.preparar_modelo", lambda *a, **k: object())
    return chamadas


def test_padrao_escuta_apenas_no_computador_local(uvicorn_falso, capsys):
    assert servidor.main([]) == 0
    (args, kwargs), = uvicorn_falso
    assert args[0] is servidor.app
    assert kwargs["host"] == "127.0.0.1" and kwargs["port"] == 8000
    assert "ATENCAO" not in capsys.readouterr().err


def test_host_de_rede_avisa_sobre_falta_de_autenticacao(uvicorn_falso, capsys):
    servidor.main(["--host", "0.0.0.0", "--porta", "8010"])
    assert "ATENCAO" in capsys.readouterr().err
    assert uvicorn_falso[0][1]["port"] == 8010


def test_reload_usa_import_string(uvicorn_falso):
    servidor.main(["--reload"])
    assert uvicorn_falso[0][0][0] == "app:app"
