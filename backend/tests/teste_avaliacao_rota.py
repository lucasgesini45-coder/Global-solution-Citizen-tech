import json
import tempfile
import unittest

from datetime import date
from pathlib import Path

from backend.src.avaliacao_rota import avaliar_rota_integrada
from backend.tests.teste_base_seguranca import criar_base_simulada


class TestesAvaliacaoRota(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)

        self.caminho = Path(self.pasta.name) / "base.json"

        self.caminho.write_text(
            json.dumps(criar_base_simulada()),
            encoding="utf-8",
        )

        self.necessidades = {
            "precisa_sem_degraus": True,
        }

        self.trechos = [
            {
                "id": "T1",
                "descricao": "Caminhada simulada até o embarque",
                "tipo": "CAMINHADA",
                "passagem_sem_degraus": True,
                "trajeto": [
                    (-23.549, -46.63),
                    (-23.55, -46.63),
                ],
            },
            {
                "id": "T2",
                "descricao": "Embarque simulado",
                "tipo": "EMBARQUE",
                "passagem_sem_degraus": True,
                "ponto": {
                    "latitude": -23.55,
                    "longitude": -46.63,
                },
            },
        ]

    def avaliar(self):
        return avaliar_rota_integrada(
            self.caminho,
            self.trechos,
            self.necessidades,
            date(2026, 11, 24),
            raio_metros=100,
            permitir_experimental=True,
        )

    def test_rota_compativel_com_criterio(self):
        resultado = self.avaliar()

        self.assertEqual(
            resultado["acessibilidade"]["status"],
            "COMPATIVEL",
        )
        self.assertEqual(
            resultado["decisao_acessibilidade"],
            "ATENDE_AO_CRITERIO_SOLICITADO",
        )
        self.assertIsNotNone(resultado["analise_proximidade"])
        self.assertFalse(resultado["recomendacao_automatica"])

    def test_barreira_preservada_na_integracao(self):
        self.trechos[1]["passagem_sem_degraus"] = False

        resultado = self.avaliar()

        self.assertEqual(
            resultado["acessibilidade"]["status"],
            "INCOMPATIVEL",
        )
        self.assertEqual(
            resultado["acessibilidade"]["barreiras"],
            ["T2 - Embarque simulado"],
        )
        self.assertEqual(
            resultado["decisao_acessibilidade"],
            "NAO_ATENDE_AO_CRITERIO_SOLICITADO",
        )

    def test_informacao_ausente_nao_vira_compativel(self):
        self.trechos[1]["passagem_sem_degraus"] = None

        resultado = self.avaliar()

        self.assertEqual(
            resultado["acessibilidade"]["status"],
            "NAO_VERIFICADA",
        )
        self.assertEqual(
            resultado["decisao_acessibilidade"],
            "INFORMACAO_INSUFICIENTE",
        )

    def test_barreira_prevalece_sobre_informacao_ausente(self):
        self.trechos[0]["passagem_sem_degraus"] = False
        self.trechos[1]["passagem_sem_degraus"] = None

        resultado = self.avaliar()

        self.assertEqual(
            resultado["acessibilidade"]["status"],
            "INCOMPATIVEL",
        )
        self.assertEqual(
            len(resultado["acessibilidade"]["pendencias"]),
            1,
        )

    def test_criterio_nao_solicitado(self):
        self.necessidades["precisa_sem_degraus"] = False
        self.trechos[1]["passagem_sem_degraus"] = False

        resultado = self.avaliar()

        self.assertEqual(
            resultado["decisao_acessibilidade"],
            "CRITERIO_NAO_SOLICITADO",
        )

    def test_dados_invalidos_bloqueiam_consulta(self):
        self.trechos[1]["passagem_sem_degraus"] = "sim"

        resultado = self.avaliar()

        self.assertEqual(resultado["situacao"], "DADOS_INVALIDOS")
        self.assertIsNone(resultado["analise_proximidade"])
        self.assertTrue(resultado["acessibilidade"]["erros"])

    def test_rota_vazia(self):
        self.trechos = []

        resultado = self.avaliar()

        self.assertEqual(resultado["situacao"], "ROTA_SEM_TRECHOS")
        self.assertIsNone(resultado["analise_proximidade"])

    def test_grupos_contados_sem_duplicacao(self):
        resultado = self.avaliar()

        consulta = resultado["analise_proximidade"]["proximidade_rota"]

        self.assertEqual(consulta["quantidade_grupos_distintos"], 1)
        self.assertEqual(
            consulta["quantidade_associacoes_grupo_trecho"],
            2,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)