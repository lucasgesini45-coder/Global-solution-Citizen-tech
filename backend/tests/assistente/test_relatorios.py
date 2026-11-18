"""T-A17 e T-A18: relatórios de avaliação e de calibração (em caminhos temporários)."""
from datetime import datetime

from src.assistente import avaliacao, calibracao
from src.assistente.config import LIMIARES_CALIBRACAO

AGORA = datetime(2026, 11, 12, 10, 0, 0)


def test_limiares_de_calibracao_sao_13_de_020_a_080():
    assert len(LIMIARES_CALIBRACAO) == 13
    assert LIMIARES_CALIBRACAO[0] == 0.20 and LIMIARES_CALIBRACAO[-1] == 0.80
    assert all(abs((b - a) - 0.05) < 1e-9 for a, b in zip(LIMIARES_CALIBRACAO, LIMIARES_CALIBRACAO[1:]))


def test_t_a17_relatorio_de_avaliacao(modelo, tmp_path):
    destino = tmp_path / "avaliacao.md"
    r = avaliacao.gerar_relatorio(caminho_saida=destino, modelo=modelo, agora=AGORA)
    texto = destino.read_text(encoding="utf-8")
    assert 0 <= r["top1"] <= 12 and 0 <= r["top3"] <= 12 and r["n"] == 12 and r["top3"] >= r["top1"]
    assert "12/11/2026 10:00:00" in texto and modelo.hash_base[:12] in texto and "Limiar de confiança em uso: 0.4" in texto
    for item in ("| Top-1 |", "| Top-3 |", "Tempo médio de resposta (ms)", "Tempo máximo de resposta (ms)"):
        assert item in texto
    linhas_detalhe = [l for l in texto.splitlines() if l.startswith("| ") and l.split("|")[1].strip().isdigit()]
    assert len(linhas_detalhe) == 12
    assert ("Avaliação feita com apenas 12 perguntas; os percentuais são apenas indicativos. "
            "As intenções R02, T05 e H05 não possuem pergunta de teste. "
            "Respostas revisadas pela equipe: 0 de 15 no momento da geração.") in texto


def test_t_a18_relatorio_de_calibracao(modelo, tmp_path):
    destino = tmp_path / "calibracao.md"
    r = calibracao.gerar_relatorio(caminho_saida=destino, modelo=modelo, agora=AGORA)
    assert len(r["tabela"]) == 13
    for linha in r["tabela"]:
        assert linha["certas"] + linha["erradas"] + linha["fallback"] == 12
    texto = destino.read_text(encoding="utf-8")
    assert "Estimativa baseada em 12 perguntas; use com cautela." in texto
    assert "Este relatório NÃO altera esse valor; a decisão é da equipe." in texto
    assert [l.split("|")[1].strip() for l in texto.splitlines() if l.startswith("| 0.")] == [f"{x:.2f}" for x in LIMIARES_CALIBRACAO]
