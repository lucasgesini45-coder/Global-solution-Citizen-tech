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
                              sentido="Terminal",desembarque_id="b", dia=datetime.fromisoformat(futuro).astimezone(__import__("zoneinfo").ZoneInfo("America/Sao_Paulo")).date())
    with patch("backend.src.horarios_api._json_http",return_value={"stopTimes":[evento,evento,
             {**evento,"tripId":"2","headsign":"Outro"},
             {**evento,"tripId":"3","cancelled":True},
             {**evento,"tripId":"4","nextStops":[{"stopId":"c"}]},
             {**evento,"tripId":"5","nextStops":[{"stopId":"b","dropoffType":"NOT_ALLOWED"}]}
             ]}) as http:
        r = proximas_partidas(pedido)
    assert len(r["partidas"]) == 1 and r["partidas"][0]["tempo_real"]
    assert "fetchStops=true" in http.call_args.args[0]


def test_tabela_diaria_sem_limite_oito_e_proximo():
    from zoneinfo import ZoneInfo
    fuso = ZoneInfo("America/Sao_Paulo")
    agora = datetime(2026,11,17,12,0,tzinfo=fuso)
    eventos = []
    for i in range(20):
        partida = (agora.replace(hour=6)+timedelta(minutes=40*i)).isoformat()
        eventos.append({"mode":"BUS","agencyId":"op","routeShortName":"875A","headsign":"Terminal",
                       "place":{"stopId":"a","scheduledDeparture":partida},
                       "nextStops":[{"stopId":"b"}],"tripId":str(i),"realTime":False})
    pedido = ConsultaPartidas(ponto_id="a",codigo_linha="875A",operadora_id="op",
                             sentido="Terminal",desembarque_id="b",dia=agora.date())
    with patch("backend.src.horarios_api.datetime", wraps=datetime) as relogio, patch(
        "backend.src.horarios_api._json_http", return_value={"stopTimes":eventos[::-1]}) as http:
        relogio.now.return_value = agora.astimezone(timezone.utc)
        r = proximas_partidas(pedido)
    assert len(r["partidas"]) == 20
    assert r["proxima"]["partida"] == "2026-11-17T15:00:00+00:00"
    assert r["partidas"][0]["partida"] == "2026-11-17T09:00:00+00:00"
    assert "window=86400" in http.call_args.args[0]
