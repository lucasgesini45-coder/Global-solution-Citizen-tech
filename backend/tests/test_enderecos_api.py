"""Testes dos contratos da API de endereços e caminhada."""
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from backend.src.enderecos_api import Coordenadas, RotaRealPedido, sugestoes, rota_real

class EnderecosTestes(unittest.TestCase):
    def test_busca_apresenta_resultados(self):
        fake=[{"nome":"Rua Maracá, São Paulo","lat":-23.55,"lon":-46.64,"fonte":"OpenStreetMap/Photon"}]
        with patch("backend.src.enderecos_api._buscar_cache",return_value=fake):
            resposta=sugestoes("Rua Maraca 270")
        self.assertEqual(resposta["resultados"][0]["nome"],fake[0]["nome"])

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
