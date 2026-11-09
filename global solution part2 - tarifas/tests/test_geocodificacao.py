import datetime
import pytest

from src.config import GEOCODIFICACAO_INTERVALO_MIN_S
import src.geocodificacao as geo
from src.geocodificacao import buscar_endereco
from src.historico import iniciar_banco

LIMITES_DEMO = (-23.60, -46.70, -23.50, -46.60)


@pytest.fixture(autouse=True)
def acelerar_relogio(monkeypatch):
    relogio = [10000.0]

    def fake_monotonic():
        val = relogio[0]
        relogio[0] += 0.0001
        return val

    def fake_sleep(seg):
        relogio[0] += seg

    monkeypatch.setattr(geo, "_time_monotonic", fake_monotonic)
    monkeypatch.setattr(geo, "_time_sleep", fake_sleep)
    geo._ultimo_acesso = 0.0


@pytest.fixture
def banco_geo(tmp_path):
    caminho = str(tmp_path / "teste_geo.sqlite")
    iniciar_banco(caminho)
    return caminho


def test_t_g01_user_agent_ausente(banco_geo, monkeypatch):
    monkeypatch.delenv("ROTAVIVA_USER_AGENT", raising=False)
    chamado = []

    def mock_http(url, **kwargs):
        chamado.append(url)
        return []

    resp = buscar_endereco("rua das flores", banco_geo, LIMITES_DEMO, cliente_http=mock_http)
    assert resp.get("erro", {}).get("codigo") == "user_agent_ausente"
    assert len(chamado) == 0


def test_t_g02_cache_repeticao(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")
    chamadas = []

    def mock_http(url, **kwargs):
        chamadas.append(url)
        return [
            {
                "display_name": "Rua das Flores, Centro",
                "lat": "-23.55",
                "lon": "-46.63",
            }
        ]

    resp1 = buscar_endereco(
        "Rua das   Flores", banco_geo, LIMITES_DEMO, cliente_http=mock_http
    )
    assert "candidatos" in resp1
    assert len(chamadas) == 1

    resp2 = buscar_endereco(
        "  rua   das flores  ", banco_geo, LIMITES_DEMO, cliente_http=mock_http
    )
    assert "candidatos" in resp2
    assert len(chamadas) == 1


def test_t_g03_cache_expirado_31_dias(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")
    chamadas = []

    def mock_http(url, **kwargs):
        chamadas.append(url)
        return [
            {
                "display_name": "Rua das Flores",
                "lat": "-23.55",
                "lon": "-46.63",
            }
        ]

    data_antiga = datetime.datetime(2026, 1, 1, 10, 0, 0)
    data_recente = data_antiga + datetime.timedelta(days=31)

    buscar_endereco(
        "rua das flores",
        banco_geo,
        LIMITES_DEMO,
        cliente_http=mock_http,
        agora=data_antiga,
    )
    assert len(chamadas) == 1

    buscar_endereco(
        "rua das flores",
        banco_geo,
        LIMITES_DEMO,
        cliente_http=mock_http,
        agora=data_recente,
    )
    assert len(chamadas) == 2


def test_t_g04_consulta_invalida(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")
    r1 = buscar_endereco("ab", banco_geo, LIMITES_DEMO)
    assert r1.get("erro", {}).get("codigo") == "consulta_invalida"

    r2 = buscar_endereco("a" * 201, banco_geo, LIMITES_DEMO)
    assert r2.get("erro", {}).get("codigo") == "consulta_invalida"


def test_t_g05_resposta_fora_da_area(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")

    def mock_http(url, **kwargs):
        return [
            {
                "display_name": "Ponto Longe",
                "lat": "-10.00",
                "lon": "-50.00",
            }
        ]

    resp = buscar_endereco(
        "ponto longe", banco_geo, LIMITES_DEMO, cliente_http=mock_http
    )
    assert resp.get("erro", {}).get("codigo") == "sem_resultado_na_area_piloto"


def test_t_g06_erro_de_rede_nao_grava_cache(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")

    def mock_http(url, **kwargs):
        raise ConnectionError("Falha de rede simulada")

    resp = buscar_endereco(
        "rua que falha", banco_geo, LIMITES_DEMO, cliente_http=mock_http
    )
    assert resp.get("erro", {}).get("codigo") == "geocodificacao_indisponivel"

    import sqlite3

    with sqlite3.connect(banco_geo) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache_geocodificacao")
        assert cursor.fetchone()[0] == 0


def test_t_g07_resposta_dois_pontos_sucesso(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")

    def mock_http(url, **kwargs):
        return [
            {
                "display_name": "Ponto 1",
                "lat": "-23.55",
                "lon": "-46.63",
            },
            {
                "display_name": "Ponto 2",
                "lat": "-23.56",
                "lon": "-46.64",
            },
        ]

    resp = buscar_endereco(
        "pontos centrais", banco_geo, LIMITES_DEMO, cliente_http=mock_http
    )
    assert "candidatos" in resp
    assert len(resp["candidatos"]) == 2
    for c in resp["candidatos"]:
        assert isinstance(c["lat"], float)
        assert isinstance(c["lon"], float)
        assert isinstance(c["nome"], str)
    assert (
        resp["atribuicao"]
        == "Dados de endereço © colaboradores do OpenStreetMap"
    )


def test_t_g08_intervalo_minimo_chamadas(banco_geo, monkeypatch):
    monkeypatch.setenv("ROTAVIVA_USER_AGENT", "TestAgent/1.0")

    geo._ultimo_acesso = 0.0
    relogio = [1000.0]

    def fake_monotonic():
        return relogio[0]

    def fake_sleep(seg):
        relogio[0] += seg

    monkeypatch.setattr(geo, "_time_monotonic", fake_monotonic)
    monkeypatch.setattr(geo, "_time_sleep", fake_sleep)

    tempos_chamadas = []

    def mock_http(url, **kwargs):
        tempos_chamadas.append(relogio[0])
        return [
            {
                "display_name": "Local Teste",
                "lat": "-23.55",
                "lon": "-46.63",
            }
        ]

    buscar_endereco("consulta um", banco_geo, LIMITES_DEMO, cliente_http=mock_http)
    buscar_endereco("consulta dois", banco_geo, LIMITES_DEMO, cliente_http=mock_http)

    assert len(tempos_chamadas) == 2
    intervalo = tempos_chamadas[1] - tempos_chamadas[0]
    assert intervalo >= GEOCODIFICACAO_INTERVALO_MIN_S - 1e-9
