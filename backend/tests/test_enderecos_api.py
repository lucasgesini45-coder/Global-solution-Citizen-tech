"""Testes dos contratos da API de endereços e caminhada."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from fastapi import HTTPException
from backend.src.enderecos_api import Coordenadas, RotaRealPedido, sugestoes, rota_real, _buscar_cache, _json_http

class EnderecosTestes(unittest.TestCase):
    def test_busca_apresenta_resultados(self):
        fake=[{"nome":"Rua Maracá, São Paulo","lat":-23.55,"lon":-46.64,"fonte":"OpenStreetMap/Photon"}]
        with patch("backend.src.enderecos_api._buscar_cache",return_value=fake):
            resposta=sugestoes("Rua Maraca 270")
        self.assertEqual(resposta["resultados"][0]["nome"],fake[0]["nome"])

    def test_consultas_sucessivas_nao_recebem_429(self):
        fake = [{"nome": "FIAP Aclimacao, Sao Paulo", "lat": -23.57,
                 "lon": -46.63, "fonte": "OpenStreetMap/Photon"}]
        with patch("backend.src.enderecos_api._buscar_cache", return_value=fake):
            self.assertEqual(len(sugestoes("FIAP Aclimacao")["resultados"]), 1)
            self.assertEqual(len(sugestoes("FIAP Aclimacao SP")["resultados"]), 1)

    def test_resultados_photon_filtram_area_e_repeticoes(self):
        valido = {"properties": {"name": "FIAP Aclimacao", "city": "Sao Paulo"},
                  "geometry": {"coordinates": [-46.63, -23.57]}}
        fora = {"properties": {"name": "Fora da regiao"},
                "geometry": {"coordinates": [-43.2, -22.9]}}
        _buscar_cache.cache_clear()
        with patch("backend.src.enderecos_api._json_http",
                   return_value={"features": [valido, valido, fora]}):
            resultados = _buscar_cache("teste coordenadas bairro")
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["nome"], "FIAP Aclimacao, Sao Paulo")
        _buscar_cache.cache_clear()

    def test_photon_limite_mostra_erro_especifico(self):
        erro = HTTPError("https://photon.komoot.io/api", 429, "rate limit", None, None)
        with patch("backend.src.enderecos_api.urlopen", side_effect=erro), patch("backend.src.enderecos_api.time.sleep"):
            with self.assertRaises(HTTPException) as e:
                _json_http("https://photon.komoot.io/api?q=teste")
        self.assertEqual(e.exception.status_code, 503)
        self.assertIn("limite", e.exception.detail)

    def test_photon_http_400_exibe_causa_sem_confundir_com_conexao(self):
        erro = HTTPError("https://photon.komoot.io/api", 400, "bad request", None, None)
        with patch("backend.src.enderecos_api.urlopen", side_effect=erro):
            with self.assertRaises(HTTPException) as e:
                _json_http("https://photon.komoot.io/api?q=teste")
        self.assertIn("HTTP 400", e.exception.detail)
        self.assertIn("rejeitou a busca", e.exception.detail)

    def test_photon_falha_conexao_mostra_diagnostico(self):
        with patch("backend.src.enderecos_api.urlopen", side_effect=URLError("sem rede")), patch("backend.src.enderecos_api.time.sleep"):
            with self.assertRaises(HTTPException) as e:
                _json_http("https://photon.komoot.io/api?q=teste")
        self.assertIn("conectar ao Photon", e.exception.detail)

    def test_busca_photon_nao_envia_idioma_incompativel(self):
        _buscar_cache.cache_clear()
        mock_resposta = {"features": [
            {"properties": {"name": "Avenida Paulista", "city": "São Paulo"},
             "geometry": {"coordinates": [-46.65, -23.56]}}
        ]}
        with patch("backend.src.enderecos_api._json_http", return_value=mock_resposta) as request:
            resposta = _buscar_cache("Avenida Paulista")
        url = request.call_args.args[0]
        self.assertIn("q=Avenida+Paulista", url)
        self.assertNotIn("lang=", url)
        self.assertNotIn("lat=", url)
        self.assertNotIn("lon=", url)
        self.assertEqual(len(resposta), 1)
        _buscar_cache.cache_clear()

    def test_modal_ferrovia_consulta_provedor_real(self):
        resposta = {"tipo": "rota_real", "modal": "ferroviario", "trechos": []}
        with patch("backend.src.transitous_api.consultar_transitous", return_value=resposta) as provedor:
            rota = rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
              destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ferroviario"))
        self.assertEqual(rota["modal"], "ferroviario")
        self.assertEqual(provedor.call_args.args[2], "ferroviario")

    def test_falha_transitous_sem_chave_ors_nao_finge_rota(self):
        with patch.dict("os.environ",{},clear=True), patch(
            "backend.src.transitous_api.consultar_transitous",
            side_effect=HTTPException(status_code=503, detail="Transitous indisponível")
        ):
            with self.assertRaises(HTTPException) as e:
                rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
                  destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ape"))
        self.assertEqual(e.exception.status_code,503)

    def test_transitous_decodifica_geometria_sem_reta_inventada(self):
        from backend.src.transitous_api import decodificar_polilinha, consultar_transitous
        geom = {"points": "vww|k@fj__xAhk@io@", "precision": 6, "length": 2}
        pontos = decodificar_polilinha(geom)
        self.assertEqual(len(pontos), 2)
        self.assertAlmostEqual(pontos[0][0], -23.556492)
        self.assertAlmostEqual(pontos[0][1], -46.661812)
        dados = {"itineraries": [
            {"duration": 1200, "legs": [
                {"mode": "WALK", "duration": 120, "legGeometry": {},
                 "from": {"name": "Casa"}, "to": {"name": "Parada"}},
                {"mode": "BUS", "displayName": "875A-10", "duration": 1080,
                 "from": {"name": "Parada"}, "to": {"name": "Destino"},
                 "legGeometry": geom}
            ]}
        ]}
        with patch("backend.src.transitous_api._json_http", return_value=dados) as http:
            rota = consultar_transitous(Coordenadas(lat=-23.556492,lon=-46.661812),
                         Coordenadas(lat=-23.557201,lon=-46.661039),"onibus")
        self.assertEqual(rota["trechos"][0]["linha"], "875A-10")
        self.assertEqual(rota["trechos"][0]["modal"], "BUS")
        self.assertEqual(rota["trajeto"], pontos)
        self.assertIsNone(rota["tarifa_centavos"])
        self.assertIn("transitModes=BUS", http.call_args.args[0])
        self.assertIn("maxDirectTime=0", http.call_args.args[0])
        self.assertNotIn("directModes=", http.call_args.args[0])

    def test_gps_tenta_busca_ampliada_quando_nao_acha_linha(self):
        from backend.src.transitous_api import consultar_transitous
        geom = {"points": "vww|k@fj__xAhk@io@", "precision": 6}
        dados = {"itineraries": [{"duration": 900, "legs": [
            {"mode": "SUBWAY", "duration": 900, "displayName": "Linha 2",
             "from": {"name": "Estação A"}, "to": {"name": "Estação B"},
             "legGeometry": geom}
        ]}]}
        with patch("backend.src.transitous_api._json_http",
                   side_effect=[{"itineraries": []}, dados]) as http:
            rota = consultar_transitous(Coordenadas(lat=-23.55, lon=-46.63),
                        Coordenadas(lat=-23.56, lon=-46.64), "ferroviario")
        self.assertEqual(http.call_count, 2)
        self.assertIn("radius=1000", http.call_args.args[0])
        self.assertIn("maxPreTransitTime=1800", http.call_args.args[0])
        self.assertIn("maxPostTransitTime=1800", http.call_args.args[0])
        self.assertTrue(rota["busca_ampliada"])
        self.assertIn("Busca ampliada", rota["aviso"])
        self.assertEqual(rota["trechos"][0]["modal"], "SUBWAY")

    def test_gps_sem_transporte_retorna_404_sem_inventar_linha(self):
        from backend.src.transitous_api import consultar_transitous
        with patch("backend.src.transitous_api._json_http",
                   return_value={"itineraries": []}) as http:
            with self.assertRaises(HTTPException) as e:
                consultar_transitous(Coordenadas(lat=-23.55, lon=-46.63),
                                    Coordenadas(lat=-23.56, lon=-46.64), "onibus")
        self.assertEqual(http.call_count, 2)
        self.assertEqual(e.exception.status_code, 404)

    def test_cores_oficiais_varginha_esmeralda_e_caminhada(self):
        from backend.src.transitous_api import identificar_linha, CORES_LINHAS
        linha, cor = identificar_linha({"mode": "SUBURBAN", "displayName": "METRÔ L9",
                                         "routeColor": "55AAAA"})
        self.assertEqual(linha, "Linha 9 – Esmeralda")
        self.assertEqual(cor, CORES_LINHAS[9][1])
        self.assertNotEqual(cor, "#5F6D7E")
        self.assertEqual(identificar_linha({"mode": "WALK", "routeColor": "008A72"}), (None, None))
        self.assertEqual(identificar_linha({"mode": "SUBWAY", "routeShortName": "L2"}), ("Linha 2 – Verde", CORES_LINHAS[2][1]))

    def test_onibus_prioriza_codigo_de_linha_para_embarque(self):
        from backend.src.transitous_api import identificar_linha
        nome, cor = identificar_linha({
            "mode": "BUS", "routeShortName": "875A-10",
            "displayName": "Ponto inicial - Terminal", "routeColor": "2468AC"
        })
        self.assertEqual(nome, "875A-10")
        self.assertEqual(cor, "#2468AC")

    def test_prioriza_alternativa_com_menos_caminhada(self):
        from backend.src.transitous_api import consultar_transitous
        geom = {"points": "vww|k@fj__xAhk@io@", "precision": 6}
        def viagem(tempo, caminhada):
            return {"duration": tempo * 60, "legs": [
                {"mode": "WALK", "distance": caminhada, "legGeometry": geom},
                {"mode": "SUBURBAN", "duration": 1200, "displayName": "METRO L9",
                 "legGeometry": geom, "from":{"name":"Varginha"}, "to":{"name":"Pinheiros"}}
            ]}
        with patch("backend.src.transitous_api._json_http", return_value={
            "itineraries": [viagem(55, 4000), viagem(65, 500)]
        }):
            rota = consultar_transitous(Coordenadas(lat=-23.55, lon=-46.63),
                         Coordenadas(lat=-23.56, lon=-46.64), "ferroviario")
        self.assertEqual(rota["tempo_min"], 65)
        self.assertEqual(rota["caminhada_m"], 500)
        self.assertFalse(rota["caminhada_longa"])
        self.assertEqual(rota["trechos"][1]["cor_linha"], "#008A72")

    def test_modo_ferroviario_nao_aceita_itinerario_so_onibus(self):
        from backend.src.transitous_api import consultar_transitous
        dados = {"itineraries":[{"duration":600,"legs":[
            {"mode":"BUS", "legGeometry":{"points":"vww|k@fj__xAhk@io@","precision":6}}
        ]}]}
        with patch("backend.src.transitous_api._json_http",return_value=dados):
            with self.assertRaises(HTTPException) as e:
                consultar_transitous(Coordenadas(lat=-23.55,lon=-46.63),
                                     Coordenadas(lat=-23.56,lon=-46.64),"ferroviario")
        self.assertEqual(e.exception.status_code,404)

    def test_caminhada_geojson(self):
        dados={"features":[{"geometry":{"coordinates":[[-46.63,-23.55],[-46.64,-23.56]]},
               "properties":{"summary":{"duration":900,"distance":1280}}}]}
        with patch.dict("os.environ",{"ORS_API_KEY":"chave-teste"}), patch("backend.src.transitous_api.consultar_transitous",side_effect=HTTPException(status_code=503,detail="off")), patch("backend.src.enderecos_api._json_http",return_value=dados):
            rota=rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
                 destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ape"))
        self.assertEqual(rota["tempo_min"],15)
        self.assertEqual(rota["tarifa_centavos"],0)
        self.assertEqual(rota["seguranca"]["status"],"nao_verificada")
        self.assertEqual(rota["trajeto"][0],[-23.55,-46.63])

if __name__=="__main__":
    unittest.main()
