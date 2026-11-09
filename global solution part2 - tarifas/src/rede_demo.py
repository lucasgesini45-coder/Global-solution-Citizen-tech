import math
from src.config import RAIO_TERRA_M
from src.contratos import Parada, Rede, Viagem

LAT0 = -23.5500
LON0 = -46.6300
M_POR_GRAU = RAIO_TERRA_M * math.pi / 180.0


def ponto(x_m: float, y_m: float) -> tuple[float, float]:
    lat = LAT0 + y_m / M_POR_GRAU
    lon = LON0 + x_m / (M_POR_GRAU * math.cos(math.radians(LAT0)))
    return (lat, lon)


def criar_rede_demo() -> Rede:
    dados_paradas = [
        ("MA", "Metrô Alfa", 0.0, 0.0),
        ("MB", "Metrô Beta", 2000.0, 0.0),
        ("MC", "Metrô Gama", 4000.0, 0.0),
        ("BA", "Ponto Alfa", 0.0, 100.0),
        ("BB", "Ponto Beta", 2000.0, 100.0),
        ("BC", "Ponto Gama", 4000.0, 100.0),
        ("BX", "Ponto Centro", 2000.0, 700.0),
        ("PD", "Ponto Destino", 4000.0, 300.0),
        ("PF", "Ponto Fim", 2000.0, 2000.0),
    ]

    paradas: dict[str, Parada] = {}
    for p_id, nome, x, y in dados_paradas:
        lat, lon = ponto(x, y)
        paradas[p_id] = Parada(id=p_id, nome=nome, lat=lat, lon=lon)

    linhas_def = [
        {
            "linha_id": "M1",
            "nome_linha": "Metrô Linha 1",
            "operador": "Metrô Demo",
            "modal": "metro",
            "paradas": ("MA", "MB", "MC"),
            "deslocamentos": (0, 300, 600),
            "primeira": 21600,
            "ultima": 88200,
            "intervalo": 600,
            "dias": frozenset(range(7)),
            "excecoes": frozenset(),
        },
        {
            "linha_id": "L100",
            "nome_linha": "Ônibus 100",
            "operador": "Ônibus Demo",
            "modal": "onibus",
            "paradas": ("BA", "BX", "BC"),
            "deslocamentos": (0, 900, 1500),
            "primeira": 21900,
            "ultima": 86000,
            "intervalo": 900,
            "dias": frozenset({0, 1, 2, 3, 4}),
            "excecoes": frozenset({"2026-11-20"}),
        },
        {
            "linha_id": "L200",
            "nome_linha": "Ônibus 200",
            "operador": "Ônibus Demo",
            "modal": "onibus",
            "paradas": ("BA", "BX", "PD"),
            "deslocamentos": (0, 1000, 1800),
            "primeira": 22000,
            "ultima": 86000,
            "intervalo": 1200,
            "dias": frozenset(range(7)),
            "excecoes": frozenset(),
        },
        {
            "linha_id": "L300",
            "nome_linha": "Ônibus 300",
            "operador": "Ônibus Demo",
            "modal": "onibus",
            "paradas": ("BB", "PF"),
            "deslocamentos": (0, 900),
            "primeira": 21660,
            "ultima": 86000,
            "intervalo": 600,
            "dias": frozenset(range(7)),
            "excecoes": frozenset(),
        },
    ]

    viagens: list[Viagem] = []
    for l_def in linhas_def:
        t = l_def["primeira"]
        n = 0
        while t <= l_def["ultima"]:
            horarios = tuple(t + d for d in l_def["deslocamentos"])
            v_id = f"{l_def['linha_id']}-{n:03d}"
            viagens.append(
                Viagem(
                    id=v_id,
                    linha_id=l_def["linha_id"],
                    nome_linha=l_def["nome_linha"],
                    operador=l_def["operador"],
                    modal=l_def["modal"],
                    sentido="ida",
                    paradas=l_def["paradas"],
                    horarios=horarios,
                    dias_semana=l_def["dias"],
                    excecoes=l_def["excecoes"],
                )
            )
            t += l_def["intervalo"]
            n += 1

    return Rede(
        paradas=paradas,
        viagens=viagens,
        versao="demo-1",
        origem_dados="simulado",
    )
