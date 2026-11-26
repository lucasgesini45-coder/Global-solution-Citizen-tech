from backend.src.acessibilidade import analisar_acessibilidade
from backend.src.analise_rota import analisar_rota_experimental


def avaliar_rota_integrada(
    caminho_base,
    trechos,
    necessidades,
    data_uso,
    raio_metros=200,
    *,
    permitir_experimental=False,
):
    """
    Reúne acessibilidade e análise experimental de proximidade.

    Cada trecho contém os campos de acessibilidade e os
    campos geográficos necessários à análise da rota.

    Não calcula uma nota geral nem recomenda automaticamente a rota.
    """
    acessibilidade = analisar_acessibilidade(
        trechos,
        necessidades,
    )

    status = acessibilidade["status"]

    # Não executa a análise geográfica com dados de acessibilidade
    # inválidos. Devolve os erros para correção.
    if status == "DADOS_INVALIDOS":
        return {
            "situacao": "DADOS_INVALIDOS",
            "criterio_acessibilidade": "PASSAGEM_SEM_DEGRAUS",
            "decisao_acessibilidade": "CORRIGIR_DADOS",
            "acessibilidade": acessibilidade,
            "analise_proximidade": None,
            "recomendacao_automatica": False,
        }

    decisoes = {
        "COMPATIVEL": "ATENDE_AO_CRITERIO_SOLICITADO",
        "INCOMPATIVEL": "NAO_ATENDE_AO_CRITERIO_SOLICITADO",
        "NAO_VERIFICADA": "INFORMACAO_INSUFICIENTE",
        "NAO_SE_APLICA": "CRITERIO_NAO_SOLICITADO",
    }

    if status not in decisoes:
        raise ValueError(
            f"Status de acessibilidade não reconhecido: {status}"
        )

    # Rota vazia não possui geometria para consultar.
    if not trechos:
        return {
            "situacao": "ROTA_SEM_TRECHOS",
            "criterio_acessibilidade": "PASSAGEM_SEM_DEGRAUS",
            "decisao_acessibilidade": decisoes[status],
            "acessibilidade": acessibilidade,
            "analise_proximidade": None,
            "recomendacao_automatica": False,
        }

    # A análise de proximidade pode ser consultada mesmo quando
    # existe uma barreira, mas não altera a decisão de acessibilidade.
    proximidade = analisar_rota_experimental(
        caminho_base,
        trechos,
        data_uso,
        raio_metros=raio_metros,
        permitir_experimental=permitir_experimental,
    )

    return {
        "situacao": "EXPERIMENTAL",
        "criterio_acessibilidade": "PASSAGEM_SEM_DEGRAUS",
        "decisao_acessibilidade": decisoes[status],
        "acessibilidade": acessibilidade,
        "analise_proximidade": proximidade,
        "recomendacao_automatica": False,
        "limitacoes": [
            "A acessibilidade verifica somente passagem sem degraus.",
            "Não verifica todos os requisitos de acessibilidade.",
            "Proximidade de registros não comprova segurança.",
            "Uma barreira não é compensada por menor proximidade de registros.",
            "Informação ausente não é tratada como acessibilidade confirmada.",
            "Tempo e custo ainda não são comparados neste módulo.",
        ],
    }