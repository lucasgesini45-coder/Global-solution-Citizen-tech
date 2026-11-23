from datetime import date, datetime


def avaliar_atualidade(
        data_fato,
        data_registro,
        data_referencia,
        janela_dias=90
):
    """
    Verifica somente a adequação temporal da ocorrência.
    Não avalia coordenadas, duplicidades ou segurança da rota.
    """

    if type(janela_dias) is not int or janela_dias < 0:
        raise ValueError("A janela deve ser um número inteiro não negativo."
                         )

    datas = []

    for valor in (data_fato, data_registro, data_referencia):
        if isinstance(valor, datetime): datas.append(valor.date())
        elif isinstance(valor, date): datas.append(valor)
        else:
            return {
                "apta": False,
                "motivo": "DATA_INVALIDA",
                "idade_dias": None
            }

    fato, registro, referencia = datas

    if fato > registro:
        return {
            "apta": False,
            "motivo": "FATO_POSTERIOR_AO_REGISTRO",
            "idade_dias": None

        }

    if fato > referencia or registro > referencia:
        return {
            "apta": False,
            "motivo": "DATA_FUTURA",
            "idade_dias": None
        }
    idade_dias = (referencia - fato).days

    if idade_dias > janela_dias:
        return {
            "apta": False,
            "motivo": "FORA_DA_JANELA",
            "idade_dias": idade_dias
        }

    return {
        "apta": True,
        "motivo": "DENTRO_DA_JANELA",
        "idade_dias": idade_dias
    }