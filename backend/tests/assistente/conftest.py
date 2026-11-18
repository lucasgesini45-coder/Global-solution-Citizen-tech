<<<<<<< HEAD
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
=======
# encoding: utf-8
import copy
import socket
import pytest
from backend.src.assistente.base import carregar_base
from backend.src.assistente.modelo import carregar_ou_treinar


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    orig_socket = socket.socket

    class SocketMock(orig_socket):
        def connect(self, address):
            if isinstance(address, tuple) and address[0] in (
                "127.0.0.1",
                "localhost",
                "::1",
            ):
                return super().connect(address)
            raise AssertionError("Teste tentou usar a rede externa.")

    monkeypatch.setattr(socket, "socket", SocketMock)


@pytest.fixture
def dados():
    """Carrega a base de conhecimento real."""
    return carregar_base()


@pytest.fixture
def modelo():
    """Carrega ou treina o modelo para uso nos testes."""
    return carregar_ou_treinar()
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e


@pytest.fixture
def copia_dados(dados):
<<<<<<< HEAD
    base, testes = dados
    return copy.deepcopy(base), copy.deepcopy(testes)


@pytest.fixture(scope="session")
def modelo(tmp_path_factory):
    """Modelo treinado em pasta temporária (nunca toca no .joblib real)."""
    caminho = tmp_path_factory.mktemp("modelo") / "assistente.joblib"
    return carregar_ou_treinar(caminho_modelo=caminho)
=======
    """Retorna uma cópia profunda da base para testes de validação que modificam dados."""
    return copy.deepcopy(dados)
>>>>>>> 4760994196d36001ba3a482a9ebc09ee7e109b9e
