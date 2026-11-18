"""Configuração comum dos testes do assistente."""
import copy
import socket
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.assistente.base import carregar_base  # noqa: E402
from src.assistente.modelo import carregar_ou_treinar  # noqa: E402


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    """T-A19: nenhum teste do assistente pode abrir conexão de rede."""
    def bloqueado(*args, **kwargs):
        raise AssertionError("Teste tentou usar a rede.")
    monkeypatch.setattr(socket.socket, "connect", bloqueado)


@pytest.fixture(scope="session")
def dados():
    base, testes = carregar_base()
    return base, testes


@pytest.fixture
def copia_dados(dados):
    base, testes = dados
    return copy.deepcopy(base), copy.deepcopy(testes)


@pytest.fixture(scope="session")
def modelo(tmp_path_factory):
    """Modelo treinado em pasta temporária (nunca toca no .joblib real)."""
    caminho = tmp_path_factory.mktemp("modelo") / "assistente.joblib"
    return carregar_ou_treinar(caminho_modelo=caminho)
