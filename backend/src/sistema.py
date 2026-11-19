"""Interface textual da Global Solution; não depende de internet ou IA externa."""
from backend.src.core import carregar, responder, temas_disponiveis, por_tema, formatar, GRAFO


def mostrar(r, saida=print):
    saida(r["resposta"])
    for fonte in r["fontes"]:
        saida("Fonte: " + fonte["referencia"] + " | verificada em: " + fonte["data_verificacao"])
    if r["relacionados"]:
        saida("Assuntos relacionados: " + ", ".join(r["relacionados"]))


def main(entrada=input, saida=print):
    try:
        dados = carregar()
    except ValueError as exc:
        saida("Erro: " + str(exc))
        return
    modelo = "B"
    saida("Citizen Assist AI — orientação cidadã em mobilidade urbana. Não é canal oficial.")
    while True:
        saida("\n1. Perguntar\n2. Explorar temas\n3. Escolher modelo de resposta (atual: " + modelo + ")\n4. Assistente sobre o aplicativo (opcional)\n0. Sair")
        try:
            opcao = entrada("Opção: ").strip()
            if opcao == "0":
                return
            if opcao == "1":
                mostrar(responder(entrada("Pergunta: "), dados, modelo), saida)
            elif opcao == "2":
                temas = temas_disponiveis(dados)
                for i, tema in enumerate(temas, 1):
                    saida(f"{i}. {tema}")
                escolha = entrada("Tema (0 para voltar): ").strip()
                if escolha == "0":
                    continue
                if not escolha.isdecimal() or not 1 <= int(escolha) <= len(temas):
                    saida("Opção inválida.")
                    continue
                tema = temas[int(escolha)-1]
                registros = por_tema(dados, tema)
                for r in registros:
                    saida(f'{r["id"]}. {r["perguntas"][0]}')
                escolha = entrada("Identificador (0 para voltar): ").strip()
                if escolha == "0":
                    continue
                registro = next((r for r in registros if str(r["id"]) == escolha), None)
                if registro is None:
                    saida("Opção inválida.")
                else:
                    mostrar(formatar(registro, modelo), saida)
            elif opcao == "3":
                escolha = entrada("A (direto com fonte) ou B (fonte + aviso): ").strip().upper()
                if escolha in ("A", "B"):
                    modelo = escolha
                    saida("Modelo selecionado: " + modelo)
                else:
                    saida("Opção inválida.")
            elif opcao == "4":
                try:
                    from backend.src.assistente.cli import abrir_assistente
                    abrir_assistente()
                except (ImportError, OSError, RuntimeError):
                    saida("Módulo opcional indisponível; use o menu principal.")
            else:
                saida("Opção inválida.")
        except (EOFError, KeyboardInterrupt):
            saida("Consulta encerrada.")
            return


if __name__ == "__main__":
    main()
