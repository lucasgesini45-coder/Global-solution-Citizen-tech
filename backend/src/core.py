"""Citizen Assist AI: leitura JSON, busca por tokens e navegação por grafo."""
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data" / "orientacoes.json"
CAMPOS = {"id", "tema", "perguntas", "orientacao", "referencia", "data_verificacao", "status"}
GRAFO = {
    "cartoes": ["gratuidade", "acessibilidade", "direitos", "servicos"],
    "gratuidade": ["cartoes", "acessibilidade", "direitos", "servicos"],
    "acessibilidade": ["gratuidade", "servicos", "cartoes", "direitos"],
    "direitos": ["acessibilidade", "gratuidade", "cartoes"],
    "servicos": ["cartoes", "acessibilidade", "gratuidade"],
}
STOP = set("a o as os e de da do das dos em no na nos nas um uma para por com ao aos se eu meu minha como qual quais quem onde quando posso pode quero preciso".split())


def carregar(caminho=BASE):
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Base ausente ou inválida") from exc
    if not isinstance(dados, list) or not dados:
        raise ValueError("A base deve ser uma lista não vazia")
    ids = set()
    for dado in dados:
        if not isinstance(dado, dict) or not CAMPOS.issubset(dado):
            raise ValueError("Registro sem campos obrigatórios")
        if type(dado["id"]) is not int or dado["id"] in ids:
            raise ValueError("Identificador repetido ou inválido")
        ids.add(dado["id"])
        if not isinstance(dado["tema"], str) or not dado["tema"].strip():
            raise ValueError("Tema inválido")
        if (not isinstance(dado["perguntas"], list) or not dado["perguntas"]
                or not all(isinstance(p, str) and p.strip() for p in dado["perguntas"])):
            raise ValueError("Perguntas inválidas")
        if dado["status"] not in ("rascunho", "verificado"):
            raise ValueError("Status inválido")
        if dado["status"] == "verificado":
            if not all(isinstance(dado[k], str) and dado[k].strip()
                       for k in ("orientacao", "referencia", "data_verificacao")):
                raise ValueError("Registro verificado incompleto")
            try:
                date.fromisoformat(dado["data_verificacao"])
            except ValueError as exc:
                raise ValueError("Data de verificação inválida") from exc
    return dados


def termos(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", texto))


def temas_disponiveis(registros):
    return sorted({r["tema"] for r in registros if r["status"] == "verificado"})


def por_tema(registros, tema):
    return [r for r in registros if r["tema"] == tema and r["status"] == "verificado"]


def formatar(r, modelo="B"):
    if modelo not in ("A", "B"):
        raise ValueError("Modelo inválido")
    aviso = " Confirme as regras atuais no canal oficial. Este assistente não é um serviço oficial." if modelo == "B" else ""
    return {"status": "ok", "id": r["id"], "resposta": r["orientacao"] + aviso,
            "fontes": [{"referencia": r["referencia"], "data_verificacao": r["data_verificacao"]}],
            "relacionados": GRAFO.get(r["tema"], [])}


def responder(pergunta, registros, modelo="B"):
    if modelo not in ("A", "B"):
        raise ValueError("Modelo inválido")
    palavras = termos(pergunta) - STOP if isinstance(pergunta, str) else set()
    if not palavras:
        return {"status": "entrada_invalida", "resposta": "Digite uma pergunta.", "fontes": [], "relacionados": temas_disponiveis(registros)}
    encontrados = []
    for r in registros:
        if r["status"] != "verificado":
            continue
        # Dice: 2 * interseção / soma dos tamanhos. Desconta palavras genéricas.
        # Não usa o tema sozinho como correspondência de uma pergunta específica.
        score = 0.0
        for frase in r["perguntas"]:
            alvo = termos(frase) - STOP
            if not alvo:
                continue
            intersecao = len(palavras & alvo)
            if intersecao and (intersecao >= 2 or palavras == alvo):
                score = max(score, 2 * intersecao / (len(palavras) + len(alvo)))
        if score >= 0.55:
            encontrados.append((score, r))
    encontrados.sort(key=lambda p: (-p[0], p[1]["id"]))
    if not encontrados:
        return {"status": "sem_resposta", "resposta": "Não encontrei orientação verificada. Consulte o órgão responsável ou escolha um assunto.", "fontes": [], "relacionados": temas_disponiveis(registros)}
    if len(encontrados) > 1 and encontrados[0][0] - encontrados[1][0] <= 0.05:
        return {"status": "ambiguo", "resposta": "Há várias orientações possíveis. Especifique seu assunto.", "fontes": [], "relacionados": sorted({r["tema"] for _,r in encontrados})}
    return formatar(encontrados[0][1], modelo)
