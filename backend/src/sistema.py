"""Interface textual oficial do protótipo: python src/sistema.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.src.core import carregar, responder, GRAFO

def main():
    try:
        dados = carregar()
    except ValueError as exc:
        print("Erro:", exc)
        return
    while True:
        print("\n=== CITIZEN MOBILIDADE ===\n1. Perguntar\n2. Explorar temas\n0. Sair")
        opcao = input("Opção: ").strip()
        if opcao == "0":
            return
        if opcao == "2":
            for tema, relacionados in GRAFO.items():
                print(f"{tema}: {', '.join(relacionados)}")
        elif opcao == "1":
            r = responder(input("Pergunta: "), dados)
            print(r["resposta"])
            for fonte in r["fontes"]:
                print("Fonte:", fonte["referencia"], "| verificado em:", fonte["data_verificacao"])
            if r["relacionados"]:
                print("Assuntos relacionados:", ", ".join(r["relacionados"]))
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
