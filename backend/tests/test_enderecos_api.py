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

    def test_photon_falha_conexao_mostra_diagnostico(self):
        with patch("backend.src.enderecos_api.urlopen", side_effect=URLError("sem rede")), patch("backend.src.enderecos_api.time.sleep"):
            with self.assertRaises(HTTPException) as e:
                _json_http("https://photon.komoot.io/api?q=teste")
        self.assertIn("conectar ao Photon", e.exception.detail)

    def test_modal_ferrovia_nao_finge_suporte(self):
        with self.assertRaises(HTTPException) as e:
            rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
              destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ferroviario"))
        self.assertEqual(e.exception.status_code,422)

    def test_ausencia_chave_nao_finge_rota_real(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaises(HTTPException) as e:
                rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
                  destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ape"))
        self.assertEqual(e.exception.status_code,503)

    def test_caminhada_geojson(self):
        dados={"features":[{"geometry":{"coordinates":[[-46.63,-23.55],[-46.64,-23.56]]},
               "properties":{"summary":{"duration":900,"distance":1280}}}]}
        with patch.dict("os.environ",{"ORS_API_KEY":"chave-teste"}),patch("backend.src.enderecos_api._json_http",return_value=dados):
            rota=rota_real(RotaRealPedido(origem=Coordenadas(lat=-23.55,lon=-46.63),
                 destino=Coordenadas(lat=-23.56,lon=-46.64),modal="ape"))
        self.assertEqual(rota["tempo_min"],15)
        self.assertEqual(rota["tarifa_centavos"],0)
        self.assertEqual(rota["seguranca"]["status"],"nao_verificada")
        self.assertEqual(rota["trajeto"][0],[-23.55,-46.63])

if __name__=="__main__":
    unittest.main()
