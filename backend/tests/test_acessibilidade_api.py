"""Contratos de acessibilidade: conteúdo simulado nunca é prova de rota segura."""
import unittest
from fastapi.testclient import TestClient
from backend.src.api import app

client = TestClient(app)


class AcessibilidadeApiTeste(unittest.TestCase):
    def test_rota_sem_evidencia_nao_e_verificada(self):
        r = client.post("/acessibilidade/avaliar", json={
            "trechos": [{"id": "1", "descricao": "Estação", "passagem_sem_degraus": None}],
            "precisa_sem_degraus": True,
        })
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "NAO_VERIFICADA")
        self.assertFalse(body["verificacao_em_campo"])

    def test_rota_com_barreira_documentada(self):
        r = client.post("/acessibilidade/avaliar", json={
            "trechos": [{"id": "1", "descricao": "Escada", "passagem_sem_degraus": False}],
            "precisa_sem_degraus": True,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "INCOMPATIVEL")

    def test_rota_real_expoe_preferencia_sem_garantia(self):
        from unittest.mock import patch
        from backend.src.enderecos_api import rota_real, Coordenadas, RotaRealPedido
        fake = {"tipo": "rota_real", "trechos": [], "aviso": "Teste"}
        with patch("backend.src.transitous_api.consultar_transitous", return_value=fake) as transit:
            pedido = RotaRealPedido(
                origem=Coordenadas(lat=-23.55, lon=-46.63),
                destino=Coordenadas(lat=-23.56, lon=-46.64),
                modal="ferroviario",
                evitar_escadas=True,
                priorizar_menos_caminhada=True,
            )
            result = rota_real(pedido)
        self.assertEqual(result["acessibilidade"]["status"], "NAO_VERIFICADA")
        self.assertTrue(result["acessibilidade"]["solicitou_sem_degraus"])
        self.assertTrue(transit.call_args.kwargs["priorizar_menos_caminhada"])
