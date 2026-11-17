"""Recuperação documental local, sem geração de fatos nem acesso arbitrário à web."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from .core import termos, STOP

BASE = Path(__file__).resolve().parents[1] / "data" / "documentos_transporte.json"
DOMINIOS = {"www.metro.sp.gov.br", "www.sptrans.com.br", "bilheteunico.sptrans.com.br", "atendimento.sptrans.com.br", "www.cptm.sp.gov.br", "passelivre.antt.gov.br", "www.gov.br"}
ESCOPO = set("metro trem trens onibus transporte transportes mobilidade bilhete cartao sptrans cptm antt passagem tarifa tarifas estacao estacoes baldeacao integracao gratuidade passe cadeira cadeirante acessibilidade elevador catraca atende bicicleta rota trajeto caminhada".split())
FORA = set("receita bolo futebol politica eleicao presidente bitcoin investimento programacao python javascript matematica astrologia".split())

def bloqueado(texto):
    return bool(termos(texto) & FORA or re.search(r"\b(ignore|desconsidere|esqueca|esqueça)\b.{0,40}\b(instrucoes|instruções|regras|prompt|escopo)\b", texto.lower()))
SINONIMOS = {"precos":"preco","valor":"preco","custa":"preco","custo":"preco","pago":"preco","passagens":"passagem","tarifas":"tarifa","cartoes":"cartao","estacoes":"estacao","trens":"trem","bike":"bicicleta","pet":"animal","pets":"animal","cachorro":"cao","cachorros":"cao","gatos":"gato","perdido":"perda","perdi":"perda","roubaram":"roubo","roubado":"roubo","extraviado":"perda","idosos":"idoso","cadeirantes":"cadeirante","elevadores":"elevador","gratuito":"gratuidade","gratis":"gratuidade","gratuita":"gratuidade","recarregar":"recarga","recarrego":"recarga","creditos":"credito","coloco":"colocar","colocar":"recarga","fechamento":"fecha","fecham":"fecha","abertura":"abre","abrem":"abre"}
GENERICOS = set("oi ola bom boa dia tarde noite gostaria saber favor por gentileza tenho funciona funciona fazer consigo pode poderia pode me informar dizer explicar preciso quero posso qual quais acerca sobre ai e entao".split())
SUGESTOES = ["Quanto custa a passagem de metrô?", "Como pedir gratuidade PCD?", "Posso levar bicicleta dobrável no metrô?"]

def tokens(texto):
    return {SINONIMOS.get(t,t) for t in termos(texto)-STOP-GENERICOS}

def escopo(texto):
    t=tokens(texto)
    if bloqueado(texto):
        return False
    return bool(t & ESCOPO or {"passe","livre"} <= t or "pcd" in t or "atende" in t)

def documentos():
    dados=json.loads(BASE.read_text(encoding="utf-8"))
    return [d for d in dados if urlparse(d["url"]).scheme=="https" and urlparse(d["url"]).hostname in DOMINIOS]

def resposta_limite(texto, origem="sem_resposta_verificada", sugestoes=None):
    return {"resposta":texto,"origem_resposta":origem,"fontes":[],"sugestoes":sugestoes or SUGESTOES,"aviso":None,"rota":None}

def consultar_documentos(pergunta, registros):
    """Busca em resumos e perguntas de documentos, além das orientações verificadas.
    Só devolve trecho cadastrado; sem composição livre ou novas afirmações."""
    p=tokens(pergunta)
    if not p or not escopo(pergunta):
        return resposta_limite("Meu atendimento é exclusivo para transporte público, mobilidade urbana, tarifas, benefícios e acessibilidade.", "fora_escopo")
    if p <= {"cartao","comum","bilhete","unico"}:
        return resposta_limite("Você quer emitir, recarregar ou solicitar a segunda via do Bilhete Único?", "ambiguo", ["Como emitir cartão comum?", "Onde recarregar o Bilhete Único Comum?", "Quanto custa a segunda via do Bilhete Único?"])
    candidatos=[]
    fontes=[]
    for r in registros:
        if r.get("status")=="verificado":
            fontes.append({"titulo":"Orientação cidadã", "url":r["referencia"],"perguntas":r["perguntas"],"resumo":r["orientacao"],"data_consulta":r["data_verificacao"]})
    try:
        fontes.extend(documentos())
    except (OSError,ValueError,KeyError):
        pass
    for d in fontes:
        if urlparse(d["url"]).hostname not in DOMINIOS:
            continue
        score=0
        for frase in d["perguntas"]:
            q=tokens(frase)
            n=len(p&q)
            if n>=2:
                score=max(score,2*n/(len(p)+len(q)))
        if score>=0.53:
            candidatos.append((score,d))
    candidatos.sort(key=lambda x:-x[0])
    if not candidatos:
        return resposta_limite("Não encontrei um trecho oficial suficientemente relacionado à sua pergunta. Especifique a linha, o serviço ou o cartão desejado.")
    melhores=[d for s,d in candidatos if candidatos[0][0]-s<=0.06]
    if len(melhores)>1:
        return resposta_limite("Encontrei mais de uma orientação possível. Qual destas dúvidas corresponde melhor ao que você precisa?", "ambiguo", [d["perguntas"][0] for d in melhores[:3]])
    d=candidatos[0][1]
    return {"resposta":d["resumo"],"origem_resposta":"documento_oficial","fontes":[{"referencia":d["url"],"data_verificacao":d["data_consulta"],"titulo":d["titulo"]}],"sugestoes":[],"aviso":"Resumo de fonte institucional consultada na data indicada. Confirme regras atuais no órgão responsável. Não é canal oficial.","rota":None}
