"""Camada conversacional local: recuperação de conteúdo, contexto e limites."""
import re
import unicodedata

def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto.casefold()) if not unicodedata.combining(c))

TEMAS = {
    "gratuidade": r"\b(gratui\w*|de graca|passe livre|sem pagar|isencao|tarifa zero)\b",
    "cartoes": r"\b(cartao|cartoes|bilhete|documentos?|cadastro|segunda via|renovar|formulario|laudo)\b",
    "acessibilidade": r"\b(cadeir\w*|rampas?|elevador\w*|escadas?|acessib\w*|barreiras?|embarcar|mobilidade reduzida)\b",
    "integracao": r"\b(integrac\w*|baldeac\w*|troca de linha|mesmo cartao)\b",
    "direitos": r"\b(direitos?|preferencia\w*|preferencial|prioridade|assentos?|fila)\b",
    "tarifas": r"\b(tarifas?|preco|valor|custa|quanto (pago|gasto)|passagem)\b",
}
SEGUIMENTOS = r"^(e\b|mas\b|entao\b|como assim|por que|porque|onde\b|quais\b|qual\b|quanto\b|posso\b|preciso\b|como faco|me explica|explique|e se|o que mais|sim\b|nao\b)"

def resposta(texto, tema=None, fontes=None, aviso=None, sugestoes=None, origem="orientacao_do_app"):
    return {"resposta": texto, "tema_contexto": tema, "origem_resposta": origem,
            "fontes": fontes or [], "aviso": aviso, "sugestoes": sugestoes or [], "rota": None}

def conversa_local(pergunta, tema_anterior, registros):
    s = normalizar(pergunta).strip()
    if re.fullmatch(r"(oi|ola|bom dia|boa tarde|boa noite|e ai|tudo bem)[!?. ]*", s):
        return resposta("Olá! Posso ajudar você a planejar viagens em São Paulo, entender o transporte público, cartões, gratuidade e acessibilidade. O que você gostaria de saber?")
    if re.fullmatch(r"(obrigad[oa]|valeu|muito obrigad[oa]|entendi|ok|beleza)[!?. ]*", s):
        return resposta("Por nada! Se quiser, podemos continuar falando sobre sua viagem.", tema_anterior)
    if re.search(r"\b(receita de bolo|futebol|politica partidaria|programacao|codigo python|investimento|ignore.*instrucoes)\b", s):
        return resposta("Meu foco é mobilidade urbana e acessibilidade em São Paulo. Posso ajudar com transporte público, planejamento de rotas e orientações cidadãs.")
    temas = [t for t, p in TEMAS.items() if re.search(p, s)]
    # Perguntas sobre documentos do benefício mantêm o assunto de cartão.
    if re.search(r"\b(documentos?|formulario|laudo|solicitar|emitir|tirar|renovar)\b", s) and ("cartoes" in temas or tema_anterior in {"cartoes", "gratuidade"}):
        tema = "cartoes"
    elif re.search(r"\b(gratui\w*|de graca|passe livre|sem pagar|isencao)\b", s):
        tema = "gratuidade"
    elif "integracao" in temas:
        tema = "integracao"
    elif "direitos" in temas:
        tema = "direitos"
    elif "tarifas" in temas:
        tema = "tarifas"
    elif "cartoes" in temas:
        tema = "cartoes"
    elif temas:
        tema = temas[0]
    elif tema_anterior in TEMAS and re.search(SEGUIMENTOS, s):
        tema = tema_anterior
    else:
        tema = None
    if tema:
        reg = next((r for r in registros if r["tema"] == tema and r["status"] == "verificado"), None)
        if reg:
            texto = reg["orientacao"]
            if tema == "cartoes" and re.search(r"\b(documentos?|laudo|formulario)\b", s):
                texto = "Para solicitar o Bilhete Especial PCD, consulte a lista de documentos e exames exigidos para sua situação, preencha o formulário e encaminhe ao atendimento da SPTrans. Os requisitos variam; use o link oficial abaixo."
            elif tema == "acessibilidade" and re.search(r"\b(funcionando|quebrado|hoje|agora|operacional)\b", s):
                texto = "Não tenho acesso ao funcionamento dos elevadores em tempo real. Confirme diretamente com a operadora ou com a equipe da estação antes de sair."
            elif tema == "gratuidade" and re.search(r"\b(onde|solicitar|pedir|faco)\b", s):
                texto += " Você pode iniciar a solicitação pelo portal oficial da SPTrans."
            return resposta(texto, tema, [{"referencia": reg["referencia"], "data_verificacao": reg["data_verificacao"]}], "Confirme as condições atuais no canal oficial.", origem="base_verificada")
    if re.search(r"\b(gps|localizacao|mapa|planejador|origem|destino|trajeto|rotas?|caminhada|onibus|metro|trem|transporte|mobilidade|estacao|viagem)\b", s):
        return resposta("Posso ajudar a planejar seu deslocamento. Selecione origem e destino no mapa e escolha metrô/trem, ônibus ou caminhada. Também é possível priorizar menos caminhada. A acessibilidade física não é garantida pelo aplicativo. Você quer calcular uma rota ou saber algo sobre o transporte?", "rota")
    if re.search(r"\b(privacidade|dados pessoais|historico)\b", s):
        return resposta("O histórico desta conversa fica na sessão da interface. O agente não grava as mensagens no banco. Não envie CPF, documentos ou informações médicas.", "privacidade")
    return None
