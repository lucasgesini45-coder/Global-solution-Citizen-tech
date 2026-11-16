"""Relatório de calibração do limiar (seção 11).

Comando (a partir de backend/):  python -m src.assistente.calibracao
Gera docs/relatorio_calibracao_assistente.md. Este módulo NÃO altera LIMIAR_CONFIANCA:
a decisão de mudar o limiar é da equipe.
"""
from datetime import datetime

import sklearn

from .base import carregar_base
from .config import CAMINHO_RELATORIO_CALIBRACAO, LIMIARES_CALIBRACAO, LIMIAR_CONFIANCA, resolver_caminho
from .modelo import carregar_ou_treinar
from .previsao import ordenar_intencoes, validar_pergunta


def calcular_tabela(modelo, perguntas: list) -> list:
    """Uma linha por limiar: respondidas (confiança >= limiar), certas, erradas e fallback."""
    melhores = []
    for item in perguntas:
        id_previsto, confianca = ordenar_intencoes(modelo, validar_pergunta(item["pergunta"]))[0]
        melhores.append((id_previsto == item["intencao_esperada"], confianca))
    tabela = []
    for limiar in LIMIARES_CALIBRACAO:
        respondidas = [acertou for acertou, conf in melhores if conf >= limiar]
        certas = sum(1 for a in respondidas if a)
        tabela.append({
            "limiar": limiar, "respondidas": len(respondidas), "certas": certas,
            "erradas": len(respondidas) - certas, "fallback": len(melhores) - len(respondidas),
        })
    return tabela


def gerar_relatorio(caminho_saida=None, modelo=None, caminho_testes=None, agora=None) -> dict:
    _, dados_testes = carregar_base(caminho_testes=caminho_testes)
    modelo = modelo or carregar_ou_treinar(caminho_testes=caminho_testes)
    tabela = calcular_tabela(modelo, dados_testes)
    momento = agora or datetime.now()
    texto = [
        "# Relatório de calibração do limiar do assistente de dúvidas",
        "",
        f"- Gerado em: {momento.strftime('%d/%m/%Y %H:%M:%S')}",
        f"- Hash da base (12 primeiros caracteres): {modelo.hash_base[:12]}",
        f"- Versão do scikit-learn: {sklearn.__version__}",
        f"- Limiar de confiança em uso: {LIMIAR_CONFIANCA}",
        "",
        "| Limiar | Perguntas respondidas (confiança ≥ limiar) | Respondidas corretamente | Respondidas incorretamente | Caiu no fallback |",
        "|---|---|---|---|---|",
    ]
    for l in tabela:
        texto.append(f"| {l['limiar']:.2f} | {l['respondidas']} | {l['certas']} | {l['erradas']} | {l['fallback']} |")
    texto += [
        "",
        "O limiar em uso é o valor de LIMIAR_CONFIANCA em backend/src/assistente/config.py. "
        "Este relatório NÃO altera esse valor; a decisão é da equipe.",
        "",
        "Estimativa baseada em 12 perguntas; use com cautela.",
        "",
    ]
    destino = resolver_caminho(caminho_saida or CAMINHO_RELATORIO_CALIBRACAO)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(texto), encoding="utf-8")
    return {"tabela": tabela, "caminho": str(destino)}


def main() -> None:
    r = gerar_relatorio()
    print(f"Relatório gerado em {r['caminho']} ({len(r['tabela'])} limiares)")


if __name__ == "__main__":
    main()
