"""Inicia a API do Assistente de Dúvidas diretamente (sem precisar configurar PYTHONPATH)."""
import sys
from pathlib import Path
import uvicorn

RAIZ = Path(__file__).resolve().parent
SRC = RAIZ / "backend" / "src"
for p in (str(SRC), str(RAIZ / "backend"), str(RAIZ)):
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == "__main__":
    uvicorn.run("assistente.rotas_api:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=[str(SRC)])
