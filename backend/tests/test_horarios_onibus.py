from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from backend.src.transitous_api import horarios_onibus
from backend.src.horarios_api import ConsultaPartidas, proximas_partidas


def test_itinerario_preserva_onibus_sem_geometria_e_hora_ausente():
    dados = {"legs": [
        {"mode":"WALK"},
        {"mode":"BUS","routeShortName":"875A-10","realTime":False,
         "scheduledStartTime":"2026-11-17T13:30:00-03:00",
         "from":{"stopId":"a","name":"Embarque"},"to":{"stopId":"b","name":"Saída"}}]}
    h = horarios_onibus(dados)
    assert len(h) == 1
    assert h[0]["etapa"] == 2 and h[0]["ponto_id"] == "a"
    assert h[0]["partida"] == "2026-11-17T16:30:00+00:00"
    assert h[0]["chegada"] is None and not h[0]["tempo_real"]


def test_partidas_filtram_parada_linha_sentido_desembarque_e_cancelamentos():
    futuro = (datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
    evento = {"mode":"BUS","agencyId":"op","routeShortName":"875A","headsign":"Terminal",
              "place":{"stopId":"a","departure":futuro,"scheduledDeparture":futuro},
              "nextStops":[{"stopId":"b"}],"tripId":"1","realTime":True}
    pedido = ConsultaPartidas(ponto_id="a",codigo_linha="875A",operadora_id="op",
                              sentido="Terminal",desembarque_id="b")
    with patch("backend.src.horarios_api._json_http",return_value={"stopTimes":[evento,evento,
             {**evento,"tripId":"2","headsign":"Outro"},
             {**evento,"tripId":"3","cancelled":True},
             {**evento,"tripId":"4","nextStops":[{"stopId":"c"}]},
             {**evento,"tripId":"5","nextStops":[{"stopId":"b","dropoffType":"NOT_ALLOWED"}]}
             ]}) as http:
        r = proximas_partidas(pedido)
    assert len(r["partidas"]) == 1 and r["partidas"][0]["tempo_real"]
    assert "fetchStops=true" in http.call_args.args[0]
