"""Busca determinística e validação da base de orientações."""
import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data" / "orientacoes.json"
CAMPOS = {"id", "tema", "perguntas", "orientacao", "referencia", "data_verificacao", "status"}
GRAFO = {
    "cartoes": ["gratuidade", "acessibilidade", "direitos"],
    "gratuidade": ["cartoes", "acessibilidade", "direitos"],
    "acessibilidade": ["gratuidade", "direitos", "cartoes"],
    "direitos": ["acessibilidade", "gratuidade", "cartoes"],
}

def carregar(caminho=BASE):
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Base ausente ou inválida") from exc
    if not isinstance(dados, list) or not dados:
        raise ValueError("A base deve ser uma lista não vazia")
    ids = set()
    for dado in dados:
        if not isinstance(dado, dict) or not CAMPOS.issubset(dado):
            raise ValueError("Registro sem campos obrigatórios")
        if not isinstance(dado["id"], int) or dado["id"] in ids:
            raise ValueError("Identificador repetido ou inválido")
        ids.add(dado["id"])
        if not isinstance(dado["perguntas"], list) or not dado["perguntas"]:
            raise ValueError("Perguntas inválidas")
        if dado["status"] not in ("rascunho", "verificado"):
            raise ValueError("Status inválido")
        if dado["status"] == "verificado" and not all(
            isinstance(dado[c], str) and dado[c].strip()
            for c in ("orientacao", "referencia", "data_verificacao")
        ):
            raise ValueError("Registro verificado incompleto")
    return dados

def termos(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", texto))

def responder(pergunta, registros, modelo="B"):
    if modelo not in ("A", "B"):
        raise ValueError("Modelo inválido")
    palavras = termos(pergunta)
    if not palavras:
        return {"status": "entrada_invalida", "resposta": "Digite uma pergunta.", "fontes": [], "relacionados": []}
    encontrados = []
    for r in registros:
        if r["status"] != "verificado":
            continue
        score = max((len(palavras & termos(t)) / len(palavras) for t in [r["tema"], *r["perguntas"]]), default=0)
        if score >= 0.5:
            encontrados.append((score, r))
    encontrados.sort(key=lambda p: (-p[0], p[1]["id"]))
    if not encontrados:
        return {"status": "sem_resposta", "resposta": "Não encontrei orientação verificada. Consulte o órgão responsável.", "fontes": [], "relacionados": list(GRAFO)}
    if len(encontrados) > 1 and encontrados[0][0] == encontrados[1][0]:
        return {"status": "ambiguo", "resposta": "Há várias orientações possíveis. Especifique seu assunto.", "fontes": [], "relacionados": sorted({r["tema"] for _,r in encontrados})}
    r = encontrados[0][1]
    aviso = " Confirme as regras atuais no canal oficial." if modelo == "B" else ""
    return {"status": "ok", "resposta": r["orientacao"] + aviso, "fontes": [{"referencia": r["referencia"], "data_verificacao": r["data_verificacao"]}], "relacionados": GRAFO.get(r["tema"], [])}
