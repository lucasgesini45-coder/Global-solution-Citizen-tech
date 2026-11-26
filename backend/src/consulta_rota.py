import math

from backend.src.proximidade import buscar_grupos_proximos
from backend.src.proximidade_trajeto import (
    buscar_grupos_proximos_do_trajeto,
)


def consultar_proximidade_rota(
    trechos,
    candidatos,
    raio_metros=200,
):
    """
    Reúne consultas de caminhadas e pontos de embarque.

    Recebe candidatos já validados e reavaliados temporalmente,
    provenientes de uma mesma exportação.

    Não calcula pontuação de segurança.
    """
    if not isinstance(trechos, list) or not trechos:
        raise ValueError(
            "A rota deve ser uma lista com pelo menos um trecho."
        )

    if (
        type(raio_metros) not in (int, float)
        or not math.isfinite(raio_metros)
        or not 0 <= raio_metros <= 2000
    ):
        raise ValueError(
            "O raio deve estar entre 0 e 2000 metros."
        )

    ids_trechos = set()

    # Valida a estrutura de todos os trechos antes das consultas.
    for trecho in trechos:
        if not isinstance(trecho, dict):
            raise ValueError("Cada trecho deve ser um dicionário.")

        identificador = trecho.get("id")

        if (
            not isinstance(identificador, str)
            or not identificador.strip()
        ):
            raise ValueError("Trecho com identificador inválido.")

        if identificador in ids_trechos:
            raise ValueError(
                f"Identificador de trecho repetido: {identificador}"
            )

        ids_trechos.add(identificador)

        tipo = trecho.get("tipo")

        if tipo == "CAMINHADA":
            if "trajeto" not in trecho:
                raise ValueError(
                    f"Trecho {identificador}: falta o trajeto."
                )

        elif tipo == "EMBARQUE":
            ponto = trecho.get("ponto")

            if not isinstance(ponto, dict):
                raise ValueError(
                    f"Trecho {identificador}: ponto inválido."
                )

            if "latitude" not in ponto or "longitude" not in ponto:
                raise ValueError(
                    f"Trecho {identificador}: faltam coordenadas."
                )

        else:
            raise ValueError(
                f"Trecho {identificador}: tipo não suportado."
            )

    resultados_trechos = []
    grupos_na_rota = {}
    total_associacoes = 0

    for trecho in trechos:
        identificador = trecho["id"]
        tipo = trecho["tipo"]

        if tipo == "CAMINHADA":
            consulta = buscar_grupos_proximos_do_trajeto(
                trecho["trajeto"],
                candidatos,
                raio_metros=raio_metros,
            )
            campo_distancia = "distancia_aproximada_trajeto_m"

        else:
            ponto = trecho["ponto"]

            consulta = buscar_grupos_proximos(
                ponto["latitude"],
                ponto["longitude"],
                candidatos,
                raio_metros=raio_metros,
            )
            campo_distancia = "distancia_aproximada_m"

        grupos_do_trecho = []

        for encontrado in consulta["grupos_proximos"]:
            id_grupo = encontrado["id_exportacao"]
            distancia = encontrado[campo_distancia]

            grupos_do_trecho.append({
                "id_exportacao": id_grupo,
                "distancia_aproximada_m": distancia,
            })

            if id_grupo not in grupos_na_rota:
                grupos_na_rota[id_grupo] = {
                    "id_exportacao": id_grupo,
                    "trechos_proximos": [],
                }

            # Preserva a distância de cada associação.
            # Os métodos de distância de ponto e trajeto são diferentes.
            grupos_na_rota[id_grupo]["trechos_proximos"].append({
                "id_trecho": identificador,
                "tipo": tipo,
                "distancia_aproximada_m": distancia,
            })

            total_associacoes += 1

        resultados_trechos.append({
            "id_trecho": identificador,
            "tipo": tipo,
            "quantidade_grupos_proximos": len(grupos_do_trecho),
            "grupos_proximos": grupos_do_trecho,
        })

    grupos_distintos = [
        grupos_na_rota[identificador]
        for identificador in sorted(grupos_na_rota)
    ]

    if total_associacoes != sum(
        trecho["quantidade_grupos_proximos"]
        for trecho in resultados_trechos
    ):
        raise ValueError("Contagem inconsistente das associações.")

    return {
        "situacao": "EXPERIMENTAL",
        "raio_metros": raio_metros,
        "quantidade_trechos": len(trechos),
        "quantidade_grupos_distintos": len(grupos_distintos),
        "quantidade_associacoes_grupo_trecho": total_associacoes,
        "trechos": resultados_trechos,
        "grupos_distintos": grupos_distintos,
        "limitacoes": [
            "Não calcula pontuação de risco ou segurança.",
            "A mesma identificação é contada uma vez no total da rota.",
            "Todos os candidatos devem vir da mesma exportação.",
            "A função não verifica novamente a idade dos fatos.",
            "Caminhadas precisam de uma geometria representativa.",
            "Não analisa deslocamentos dentro dos veículos.",
            "Distâncias são aproximadas e usam métodos distintos.",
            "Contagens brutas não permitem concluir qual rota é mais segura.",
            "Ausência de grupos próximos não significa ausência de risco.",
        ],
    }