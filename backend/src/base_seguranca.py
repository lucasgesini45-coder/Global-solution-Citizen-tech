import json
import math
from datetime import date
from pathlib import Path


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def inteiro_nao_negativo(valor):
    # Evita aceitar True e False como números inteiros.
    return type(valor) is int and valor >= 0


def validar_base_seguranca(base):
    """
    Valida o contrato inicial do JSON de integração.

    Não confirma a veracidade dos registros, a referência
    espacial ou a segurança de uma rota.
    """
    exigir(isinstance(base, dict), "A base deve ser um dicionário.")

    exigir(
        base.get("versao_esquema") == "1.0",
        "Versão do esquema não suportada.",
    )
    exigir(
        base.get("situacao_base") == "EXPERIMENTAL",
        "Situação da base não suportada.",
    )

    contexto = base.get("contexto")
    resumo = base.get("resumo")
    grupos = base.get("grupos")

    exigir(isinstance(contexto, dict), "Contexto ausente ou inválido.")
    exigir(isinstance(resumo, dict), "Resumo ausente ou inválido.")
    exigir(isinstance(grupos, list), "Grupos devem ser uma lista.")

    exigir(
        isinstance(contexto.get("data_consulta"), str),
        "Data da consulta ausente ou inválida.",
    )

    try:
        data_consulta = date.fromisoformat(contexto["data_consulta"])
    except ValueError as erro:
        raise ValueError("Data da consulta inválida.") from erro

    janela = contexto.get("janela_dias")

    exigir(
        inteiro_nao_negativo(janela),
        "Janela de dias deve ser um inteiro não negativo.",
    )

    exigir(
        isinstance(base.get("limitacoes"), list)
        and bool(base["limitacoes"])
        and all(
            isinstance(item, str) and item.strip()
            for item in base["limitacoes"]
        ),
        "A base deve informar suas limitações.",
    )

    identificadores = set()
    candidatos = 0
    pendentes = 0
    linhas_candidatos = 0
    linhas_pendentes = 0

    for posicao, grupo in enumerate(grupos, start=1):
        prefixo = f"Grupo {posicao}: "

        exigir(
            isinstance(grupo, dict),
            prefixo + "deve ser um dicionário.",
        )

        identificador = grupo.get("id_exportacao")

        exigir(
            isinstance(identificador, str) and identificador.strip(),
            prefixo + "identificador inválido.",
        )
        exigir(
            identificador not in identificadores,
            prefixo + "identificador repetido.",
        )
        identificadores.add(identificador)

        quantidade = grupo.get("quantidade_linhas_origem")

        exigir(
            type(quantidade) is int and quantidade > 0,
            prefixo + "quantidade de linhas inválida.",
        )

        datas = grupo.get("datas_fato")

        exigir(
            isinstance(datas, list) and bool(datas),
            prefixo + "datas ausentes ou inválidas.",
        )

        for valor in datas:
            exigir(
                isinstance(valor, str),
                prefixo + "a data deve ser texto.",
            )
            try:
                dia = date.fromisoformat(valor)
            except ValueError as erro:
                raise ValueError(prefixo + "data inválida.") from erro

            idade = (data_consulta - dia).days

            exigir(
                0 <= idade <= janela,
                prefixo + "data fora da janela declarada.",
            )

        exigir(
            len(datas) == len(set(datas)),
            prefixo + "datas repetidas.",
        )

        naturezas = grupo.get("naturezas")

        exigir(
            isinstance(naturezas, list)
            and all(
                isinstance(item, str) and item.strip()
                for item in naturezas
            ),
            prefixo + "naturezas inválidas.",
        )
        exigir(
            len(naturezas) == len(set(naturezas)),
            prefixo + "naturezas repetidas.",
        )

        motivos = grupo.get("motivos_pendencia")

        exigir(
            isinstance(motivos, list)
            and all(
                isinstance(item, str) and item.strip()
                for item in motivos
            ),
            prefixo + "motivos de pendência inválidos.",
        )

        pontos = grupo.get("quantidade_pontos_distintos")

        exigir(
            type(pontos) is int and pontos > 0,
            prefixo + "quantidade de pontos inválida.",
        )

        exigir(
            "ponto_para_integracao_experimental" in grupo,
            prefixo + "campo de ponto ausente.",
        )

        ponto = grupo["ponto_para_integracao_experimental"]
        situacao = grupo.get("situacao_integracao")
        classificacao = grupo.get("classificacao_geografica")

        exigir(
            classificacao in (
                None,
                "DENTRO_DO_CONTORNO",
                "FORA_DO_CONTORNO",
                "NA_BORDA_DO_CONTORNO",
            ),
            prefixo + "classificação geográfica inválida.",
        )

        if situacao == "CANDIDATO_EXPERIMENTAL":
            exigir(not motivos, prefixo + "candidato possui pendências.")
            exigir(bool(naturezas), prefixo + "candidato sem natureza.")
            exigir(len(datas) == 1, prefixo + "candidato com datas divergentes.")
            exigir(pontos == 1, prefixo + "candidato com pontos divergentes.")
            exigir(
                classificacao == "DENTRO_DO_CONTORNO",
                prefixo + "candidato não está dentro do contorno.",
            )
            exigir(
                isinstance(ponto, dict),
                prefixo + "ponto do candidato inválido.",
            )

            for campo, limite in (
                ("latitude", 90),
                ("longitude", 180),
            ):
                valor = ponto.get(campo)

                exigir(
                    type(valor) in (int, float),
                    prefixo + f"{campo} deve ser numérica.",
                )
                exigir(
                    math.isfinite(valor) and -limite <= valor <= limite,
                    prefixo + f"{campo} fora dos limites ou não finita.",
                )

            exigir(
                not (
                    ponto["latitude"] == 0
                    and ponto["longitude"] == 0
                ),
                prefixo + "ponto zero suspeito.",
            )

            candidatos += 1
            linhas_candidatos += quantidade

        elif situacao == "PENDENTE_REVISAO":
            exigir(bool(motivos), prefixo + "pendente sem motivo.")
            exigir(
                ponto is None,
                prefixo + "pendente não pode ter ponto para integração.",
            )
            pendentes += 1
            linhas_pendentes += quantidade

        else:
            raise ValueError(prefixo + "situação de integração inválida.")

    campos_resumo = (
        "linhas_municipio",
        "linhas_candidatas_antes_da_triagem",
        "grupos_provisorios_exportados",
        "grupos_candidatos_experimentais",
        "grupos_pendentes",
        "linhas_em_grupos_candidatos",
        "linhas_em_grupos_pendentes",
        "linhas_sem_identificacao_nao_exportadas",
    )

    for campo in campos_resumo:
        exigir(
            inteiro_nao_negativo(resumo.get(campo)),
            f"Resumo: campo inválido '{campo}'.",
        )

    esperados = {
        "grupos_provisorios_exportados": len(grupos),
        "grupos_candidatos_experimentais": candidatos,
        "grupos_pendentes": pendentes,
        "linhas_em_grupos_candidatos": linhas_candidatos,
        "linhas_em_grupos_pendentes": linhas_pendentes,
        "linhas_candidatas_antes_da_triagem": (
            linhas_candidatos
            + linhas_pendentes
            + resumo["linhas_sem_identificacao_nao_exportadas"]
        ),
    }

    for campo, esperado in esperados.items():
        exigir(
            resumo[campo] == esperado,
            f"Resumo inconsistente: '{campo}'.",
        )

    exigir(
        resumo["linhas_municipio"]
        >= resumo["linhas_candidatas_antes_da_triagem"],
        "O total municipal é menor que o total de linhas candidatas.",
    )

    return base


