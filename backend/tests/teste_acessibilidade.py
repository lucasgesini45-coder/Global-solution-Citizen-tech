# Dados simulados para aprender e testar a lógica.
from backend.src.acessibilidade import (
    avaliar_acessibilidade,
    detalhar_acessibilidade,
    validar_rota,
    analisar_acessibilidade
)


necessidades = {
    "precisa_sem_degraus": True
}

rota = [
    {
        "id": "T1",
        "descricao": "Caminhada até o ponto",
        "passagem_sem_degraus": True
    },
    {
        "id": "T2",
        "descricao": "Embarque no ônibus",
        "passagem_sem_degraus": False
    },
    {
        "id": "T3",
        "descricao": "Caminhada até o destino",
        "passagem_sem_degraus": None
    }
]


# 1. Avalia somente a necessidade de passagem sem degraus.
def avaliar_acessibilidade(rota, necessidades):
    if not rota:
        return "NAO_VERIFICADA"

    if not necessidades["precisa_sem_degraus"]:
        return "NAO_SE_APLICA"

    resultado = "COMPATIVEL"

    for trecho in rota:
        passagem = trecho["passagem_sem_degraus"]

        if passagem is False:
            resultado = "INCOMPATIVEL"

        elif passagem is None:
            if resultado != "INCOMPATIVEL":
                resultado = "NAO_VERIFICADA"

    return resultado


# 2. Identifica as barreiras e as informações pendentes.
def detalhar_acessibilidade(rota, necessidades):
    status = avaliar_acessibilidade(rota, necessidades)
    barreiras = []
    pendencias = []

    if not rota:
        pendencias.append("A rota não possui trechos.")

    elif necessidades["precisa_sem_degraus"]:
        for trecho in rota:
            identificacao = (
                f'{trecho["id"]} - {trecho["descricao"]}'
            )

            passagem = trecho["passagem_sem_degraus"]

            if passagem is False:
                barreiras.append(identificacao)

            elif passagem is None:
                pendencias.append(identificacao)

    return {
        "status": status,
        "barreiras": barreiras,
        "pendencias": pendencias
    }


# 3. Verifica a estrutura e os valores dos dados da rota.
def validar_rota(rota):
    erros = []

    if not isinstance(rota, list):
        erros.append("A rota deve ser uma lista.")
        return erros

    for posicao, trecho in enumerate(rota, start=1):
        if not isinstance(trecho, dict):
            erros.append(
                f"Trecho {posicao}: deve ser um dicionário."
            )
            continue

        campos = ["id", "descricao", "passagem_sem_degraus"]

        for campo in campos:
            if campo not in trecho:
                erros.append(
                    f"Trecho {posicao}: falta o campo '{campo}'."
                )

        if "passagem_sem_degraus" in trecho:
            passagem = trecho["passagem_sem_degraus"]

            if (
                passagem is not True
                and passagem is not False
                and passagem is not None
            ):
                erros.append(
                    f"Trecho {posicao}: passagem_sem_degraus "
                    "deve ser True, False ou None."
                )

    return erros


# 4. Valida os dados antes de realizar a avaliação.
# Esta é a função que a equipe deverá chamar.
def analisar_acessibilidade(rota, necessidades):
    erros = validar_rota(rota)

    if not isinstance(necessidades, dict):
        erros.append("As necessidades devem ser um dicionário.")

    elif "precisa_sem_degraus" not in necessidades:
        erros.append("Falta informar 'precisa_sem_degraus'.")

    else:
        precisa = necessidades["precisa_sem_degraus"]

        if precisa is not True and precisa is not False:
            erros.append(
                "'precisa_sem_degraus' deve ser True ou False."
            )

    # Se houver erros, encerra antes de avaliar.
    if erros:
        return {
            "status": "DADOS_INVALIDOS",
            "barreiras": [],
            "pendencias": [],
            "erros": erros
        }

    # Este trecho também pertence à função.
    detalhes = detalhar_acessibilidade(rota, necessidades)
    detalhes["erros"] = []

    return detalhes


# Mostra a necessidade e os trechos da rota simulada.
print("Precisa de passagem sem degraus?")
print(necessidades["precisa_sem_degraus"])

print("\nTrechos da rota:")

for trecho in rota:
    print(trecho["id"], "-", trecho["descricao"])
    print("Passagem sem degraus:", trecho["passagem_sem_degraus"])

avaliacao = avaliar_acessibilidade(rota, necessidades)
print("\nResultado da avaliação:", avaliacao)


# Testes da lógica de avaliação.
cenarios = [
    {
        "nome": "Todos os trechos sem degraus",
        "passagens": [True, True, True],
        "esperado": "COMPATIVEL"
    },
    {
        "nome": "Um trecho sem informação",
        "passagens": [True, True, None],
        "esperado": "NAO_VERIFICADA"
    },
    {
        "nome": "Barreira antes da informação ausente",
        "passagens": [True, False, None],
        "esperado": "INCOMPATIVEL"
    },
    {
        "nome": "Barreira depois da informação ausente",
        "passagens": [None, True, False],
        "esperado": "INCOMPATIVEL"
    },
    {
        "nome": "Rota vazia",
        "passagens": [],
        "esperado": "NAO_VERIFICADA"
    }
]

necessidades_teste = {
    "precisa_sem_degraus": True
}

print("\n--- TESTES DE ACESSIBILIDADE ---")

