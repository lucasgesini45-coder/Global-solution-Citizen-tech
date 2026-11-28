import json
from datetime import date, datetime
from pathlib import Path


def ler_data_iso(valor, campo):
    """Aceita somente uma data no formato AAAA-MM-DD."""
    if not isinstance(valor, str):
        raise ValueError(f"{campo}: informe uma data como texto.")

    try:
        data = date.fromisoformat(valor)
    except ValueError:
        raise ValueError(
            f"{campo}: data inválida. Use AAAA-MM-DD."
        ) from None

    if data.isoformat() != valor:
        raise ValueError(
            f"{campo}: use exatamente o formato AAAA-MM-DD."
        )

    return data


def validar_base_acessibilidade(base):
    """Valida a estrutura da base simulada, sem alterar os dados."""
    if not isinstance(base, dict):
        raise ValueError("A base deve ser um dicionário.")

    if base.get("versao_esquema") != "1.0":
        raise ValueError("Versão do esquema não suportada.")

    if base.get("tipo_base") != "SIMULADA":
        raise ValueError(
            "Este leitor aceita somente a base SIMULADA nesta etapa."
        )

    if base.get("criterio") != "PASSAGEM_SEM_DEGRAUS":
        raise ValueError("Critério de acessibilidade não suportado.")

    registros = base.get("registros")

    if not isinstance(registros, list):
        raise ValueError("'registros' deve ser uma lista.")

    campos = (
        "id_trecho",
        "descricao",
        "passagem_sem_degraus",
        "fonte",
        "data_verificacao",
        "valido_ate",
    )

    identificadores = set()

    for posicao, registro in enumerate(registros, start=1):
        contexto = f"Registro {posicao}"

        if not isinstance(registro, dict):
            raise ValueError(
                f"{contexto}: deve ser um dicionário."
            )

        for campo in campos:
            if campo not in registro:
                raise ValueError(
                    f"{contexto}: falta o campo '{campo}'."
                )

        for campo in ("id_trecho", "descricao"):
            valor = registro[campo]

            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(
                    f"{contexto}: '{campo}' deve ser texto não vazio."
                )

        identificador = registro["id_trecho"]

        if identificador != identificador.strip():
            raise ValueError(
                f"{contexto}: id_trecho possui espaços nas extremidades."
            )

        if identificador in identificadores:
            raise ValueError(
                f"{contexto}: id_trecho repetido: {identificador}."
            )

        identificadores.add(identificador)

        passagem = registro["passagem_sem_degraus"]

        if (
            passagem is not True
            and passagem is not False
            and passagem is not None
        ):
            raise ValueError(
                f"{contexto}: passagem_sem_degraus "
                "deve ser True, False ou None."
            )

        fonte = registro["fonte"]
        verificacao = registro["data_verificacao"]
        validade = registro["valido_ate"]

        # Informação desconhecida pode não ter fonte nem datas.
        sem_metadados = (
            fonte is None
            and verificacao is None
            and validade is None
        )

        if sem_metadados:
            if passagem is not None:
                raise ValueError(
                    f"{contexto}: uma condição informada "
                    "precisa de fonte e datas."
                )

            continue

        # Se algum metadado foi preenchido, exige o conjunto completo.
        if not isinstance(fonte, str) or not fonte.strip():
            raise ValueError(
                f"{contexto}: fonte deve ser texto não vazio."
            )

        data_verificacao = ler_data_iso(
            verificacao,
            f"{contexto} - data_verificacao",
        )

        valido_ate = ler_data_iso(
            validade,
            f"{contexto} - valido_ate",
        )

        if valido_ate < data_verificacao:
            raise ValueError(
                f"{contexto}: a validade não pode terminar "
                "antes da verificação."
            )

    return base


def carregar_base_acessibilidade(caminho):
    """Lê o JSON e valida seu conteúdo."""
    try:
        with Path(caminho).open(
            "r",
            encoding="utf-8-sig",
        ) as arquivo:
            base = json.load(arquivo)

    except FileNotFoundError:
        raise ValueError(
            f"Arquivo não encontrado: {caminho}"
        ) from None

    except json.JSONDecodeError as erro:
        raise ValueError(
            f"JSON inválido na linha {erro.lineno}, "
            f"coluna {erro.colno}."
        ) from None

    except UnicodeError:
        raise ValueError(
            "O arquivo deve estar codificado em UTF-8."
        ) from None

    except OSError as erro:
        raise ValueError(
            f"Não foi possível ler o arquivo: {erro}"
        ) from None

    return validar_base_acessibilidade(base)


def consultar_acessibilidade(base, id_trecho, data_consulta):
    """
    Consulta um trecho em uma data.

    Informação ausente, futura ou vencida retorna None.
    O registro original não é alterado.
    """
    validar_base_acessibilidade(base)

    if not isinstance(id_trecho, str) or not id_trecho.strip():
        raise ValueError("id_trecho deve ser texto não vazio.")

    if isinstance(data_consulta, datetime):
        data_consulta = data_consulta.date()

    if not isinstance(data_consulta, date):
        raise ValueError(
            "data_consulta deve ser date ou datetime."
        )

    registro = next(
        (
            item
            for item in base["registros"]
            if item["id_trecho"] == id_trecho
        ),
        None,
    )

    resultado = {
        "id_trecho": id_trecho,
        "tipo_base": base["tipo_base"],
        "data_consulta": data_consulta.isoformat(),
        "passagem_sem_degraus": None,
        "motivo": "TRECHO_NAO_ENCONTRADO",
        "fonte": None,
        "data_verificacao": None,
        "valido_ate": None,
    }

    if registro is None:
        return resultado

    for campo in ("fonte", "data_verificacao", "valido_ate"):
        resultado[campo] = registro[campo]

    passagem = registro["passagem_sem_degraus"]

    if passagem is None:
        resultado["motivo"] = "INFORMACAO_AUSENTE"
        return resultado

    verificacao = ler_data_iso(
        registro["data_verificacao"],
        "data_verificacao",
    )
    validade = ler_data_iso(
        registro["valido_ate"],
        "valido_ate",
    )

    if verificacao > data_consulta:
        resultado["motivo"] = "VERIFICACAO_FUTURA"
        return resultado

    if data_consulta > validade:
        resultado["motivo"] = "INFORMACAO_VENCIDA"
        return resultado

    resultado["passagem_sem_degraus"] = passagem
    resultado["motivo"] = "INFORMACAO_DENTRO_DA_VALIDADE"

    return resultado