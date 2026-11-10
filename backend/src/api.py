"""API única para site e celular."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .core import carregar, responder, GRAFO
from .rotas_api import router as rotas_router

app = FastAPI(title="Citizen Mobilidade", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:19006"], allow_methods=["GET","POST"], allow_headers=["Content-Type"])

app.include_router(rotas_router)

class Pergunta(BaseModel):
    pergunta: str = Field(max_length=500)
    modelo: str = "B"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/temas")
def temas():
    return GRAFO

@app.post("/consultar")
def consultar(body: Pergunta):
    try:
        return responder(body.pergunta, carregar(), body.modelo)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