for cenario in cenarios:
    rota_teste = []

    for passagem in cenario["passagens"]:
        rota_teste.append({
            "passagem_sem_degraus": passagem
        })

    resultado = avaliar_acessibilidade(
        rota_teste,
        necessidades_teste
    )

    if resultado == cenario["esperado"]:
        print("PASSOU:", cenario["nome"])
    else:
        print("FALHOU:", cenario["nome"])
        print("Esperado:", cenario["esperado"])
        print("Recebido:", resultado)


# Exibe os detalhes da rota simulada original.
detalhes = detalhar_acessibilidade(rota, necessidades)

print("\n--- AVALIAÇÃO DETALHADA ---")
print("Resultado:", detalhes["status"])

for barreira in detalhes["barreiras"]:
    print("Barreira:", barreira)

for pendencia in detalhes["pendencias"]:
    print("Informação pendente:", pendencia)


# Confere o conteúdo da avaliação detalhada.
print("\n--- TESTE DA AVALIAÇÃO DETALHADA ---")

detalhes_teste = detalhar_acessibilidade(rota, necessidades)

assert detalhes_teste["status"] == "INCOMPATIVEL"
assert detalhes_teste["barreiras"] == [
    "T2 - Embarque no ônibus"
]
assert detalhes_teste["pendencias"] == [
    "T3 - Caminhada até o destino"
]

print("PASSOU: Status, barreira e pendência corretos.")


# Verifica os dados da rota original.
print("\n--- VALIDAÇÃO DOS DADOS ---")

erros = validar_rota(rota)

if erros:
    for erro in erros:
        print("ERRO:", erro)
else:
    print("Dados válidos para as verificações realizadas.")


# "False" é texto: está incorreto de propósito neste teste.
rota_invalida = [
    {
        "id": "T4",
        "descricao": "Entrada da estação",
        "passagem_sem_degraus": "False"
    }
]

print("\n--- TESTE COM DADO INVÁLIDO ---")

erros = validar_rota(rota_invalida)

if erros:
    print("Avaliação bloqueada: corrija os dados.")

    for erro in erros:
        print("ERRO:", erro)
else:
    detalhes_validados = detalhar_acessibilidade(
        rota_invalida,
        necessidades
    )
    print("Resultado:", detalhes_validados["status"])


# Testa a função que reúne validação e avaliação.
print("\n--- TESTES DA FUNÇÃO INTEGRADA ---")

# Caso 1: rota original e necessidades válidas.
analise = analisar_acessibilidade(rota, necessidades)

assert analise["status"] == "INCOMPATIVEL"
assert analise["barreiras"] == [
    "T2 - Embarque no ônibus"
]
assert analise["pendencias"] == [
    "T3 - Caminhada até o destino"
]
assert analise["erros"] == []

print("PASSOU: Dados válidos avaliados corretamente.")


# Caso 2: necessidade com texto no lugar de booleano.
necessidades_invalidas = {
    "precisa_sem_degraus": "True"
}

analise_invalida = analisar_acessibilidade(
    rota,
    necessidades_invalidas
)

assert analise_invalida["status"] == "DADOS_INVALIDOS"
assert analise_invalida["erros"] == [
    "'precisa_sem_degraus' deve ser True ou False."
]

print("PASSOU: Necessidade inválida bloqueada.")


# Caso 3: rota com texto no lugar de booleano.
analise_rota_invalida = analisar_acessibilidade(
    rota_invalida,
    necessidades
)

assert analise_rota_invalida["status"] == "DADOS_INVALIDOS"
assert analise_rota_invalida["erros"] == [
    "Trecho 1: passagem_sem_degraus deve ser True, False ou None."
]

print("PASSOU: Rota inválida bloqueada.")

from pathlib import Path
from backend.src.acessibilidade import carregar_rota_json

print("\n--- TESTE DE LEITURA DO JSON ---")

# Localiza o JSON na pasta beckend/data.
caminho_json = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "rota_exemplo.json"
)
rota_carregada = carregar_rota_json(caminho_json)

analise_json = analisar_acessibilidade(rota_carregada,
                                       necessidades
)                                       

assert analise_json["status"] == "INCOMPATIVEL"
assert analise_json["barreiras"] == [
    "T2 - Embarque no ônibus"
]
assert analise_json["pendencias"] == [
    "T3 - Caminhada até o destino"
]
assert analise_json["erros"]==[]

print("PASSOU: Rota carregada do JSON e avaliada corretamente.")


from tempfile import TemporaryDirectory

print("\n--- TESTES DE ERROS NA LEITURA ---")

# Cria uma pasta temporária, removida automaticamente ao terminar.
with TemporaryDirectory() as pasta:
    pasta_temporaria = Path(pasta)

    # Caso 1: tenta ler um arquivo que não existe.
    caminho_ausente = pasta_temporaria / "inexistente.json"

    try:
        carregar_rota_json(caminho_ausente)
    except ValueError as erro:
        assert "Arquivo JSON não encontrado" in str(erro)
        print("PASSOU: Arquivo inexistente identificado.")
    else:
        raise AssertionError("Deveria rejeitar arquivo inexistente.")

    # Caso 2: cria um arquivo com JSON incompleto.
    caminho_malformado = pasta_temporaria / "malformado.json"
    caminho_malformado.write_text('{"id":', encoding="utf-8")

    try:
        carregar_rota_json(caminho_malformado)
    except ValueError as erro:
        assert "JSON inválido" in str(erro)
        print("PASSOU: JSON malformado identificado.")
    else:
        raise AssertionError("Deveria rejeitar JSON malformado.")