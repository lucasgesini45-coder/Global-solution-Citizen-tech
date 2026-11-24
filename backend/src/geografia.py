import math

from shapely.geometry import Point


def validar_coordenadas(latitude, longitude):
    """
    Valida coordenadas numéricas em graus.

    Não confirma o sistema de referência, a precisão
    nem a localização dentro de um município.
    """
    for nome, valor, limite in (
        ("latitude", latitude, 90),
        ("longitude", longitude, 180),
    ):
        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
        ):
            raise ValueError(f"{nome} deve ser um número.")

        if not math.isfinite(valor):
            raise ValueError(f"{nome} deve ser finita.")

        if not -limite <= valor <= limite:
            raise ValueError(f"{nome} está fora dos limites.")


def validar_contorno(contorno):
    """Verifica se o contorno é uma geometria poligonal válida."""
    if getattr(contorno, "geom_type", None) not in (
        "Polygon",
        "MultiPolygon",
    ):
        raise ValueError("O contorno deve ser Polygon ou MultiPolygon.")

    if contorno.is_empty:
        raise ValueError("O contorno está vazio.")

    if not contorno.is_valid:
        raise ValueError("O contorno possui geometria inválida.")


def classificar_ponto_no_contorno(latitude, longitude, contorno):
    """
    Classifica um ponto em relação ao contorno.

    Pressupõe que ponto e contorno estejam em referências
    espaciais compatíveis, com longitude/latitude em graus.
    Não realiza transformação de coordenadas.
    """
    validar_coordenadas(latitude, longitude)
    validar_contorno(contorno)

    ponto = Point(longitude, latitude)

    if contorno.contains(ponto):
        return "DENTRO_DO_CONTORNO"

    if contorno.touches(ponto):
        return "NA_BORDA_DO_CONTORNO"

    return "FORA_DO_CONTORNO"


def calcular_distancia_metros(ponto_a, ponto_b):
    """
    Calcula a distância aproximada pela fórmula de Haversine.

    Os pontos devem conter (latitude, longitude), em graus.
    Usa uma Terra esférica e não calcula distância por ruas.
    """
    for ponto in (ponto_a, ponto_b):
        if not isinstance(ponto, (tuple, list)) or len(ponto) != 2:
            raise ValueError(
                "Cada ponto deve conter latitude e longitude."
            )

        validar_coordenadas(ponto[0], ponto[1])

    latitude_a, longitude_a = map(math.radians, ponto_a)
    latitude_b, longitude_b = map(math.radians, ponto_b)

    diferenca_latitude = latitude_b - latitude_a
    diferenca_longitude = longitude_b - longitude_a

    valor = (
        math.sin(diferenca_latitude / 2) ** 2
        + math.cos(latitude_a)
        * math.cos(latitude_b)
        * math.sin(diferenca_longitude / 2) ** 2
    )

    valor = min(1.0, max(0.0, valor))

    angulo = 2 * math.atan2(
        math.sqrt(valor),
        math.sqrt(1 - valor),
    )

    return 6_371_000 * angulo