"""Inicia a API do Assistente de Dúvidas a partir da pasta backend/."""
import sys
from pathlib import Path
import uvicorn

BACKEND = Path(__file__).resolve().parent
SRC = BACKEND / "src"
for p in (str(SRC), str(BACKEND), str(BACKEND.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == "__main__":
    uvicorn.run("assistente.rotas_api:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=[str(SRC)])