def rejeitar_constante_json(valor):
    raise ValueError(f"Constante numérica inválida no JSON: {valor}")


def carregar_base_seguranca(caminho):
    """Lê o arquivo e devolve a base somente após a validação."""
    try:
        with Path(caminho).open("r", encoding="utf-8-sig") as arquivo:
            base = json.load(
                arquivo,
                parse_constant=rejeitar_constante_json,
            )
    except FileNotFoundError as erro:
        raise ValueError("Arquivo da base não encontrado.") from erro
    except json.JSONDecodeError as erro:
        raise ValueError("O arquivo contém JSON malformado.") from erro
    except UnicodeDecodeError as erro:
        raise ValueError("O arquivo não está em UTF-8 válido.") from erro
    except OSError as erro:
        raise ValueError("Não foi possível ler o arquivo da base.") from erro

    return validar_base_seguranca(base)


def selecionar_candidatos(base, *, permitir_experimental=False):
    """
    Seleciona candidatos sem incluir os grupos pendentes.

    O uso experimental precisa ser explicitamente permitido.
    Não confirma atualidade na data de uso nem segurança da rota.
    """
    validar_base_seguranca(base)

    if permitir_experimental is not True:
        raise ValueError(
            "Base experimental: seleção bloqueada. "
            "Para testes, use permitir_experimental=True."
        )

    return [
        grupo
        for grupo in base["grupos"]
        if grupo["situacao_integracao"] == "CANDIDATO_EXPERIMENTAL"
    ]