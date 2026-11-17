"""Avalia os modelos A/B com a mesma base; gera relatório JSON com tempos reais."""
from pathlib import Path
from time import perf_counter
import json
from .core import carregar, responder

RAIZ = Path(__file__).resolve().parents[2]
CASOS = RAIZ / "backend/data/perguntas_cidadas_teste.json"


def avaliar():
    dados = carregar()
    por_id = {r["id"]: r for r in dados}
    casos = json.loads(CASOS.read_text(encoding="utf-8"))
    resultados = []
    for modelo in ("A", "B"):
        linhas = []
        for caso in casos:
            inicio = perf_counter()
            r = responder(caso["pergunta"], dados, modelo)
            tempo = (perf_counter() - inicio) * 1000
            acertou = (r["status"] == caso["status_esperado"]
                       and r.get("id") == caso["id_esperado"]
                       and (bool(r["fontes"]) == (r["status"] == "ok")))
            esperado = por_id.get(caso["id_esperado"])
            respostas_limite = {
                "entrada_invalida": "Solicitar uma pergunta válida.",
                "ambiguo": "Pedir esclarecimento sem escolher uma orientação.",
                "sem_resposta": "Informar ausência de orientação verificada e sugerir consulta alternativa.",
            }
            linhas.append({**caso, "resposta_esperada": esperado["orientacao"] if esperado else respostas_limite[caso["status_esperado"]],
                           "status_obtido": r["status"], "id_obtido": r.get("id"),
                           "resposta_obtida": r["resposta"], "fontes": r["fontes"],
                           "acerto": acertou, "tempo_ms": round(tempo, 6)})
        acertos = sum(l["acerto"] for l in linhas)
        validas = [l for l in linhas if l["status_obtido"] == "ok"]
        avisos = sum("não é um serviço oficial" in l["resposta_obtida"] for l in validas)
        resultados.append({"modelo": modelo, "quantidade": len(linhas), "acertos": acertos,
                           "taxa_acerto_pct": round(100 * acertos / len(linhas), 2),
                           "tempo_medio_ms": round(sum(l["tempo_ms"] for l in linhas)/len(linhas), 6),
                           "respostas_com_aviso": avisos, "resultados": linhas})
    return resultados


if __name__ == "__main__":
    resultado = avaliar()
    arquivo = RAIZ / "docs/resultados_avaliacao_cidada.json"
    arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for r in resultado:
        print(f'Modelo {r["modelo"]}: {r["acertos"]}/{r["quantidade"]} ({r["taxa_acerto_pct"]}%) | {r["tempo_medio_ms"]:.4f} ms | avisos: {r["respostas_com_aviso"]}')
    print("Relatório:", arquivo)
