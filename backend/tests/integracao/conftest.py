"""Preparação comum dos testes de integração (parte 5)."""
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:  # permite `import app` mesmo com o comando `pytest` simples
    sys.path.insert(0, str(RAIZ))
os.environ.setdefault("CITIZEN_MODO", "teste")

from fastapi.testclient import TestClient  # noqa: E402

import app as servidor  # noqa: E402
from backend.src.sessoes import obter_gerenciador  # noqa: E402


@pytest.fixture(scope="session")
def cliente():
    return TestClient(servidor.app)


@pytest.fixture(autouse=True)
def sessoes_limpas():
    """Cada teste começa sem sessões e não deixa nenhuma para trás."""
    obter_gerenciador().limpar()
    yield
    obter_gerenciador().limpar()
