import math

from backend.src.geografia import (
    calcular_distancia_metros,
    validar_coordenadas,
)


def buscar_grupos_proximos(
    latitude,
    longitude,
    candidatos,
    raio_metros=200,
):
    """
    Consulta grupos próximos de um ponto.

    Recebe candidatos já validados e reavaliados temporalmente.
    Não calcula risco, segurança ou distância por ruas.

    Cada identificador de grupo é contado uma única vez.
    """
    validar_coordenadas(latitude, longitude)

    if (
        type(raio_metros) not in (int, float)
        or not math.isfinite(raio_metros)
        or raio_metros < 0
    ):
        raise ValueError(
            "O raio deve ser um número finito não negativo."
        )

    if not isinstance(candidatos, list):
        raise ValueError("Os candidatos devem ser uma lista.")

    identificadores = set()
    proximos = []

    for grupo in candidatos:
        if not isinstance(grupo, dict):
            raise ValueError("Cada grupo deve ser um dicionário.")

        identificador = grupo.get("id_exportacao")

        if (
            not isinstance(identificador, str)
            or not identificador.strip()
        ):
            raise ValueError("Grupo com identificador inválido.")

        # Rejeita repetições para não contar duas vezes o mesmo grupo.
        if identificador in identificadores:
            raise ValueError(
                f"Identificador repetido: {identificador}"
            )

        identificadores.add(identificador)

        if grupo.get("situacao_integracao") != "CANDIDATO_EXPERIMENTAL":
            raise ValueError(
                "A consulta aceita somente candidatos experimentais."
            )

        if grupo.get("motivos_pendencia") != []:
            raise ValueError("O candidato possui pendências.")

        if grupo.get("classificacao_geografica") != "DENTRO_DO_CONTORNO":
            raise ValueError("O candidato não está dentro do contorno.")

        ponto = grupo.get("ponto_para_integracao_experimental")

        if not isinstance(ponto, dict):
            raise ValueError("O candidato não possui ponto válido.")

        latitude_grupo = ponto.get("latitude")
        longitude_grupo = ponto.get("longitude")

        validar_coordenadas(latitude_grupo, longitude_grupo)

        distancia = calcular_distancia_metros(
            (latitude, longitude),
            (latitude_grupo, longitude_grupo),
        )

        # Compara antes de arredondar.
        if distancia <= raio_metros:
            proximos.append({
                "id_exportacao": identificador,
                "distancia_aproximada_m": distancia,
            })

    proximos.sort(
        key=lambda item: (
            item["distancia_aproximada_m"],
            item["id_exportacao"],
        )
    )

    return {
        "situacao": "EXPERIMENTAL",
        "ponto_consulta": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "raio_metros": raio_metros,
        "grupos_consultados": len(candidatos),
        "quantidade_grupos_proximos": len(proximos),
        "grupos_proximos": proximos,
        "limitacoes": [
            "Proximidade não equivale a risco ou segurança.",
            "Grupos provisórios não equivalem a ocorrências únicas.",
            "Distância aproximada sobre a superfície, não por ruas.",
            "A função não verifica novamente a idade dos fatos.",
            "Ausência de grupos próximos não significa local seguro.",
        ],
    }