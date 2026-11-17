from backend.src.economia import estimar
from backend.src.transitous_api import etapas_completas


def test_tarifas_referencia_e_operadora_desconhecida():
    bus = {"modal": "BUS", "linha": "875A-10", "operadora": "SPTrans"}
    rail = {"modal":"SUBWAY","linha":"Linha 1 – Azul","operadora":"Metrô"}
    assert estimar([bus,rail])["centavos"] == 1070
    assert estimar([bus,{"modal":"BUS","operadora":"Intermunicipal"}])["centavos"] is None
    assert estimar([{"modal":"WALK"}])["centavos"] == 0
    assert estimar([])["centavos"] is None


def test_tarifa_domingo_e_linha_especial():
    bus = {"modal":"BUS","operadora":"SPTrans","partida":"2026-11-22T12:00:00+00:00"}
    assert estimar([bus])["centavos"] == 0
    assert estimar([{"modal":"SUBWAY","operadora":"Metrô","linha":"Linha 17 – Ouro"}])["centavos"] is None


def test_etapas_sem_geometria_preservadas():
    etapas = etapas_completas({"legs":[
        {"mode":"WALK","from":{"name":"Origem"},"to":{"name":"Parada"}},
        {"mode":"BUS","routeShortName":"123","duration":600,"from":{"name":"Parada"},
         "to":{"name":"Destino"},"startTime":"2026-11-17T13:00:00-03:00",
         "endTime":"2026-11-17T13:10:00-03:00"}
    ]})
    assert len(etapas)==2
    assert etapas[0]["tempo_min"] is None
    assert etapas[1]["partida"]=="2026-11-17T16:00:00+00:00"
    assert etapas[1]["tempo_min"]==10
