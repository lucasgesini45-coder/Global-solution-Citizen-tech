"""Relatório de avaliação (seção 10).

Comando (a partir de backend/):  python -m src.assistente.avaliacao
Gera docs/relatorio_avaliacao_assistente.md, sobrescrevendo o anterior.

Definições: top-1 = a intenção de maior probabilidade é a esperada; top-3 = a esperada está entre
as 3 de maior probabilidade (ambos independem do limiar). Tempo de resposta = tempo da previsão
(passos 1 a 4 da seção 8.4), sem incluir o carregamento do modelo, em milissegundos.
"""
import time
from datetime import datetime

import sklearn

from .base import carregar_base
from .config import CAMINHO_RELATORIO_AVALIACAO, LIMIAR_CONFIANCA, TOP_K, resolver_caminho
from .modelo import ModeloAssistente, carregar_ou_treinar
from .previsao import ordenar_intencoes, prever, validar_pergunta


def medir(modelo: ModeloAssistente, perguntas: list) -> list:
    """Uma linha por pergunta de teste com previsão, acertos e tempo (ms)."""
    linhas = []
    for indice, item in enumerate(perguntas, start=1):
        pergunta, esperada = item["pergunta"], item["intencao_esperada"]
        inicio = time.perf_counter()
        prever(pergunta, modelo)
        tempo_ms = (time.perf_counter() - inicio) * 1000.0
        ordenadas = ordenar_intencoes(modelo, validar_pergunta(pergunta))
        prevista, confianca = ordenadas[0]
        linhas.append({
            "n": indice, "pergunta": pergunta, "esperada": esperada, "prevista": prevista,
            "confianca": round(confianca, 4),
            "top1": prevista == esperada,
            "top3": esperada in [id_ for id_, _ in ordenadas[:TOP_K]],
            "tempo_ms": tempo_ms,
        })
    return linhas


def _sim_nao(valor: bool) -> str:
    return "sim" if valor else "não"


def montar_relatorio(modelo, dados_base: dict, linhas: list, agora: datetime) -> str:
    n = len(linhas)
    acertos1 = sum(1 for l in linhas if l["top1"])
    acertos3 = sum(1 for l in linhas if l["top3"])
    tempos = [l["tempo_ms"] for l in linhas]
    revisadas = sum(1 for i in dados_base["intencoes"] if i["revisada_pela_equipe"])
    total = len(dados_base["intencoes"])
    texto = [
        "# Relatório de avaliação do assistente de dúvidas",
        "",
        f"- Gerado em: {agora.strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Hash da base (12 primeiros caracteres): {modelo.hash_base[:12]}",
        f"- Versão do scikit-learn: {sklearn.__version__}",
        f"- Limiar de confiança em uso: {LIMIAR_CONFIANCA}",
        "",
        "## Resumo",
        "",
        "| Métrica | Resultado |",
        "|---|---|",
        f"| Top-1 | {acertos1} de {n} ({acertos1 / n * 100:.1f}%) |",
        f"| Top-3 | {acertos3} de {n} ({acertos3 / n * 100:.1f}%) |",
        f"| Tempo médio de resposta (ms) | {sum(tempos) / n:.2f} |",
        f"| Tempo máximo de resposta (ms) | {max(tempos):.2f} |",
        "",
        "## Detalhe por pergunta",
        "",
        "| # | Pergunta | Esperada | Prevista | Confiança | Top-1 | Top-3 | Tempo (ms) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        texto.append(
            f"| {l['n']} | {l['pergunta']} | {l['esperada']} | {l['prevista']} | {l['confianca']:.4f} | "
            f"{_sim_nao(l['top1'])} | {_sim_nao(l['top3'])} | {l['tempo_ms']:.2f} |")
    texto += [
        "",
        "## Limitações",
        "",
        "Avaliação feita com apenas 12 perguntas; os percentuais são apenas indicativos. "
        "As intenções R02, T05 e H05 não possuem pergunta de teste. "
        f"Respostas revisadas pela equipe: {revisadas} de {total} no momento da geração.",
        "",
    ]
    return "\n".join(texto)


def gerar_relatorio(caminho_saida=None, modelo=None, caminho_testes=None, agora=None) -> dict:
    """Gera o arquivo e devolve as métricas (para testes e para o terminal)."""
    dados_base, dados_testes = carregar_base(caminho_testes=caminho_testes)
    modelo = modelo or carregar_ou_treinar(caminho_testes=caminho_testes)
    linhas = medir(modelo, dados_testes)
    texto = montar_relatorio(modelo, dados_base, linhas, agora or datetime.now())
    destino = resolver_caminho(caminho_saida or CAMINHO_RELATORIO_AVALIACAO)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return {
        "top1": sum(1 for l in linhas if l["top1"]), "top3": sum(1 for l in linhas if l["top3"]),
        "n": len(linhas), "caminho": str(destino), "linhas": linhas,
    }


def main() -> None:
    r = gerar_relatorio()
    print(f"Relatório gerado em {r['caminho']} | top-1: {r['top1']}/{r['n']} | top-3: {r['top3']}/{r['n']}")


if __name__ == "__main__":
    main()
