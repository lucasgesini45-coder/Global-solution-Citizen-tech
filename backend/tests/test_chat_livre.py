from backend.src.conversa_local import conversa_local
from backend.src.core import carregar
from backend.src.agente_api import ConversaEntrada, conversar

def test_pergunta_livre():
    r = conversar(ConversaEntrada(pergunta="Sou cadeirante, consigo viajar de graça?"))
    assert r["tema_contexto"] == "gratuidade"
    assert r["fontes"]

def test_continuidade_documentos():
    r = conversar(ConversaEntrada(pergunta="E quais documentos preciso?", tema_contexto="gratuidade"))
    assert r["tema_contexto"] == "cartoes"
    assert r["fontes"]

def test_saudacao():
    assert "Olá" in conversar(ConversaEntrada(pergunta="Oi"))["resposta"]

def test_elevador_nao_confirmado():
    r = conversar(ConversaEntrada(pergunta="O elevador está funcionando hoje?"))
    assert "tempo real" in r["resposta"]

def test_fora_do_escopo():
    assert "mobilidade" in conversa_local("Receita de bolo", None, carregar())["resposta"]

def test_rota_sem_coordenadas():
    r = conversar(ConversaEntrada(pergunta="Como chegar na FIAP?"))
    assert r["tema_contexto"] == "rota"
    assert r["rota"] is None
