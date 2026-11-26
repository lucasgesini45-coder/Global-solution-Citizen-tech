from backend.src.base_seguranca import carregar_base_seguranca
from backend.src.atualidade_base import selecionar_candidatos_na_data
from backend.src.consulta_rota import consultar_proximidade_rota


def analisar_rota_experimental(
    caminho_base,
    trechos,
    data_uso,
    raio_metros=200,
    *,
    permitir_experimental=False,
):
    """
    Integra leitura, validação, atualidade e proximidade.

    Não calcula pontuação de segurança.
    Não compara nem recomenda rotas.
    """
    base = carregar_base_seguranca(caminho_base)

    avaliacao_temporal = selecionar_candidatos_na_data(
        base,
        data_uso,
        permitir_experimental=permitir_experimental,
    )

    consulta = consultar_proximidade_rota(
        trechos,
        avaliacao_temporal["candidatos"],
        raio_metros=raio_metros,
    )

    candidatos_elegiveis = avaliacao_temporal["resumo"][
        "candidatos_elegiveis_na_data"
    ]

    if candidatos_elegiveis == 0:
        situacao_consulta = "SEM_CANDIDATOS_ELEGIVEIS"
    elif consulta["quantidade_grupos_distintos"] == 0:
        situacao_consulta = "SEM_GRUPOS_PROXIMOS"
    else:
        situacao_consulta = "GRUPOS_PROXIMOS_ENCONTRADOS"

    # Reúne limitações sem repetir textos idênticos.
    limitacoes = []

    for lista in (
        base["limitacoes"],
        avaliacao_temporal["limitacoes"],
        consulta["limitacoes"],
    ):
        for texto in lista:
            if texto not in limitacoes:
                limitacoes.append(texto)

    return {
        "situacao": "EXPERIMENTAL",
        "situacao_consulta": situacao_consulta,
        "pontuacao_seguranca": None,
        "contexto_base": dict(base["contexto"]),
        "avaliacao_temporal": {
            "data_uso": avaliacao_temporal["data_uso"],
            "data_consulta_base": avaliacao_temporal["data_consulta_base"],
            "dias_desde_consulta": avaliacao_temporal["dias_desde_consulta"],
            "janela_dias": avaliacao_temporal["janela_dias"],
            "resumo": avaliacao_temporal["resumo"],
            "cobertura_temporal": avaliacao_temporal["cobertura_temporal"],
        },
        "proximidade_rota": consulta,
        "limitacoes": limitacoes,
    }