from __future__ import annotations

from src.rede_demo import criar_rede_demo, ponto
from src.recomendar import processar_pedido
from src.tarifas import carregar_regras


def main() -> None:
    rede = criar_rede_demo()
    regras = carregar_regras("data/tarifas_demo.json")
    o = ponto(0.0, -100.0)
    d1 = ponto(4000.0, 300.0)
    pedido = {
        "origem": {"lat": o[0], "lon": o[1]},
        "destino": {"lat": d1[0], "lon": d1[1]},
        "partida": "2026-11-09T08:00:00",
    }
    resposta = processar_pedido(pedido, rede, regras)

    for r in resposta["rotas"]:
        ordem = r["ordem"]
        tempo_total_min = r["tempo_total_min"]
        centavos = r["custo"]["centavos"]
        if centavos is not None:
            custo = f"R$ {centavos / 100:.2f}"
        else:
            custo = "tarifa não confirmada"
        caminhada_m = r["caminhada_m"]
        baldeacoes = r["baldeacoes"]
        saida = r["saida"]
        chegada = r["chegada"]

        print(
            f"Rota {ordem}: {tempo_total_min} min | {custo} | {caminhada_m} m a pé | {baldeacoes} baldeação(ões) | {saida} -> {chegada}"
        )
        print("  Trechos:")
        for t in r["trechos"]:
            tipo = t["tipo"]
            inicio = t["inicio"]
            fim = t["fim"]
            de = t["de"]
            para = t["para"]
            if tipo == "transporte":
                print(
                    f"    [{inicio} - {fim}] {tipo.upper()}: {t['linha']} de {de} até {para}"
                )
            elif tipo == "caminhada":
                print(
                    f"    [{inicio} - {fim}] {tipo.upper()}: {de} até {para} ({t['distancia_m']} m)"
                )
            elif tipo == "espera":
                print(f"    [{inicio} - {fim}] {tipo.upper()}: em {de}")
        print("  Motivos:")
        for m in r["motivos"]:
            print(f"    - {m}")
        print()

    if resposta.get("aviso"):
        print(f"Aviso: {resposta['aviso']}")


if __name__ == "__main__":
    main()
