import math

from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point

from backend.src.geografia import (
    calcular_distancia_metros,
    validar_coordenadas,
)
from backend.src.proximidade import buscar_grupos_proximos


def buscar_grupos_proximos_do_trajeto(
    trajeto,
    candidatos,
    raio_metros=200,
):
    """
    Consulta grupos próximos da linha que representa o trajeto.

    Cada vértice deve conter (latitude, longitude).
    Os candidatos devem estar previamente validados e
    reavaliados temporalmente.

    Cálculo experimental em projeção local, sem pontuação
    de risco ou garantia de segurança.
    """
    if not isinstance(trajeto, list) or len(trajeto) < 2:
        raise ValueError(
            "O trajeto deve ser uma lista com pelo menos dois pontos."
        )

    if (
        type(raio_metros) not in (int, float)
        or not math.isfinite(raio_metros)
        or not 0 <= raio_metros <= 2000
    ):
        raise ValueError(
            "Nesta etapa, o raio deve estar entre 0 e 2000 metros."
        )

    vertices = []

    for ponto in trajeto:
        if not isinstance(ponto, (tuple, list)) or len(ponto) != 2:
            raise ValueError(
                "Cada ponto do trajeto deve conter latitude e longitude."
            )

        latitude, longitude = ponto
        validar_coordenadas(latitude, longitude)

        # Ignora apenas repetições consecutivas de vértices.
        coordenada = (latitude, longitude)

        if not vertices or coordenada != vertices[-1]:
            vertices.append(coordenada)

    if len(set(vertices)) < 2:
        raise ValueError("O trajeto precisa de dois pontos distintos.")

    origem = vertices[0]
    latitude_origem, longitude_origem = origem

    for ponto in vertices:
        distancia = calcular_distancia_metros(origem, ponto)

        if distancia > 20_000:
            raise ValueError(
                "Trajeto fora do escopo local: "
                "há um vértice a mais de 20 km do primeiro ponto."
            )

    # Valida os candidatos e seleciona um entorno amplo.
    # O limite de 50 km é apenas um pré-filtro de processamento.
    # O raio solicitado será aplicado à linha do trajeto depois.
    consulta_ampla = buscar_grupos_proximos(
        latitude_origem,
        longitude_origem,
        candidatos,
        raio_metros=50_000,
    )

    ids_entorno = {
        item["id_exportacao"]
        for item in consulta_ampla["grupos_proximos"]
    }

    # Hipótese experimental: entrada em WGS 84.
    # A projeção local permite calcular distâncias em metros.
    projecao_local = CRS.from_proj4(
        f"+proj=aeqd "
        f"+lat_0={latitude_origem} "
        f"+lon_0={longitude_origem} "
        "+datum=WGS84 +units=m +no_defs"
    )

    transformador = Transformer.from_crs(
        "EPSG:4326",
        projecao_local,
        always_xy=True,
    )

    def projetar(latitude, longitude):
        x, y = transformador.transform(
            longitude,
            latitude,
            errcheck=True,
        )

        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("A projeção produziu coordenadas inválidas.")

        return x, y

    linha = LineString([
        projetar(latitude, longitude)
        for latitude, longitude in vertices
    ])

    if linha.is_empty or linha.length == 0:
        raise ValueError("O trajeto projetado não possui comprimento.")

    proximos = []

    for grupo in candidatos:
        identificador = grupo["id_exportacao"]

        if identificador not in ids_entorno:
            continue

        coordenadas = grupo["ponto_para_integracao_experimental"]

        ponto = Point(projetar(
            coordenadas["latitude"],
            coordenadas["longitude"],
        ))

        # Distância até qualquer parte da linha, incluindo seu meio.
        distancia = ponto.distance(linha)

        # Compara antes de arredondar.
        if distancia <= raio_metros:
            proximos.append({
                "id_exportacao": identificador,
                "distancia_aproximada_trajeto_m": distancia,
            })

    proximos.sort(
        key=lambda item: (
            item["distancia_aproximada_trajeto_m"],
            item["id_exportacao"],
        )
    )

    return {
        "situacao": "EXPERIMENTAL",
        "raio_metros": raio_metros,
        "quantidade_vertices": len(vertices),
        "comprimento_aproximado_trajeto_m": linha.length,
        "grupos_recebidos": len(candidatos),
        "grupos_no_entorno_de_processamento": len(ids_entorno),
        "quantidade_grupos_proximos": len(proximos),
        "grupos_proximos": proximos,
        "limitacoes": [
            "O trajeto conecta os vértices na ordem fornecida.",
            "A geometria precisa representar o caminho efetivamente usado.",
            "Distâncias aproximadas em projeção local.",
            "Pressupõe coordenadas compatíveis com WGS 84.",
            "Não verifica novamente a idade dos fatos.",
            "Proximidade não representa probabilidade de crime.",
            "Ausência de grupos próximos não significa trajeto seguro.",
        ],
    }