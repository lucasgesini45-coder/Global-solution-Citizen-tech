"""Publicação conjunta do frontend Expo Web e da API FastAPI."""
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from .api import app

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@app.get("/", include_in_schema=False)
@app.get("/projeto", include_in_schema=False)
@app.get("/projeto/", include_in_schema=False)
def pagina():
    arquivo = DIST / "index.html"
    if not arquivo.is_file():
        raise HTTPException(503, "Frontend ainda não compilado.")
    return FileResponse(arquivo, headers={"Cache-Control": "no-cache"})


@app.get("/{caminho:path}", include_in_schema=False)
def arquivo_estatico(caminho: str):
    raiz = DIST.resolve()
    arquivo = (raiz / caminho).resolve()
    if not arquivo.is_relative_to(raiz) or not arquivo.is_file():
        raise HTTPException(404, "Arquivo não encontrado.")
    return FileResponse(arquivo)
