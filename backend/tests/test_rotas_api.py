"""Testes do adaptador HTTP (sem depender de httpx ou rede externa)."""
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.src.api import app
from backend.src.rotas_api import PedidoRota, calcular_rotas
from src.rede_demo import ponto


class TestRotasAPI(unittest.TestCase):
    def setUp(self):
        origem = ponto(0.0, -100.0)
        destino = ponto(4000.0, 300.0)
        self.pedido = PedidoRota(
            origem={"lat": origem[0], "lon": origem[1]},
            destino={"lat": destino[0], "lon": destino[1]},
            partida="2026-11-09T08:00:00",
        )

    def test_endpoint_registrado(self):
        # openapi() funciona em qualquer versão do FastAPI (app.routes mudou nas versões novas)
        caminhos = app.openapi()["paths"]
        self.assertIn("/rotas", caminhos)
        self.assertIn("post", caminhos["/rotas"])

    def test_resposta_demonstrativa_real(self):
        resposta = calcular_rotas(self.pedido)
        self.assertEqual(resposta["modo"], "demonstracao")
        self.assertIn("ficticios", resposta["origem_dados"])
        self.assertIn("resultado", resposta)
        self.assertIn("rotas", resposta["resultado"])
        self.assertGreater(len(resposta["resultado"]["rotas"]), 0)
        primeira = resposta["resultado"]["rotas"][0]
        self.assertIn("tempo_total_min", primeira)
        self.assertIn("custo", primeira)
        self.assertIn("seguranca", primeira)
        self.assertIn("status", primeira["seguranca"])
        self.assertTrue(any("geometria" in t for t in primeira["trechos"]))

    def test_coordenadas_invalidas(self):
        with self.assertRaises(ValidationError):
            PedidoRota(
                origem={"lat": 100, "lon": 0},
                destino={"lat": 0, "lon": 0},
                partida="2026-11-09T08:00:00",
            )

    def test_repassa_necessidades_ao_motor(self):
        pedido = self.pedido.model_copy(
            update={"necessidades": {"perfil_tarifario": "estudante"}}
        )
        with patch("backend.src.rotas_api.processar_pedido", return_value={"rotas": []}) as func:
            resposta = calcular_rotas(pedido)
        self.assertEqual(func.call_args.args[0]["necessidades"]["perfil_tarifario"], "estudante")
        self.assertEqual(resposta["resultado"], {"rotas": []})


if __name__ == "__main__":
    unittest.main()
