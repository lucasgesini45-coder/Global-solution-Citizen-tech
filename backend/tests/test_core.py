import unittest
from backend.src.core import carregar, responder, termos, GRAFO

class TestCore(unittest.TestCase):
    def setUp(self):
        self.dados = carregar()
    def test_acento(self):
        self.assertEqual(termos("Cartão!"), {"cartao"})
    def test_vazia(self):
        self.assertEqual(responder("", self.dados)["status"], "entrada_invalida")
    def test_sem_verificacao(self):
        self.assertEqual(responder("Como solicitar gratuidade?", self.dados)["status"], "sem_resposta")
    def test_grafo(self):
        self.assertGreaterEqual(len(GRAFO["gratuidade"]), 3)
    def test_registro_verificado(self):
        registro = {"id":9,"tema":"gratuidade","perguntas":["gratuidade transporte"],"orientacao":"Exemplo","referencia":"Fonte exemplo","data_verificacao":"2026-11-09","status":"verificado"}
        self.assertEqual(responder("gratuidade transporte", [registro])["status"], "ok")

if __name__ == "__main__":
    unittest.main()
