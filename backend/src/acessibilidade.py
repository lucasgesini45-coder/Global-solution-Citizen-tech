import json


# Lê um arquivo JSON e devolve os dados em estruturas Python.
def carregar_rota_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
                                            rota = json.load(arquivo)

    except FileNotFoundError:
         raise ValueError(
              f"Arquivo JSON não encontrado: {caminho}"
         ) from None

    except json.JSONDecodeError as erro:
         raise ValueError(
              f"JSON inválido na linha {erro.lineno}, "
              f"coluna {erro.colno}."
         ) from None

    except UnicodeDecodeError:
         raise ValueError(
              "O arquivo deve estar salvo com codificação UTF-8."
         ) from None
    except OSError as erro:
         raise ValueError(
              f"Não foi possível ler o arquivo: {erro}"
         ) from None

    return rota

# Avalia somente a necessidade de passagem sem degraus.
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


# Identifica as barreiras e as informações pendentes.
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


# Verifica a estrutura e os valores dos dados da rota.
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


# Função principal: valida os dados antes de avaliar.
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

    # Encerra a função se os dados forem inválidos.
    if erros:
        return {
            "status": "DADOS_INVALIDOS",
            "barreiras": [],
            "pendencias": [],
            "erros": erros
        }

    # Avalia os dados que passaram pelas verificações.
    detalhes = detalhar_acessibilidade(rota, necessidades)
    detalhes["erros"] = []

    return detalhes