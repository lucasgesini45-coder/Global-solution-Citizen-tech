from backend.src.core import carregar, responder, temas_disponiveis, por_tema
from backend.src.avaliacao_cidada import avaliar
from backend.src.sistema import main


def test_base_cidada_minima():
    dados = carregar()
    verificados = [r for r in dados if r["status"] == "verificado"]
    assert len(verificados) >= 15
    assert len(temas_disponiveis(dados)) >= 3
    assert all(r["referencia"].startswith("https://") for r in verificados)
    assert por_tema(dados, "acessibilidade")


def test_modelos_e_limites():
    dados = carregar()
    a = responder("Como emitir cartão comum?", dados, "A")
    b = responder("Como emitir cartão comum?", dados, "B")
    assert a["status"] == b["status"] == "ok"
    assert a["fontes"] == b["fontes"]
    assert "não é um serviço oficial" in b["resposta"]
    assert responder("", dados)["status"] == "entrada_invalida"
    assert responder("receita de bolo de chocolate", dados)["status"] == "sem_resposta"


def test_avaliacao_dos_dois_modelos():
    resultados = avaliar()
    assert len(resultados) == 2
    assert all(r["quantidade"] >= 12 for r in resultados)
    assert all(r["taxa_acerto_pct"] >= 80 for r in resultados)
    assert resultados[1]["respostas_com_aviso"] > resultados[0]["respostas_com_aviso"]


def test_roteiro_terminal():
    # Roteiro automatizado de tarefas, não avaliação com participante humano.
    entradas = iter(["99", "1", "", "2", "1", "10", "3", "A", "1", "Como emitir cartão comum?", "0"])
    saidas = []
    main(entrada=lambda _: next(entradas), saida=saidas.append)
    texto = "\n".join(saidas)
    assert "Opção inválida" in texto
    assert "Digite uma pergunta" in texto
    assert "Fonte:" in texto
    assert "Modelo selecionado: A" in texto
