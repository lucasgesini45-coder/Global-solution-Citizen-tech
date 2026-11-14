"""Conversa no terminal (seção 12.2).

Uso no menu do sistema.py: chamar `abrir_assistente()`.
As funções de leitura e escrita são parâmetros para permitir teste sem teclado.
Nenhuma pergunta é guardada ou registrada em log.
"""
from .config import (
    PALAVRA_SAIDA_TERMINAL,
    TEXTO_BOAS_VINDAS_TERMINAL,
    TEXTO_ENTRADA_INVALIDA_TERMINAL,
    TEXTO_VOCE_QUIS_DIZER,
)
from .modelo import carregar_ou_treinar
from .previsao import prever, validar_pergunta


def executar_conversa(modelo, entrada=input, saida=print) -> None:
    saida(TEXTO_BOAS_VINDAS_TERMINAL)
    while True:
        try:
            linha = entrada("> ")
        except (EOFError, KeyboardInterrupt):
            return
        linha = linha.strip()
        if linha.lower() == PALAVRA_SAIDA_TERMINAL:
            return
        try:
            validar_pergunta(linha)
        except ValueError:
            saida(TEXTO_ENTRADA_INVALIDA_TERMINAL)
            continue
        resultado = prever(linha, modelo)
        saida(resultado.resposta)
        if resultado.aviso:
            saida(resultado.aviso)
        if resultado.sugestoes:
            saida(TEXTO_VOCE_QUIS_DIZER)
            for numero, sugestao in enumerate(resultado.sugestoes, start=1):
                saida(f"{numero}. {sugestao}")


def abrir_assistente(entrada=input, saida=print) -> None:
    """Carrega (ou treina) o modelo e abre a conversa. Chamada pela opção do menu."""
    try:
        modelo = carregar_ou_treinar()
    except Exception:  # noqa: BLE001 - o terminal não deve quebrar o menu por falha do assistente
        saida("Assistente indisponível.")
        return
    executar_conversa(modelo, entrada, saida)
