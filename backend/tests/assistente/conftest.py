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


@pytest.fixture
def copia_dados(dados):
    """Retorna uma cópia profunda da base para testes de validação que modificam dados."""
    return copy.deepcopy(dados)
