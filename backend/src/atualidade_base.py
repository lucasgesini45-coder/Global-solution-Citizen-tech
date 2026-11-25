from datetime import date, datetime

from backend.src.base_seguranca import selecionar_candidatos


def selecionar_candidatos_na_data(
    base,
    data_uso,
    *,
    permitir_experimental=False,
):
    """
    Reavalia os candidatos na data de utilização.

    Mantém a janela declarada no JSON.
    Não calcula segurança nem garante atualização da fonte.
    """
    if isinstance(data_uso, datetime):
        data_uso = data_uso.date()
    elif not isinstance(data_uso, date):
        raise ValueError("A data de uso deve ser date ou datetime.")

    # Valida a base e exige autorização explícita para uso experimental.
    candidatos = selecionar_candidatos(
        base,
        permitir_experimental=permitir_experimental,
    )

    contexto = base["contexto"]
    data_consulta = date.fromisoformat(contexto["data_consulta"])
    janela_dias = contexto["janela_dias"]

    if data_uso < data_consulta:
        raise ValueError(
            "A data de uso não pode ser anterior à consulta da base."
        )

    elegiveis = []
    fora_da_janela = []

    for grupo in candidatos:
        # O validador garante uma única data para cada candidato.
        data_fato = date.fromisoformat(grupo["datas_fato"][0])
        idade_dias = (data_uso - data_fato).days

        if idade_dias > janela_dias:
            fora_da_janela.append({
                "id_exportacao": grupo["id_exportacao"],
                "motivo": "FORA_DA_JANELA_NA_DATA_DE_USO",
                "idade_dias": idade_dias,
            })
        else:
            elegiveis.append(grupo)

    # Essa data é um indicador da cobertura disponível.
    # Não representa necessariamente a data de publicação da fonte.
    valor_ultimo_registro = contexto.get(
        "maior_data_registro_encontrada"
    )

    ultimo_registro = None
    defasagem_dias = None

    if valor_ultimo_registro is not None:
        if not isinstance(valor_ultimo_registro, str):
            raise ValueError(
                "A maior data de registro deve ser texto ou null."
            )

        try:
            ultimo_registro = date.fromisoformat(
                valor_ultimo_registro
            )
        except ValueError as erro:
            raise ValueError(
                "A maior data de registro é inválida."
            ) from erro

        if ultimo_registro > data_consulta:
            situacao_cobertura = "DATA_DE_REGISTRO_INCONSISTENTE"
        else:
            defasagem_dias = (data_uso - ultimo_registro).days

            if defasagem_dias > janela_dias:
                situacao_cobertura = "ULTIMO_REGISTRO_FORA_DA_JANELA"
            else:
                situacao_cobertura = "ULTIMO_REGISTRO_DENTRO_DA_JANELA"
    else:
        situacao_cobertura = "SEM_DATA_DE_REGISTRO"

    if len(elegiveis) + len(fora_da_janela) != len(candidatos):
        raise ValueError("Contagem temporal inconsistente.")

    return {
        "situacao_base": "EXPERIMENTAL",
        "data_uso": data_uso.isoformat(),
        "data_consulta_base": data_consulta.isoformat(),
        "dias_desde_consulta": (data_uso - data_consulta).days,
        "janela_dias": janela_dias,
        "resumo": {
            "candidatos_antes": len(candidatos),
            "candidatos_elegiveis_na_data": len(elegiveis),
            "candidatos_fora_da_janela": len(fora_da_janela),
            "grupos_pendentes_na_base": base["resumo"]["grupos_pendentes"],
        },
        "cobertura_temporal": {
            "maior_data_registro_encontrada": (
                ultimo_registro.isoformat()
                if ultimo_registro is not None
                else None
            ),
            "dias_desde_ultimo_registro": defasagem_dias,
            "situacao": situacao_cobertura,
            "atualizacao_da_fonte_confirmada": False,
        },
        "candidatos": elegiveis,
        "excluidos_por_idade": fora_da_janela,
        "limitacoes": [
            "Elegibilidade temporal não significa segurança da rota.",
            "A referência espacial criminal permanece não confirmada.",
            "A maior data de registro não comprova atualização da fonte.",
            "Não foi definido um limite operacional de defasagem da fonte.",
            "Ausência de candidatos não significa ausência de risco.",
        ],
    }