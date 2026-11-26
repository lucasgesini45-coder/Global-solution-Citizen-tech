import json
import tempfile
import unittest

from datetime import date
from pathlib import Path

from backend.src.analise_rota import analisar_rota_experimental
from backend.tests.teste_base_seguranca import criar_base_simulada


class TestesAnaliseRota(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)

        self.caminho = Path(self.pasta.name) / "base.json"

        self.base = criar_base_simulada()
        self.base["contexto"]["maior_data_registro_encontrada"] = (
            "2026-11-24"
        )

        self.trechos = [
            {
                "id": "T1",
                "tipo": "CAMINHADA",
                "trajeto": [
                    (-23.549, -46.63),
                    (-23.55, -46.63),
                ],
            },
            {
                "id": "T2",
                "tipo": "EMBARQUE",
                "ponto": {
                    "latitude": -23.55,
                    "longitude": -46.63,
                },
            },
        ]

        self.salvar_base()

    def salvar_base(self):
        self.caminho.write_text(
            json.dumps(self.base),
            encoding="utf-8",
        )

    def analisar(self, data_uso=date(2026, 11, 24)):
        return analisar_rota_experimental(
            self.caminho,
            self.trechos,
            data_uso,
            raio_metros=100,
            permitir_experimental=True,
        )

    def test_fluxo_completo(self):
        resultado = self.analisar()

        self.assertEqual(
            resultado["situacao_consulta"],
            "GRUPOS_PROXIMOS_ENCONTRADOS",
        )
        self.assertEqual(
            resultado["proximidade_rota"]["quantidade_grupos_distintos"],
            1,
        )
        self.assertEqual(
            resultado["proximidade_rota"][
                "quantidade_associacoes_grupo_trecho"
            ],
            2,
        )

    def test_pendentes_ficam_fora(self):
        resultado = self.analisar()

        ids = [
            grupo["id_exportacao"]
            for grupo in resultado["proximidade_rota"]["grupos_distintos"]
        ]

        self.assertEqual(ids, ["G000001"])

    def test_uso_experimental_bloqueado_por_padrao(self):
        with self.assertRaises(ValueError):
            analisar_rota_experimental(
                self.caminho,
                self.trechos,
                date(2026, 11, 24),
            )

    def test_base_invalida_bloqueada(self):
        self.base["resumo"]["grupos_provisorios_exportados"] = 999
        self.salvar_base()

        with self.assertRaises(ValueError):
            self.analisar()

    def test_sem_candidatos_apos_envelhecimento(self):
        resultado = self.analisar(date(2027, 3, 1))

        self.assertEqual(
            resultado["situacao_consulta"],
            "SEM_CANDIDATOS_ELEGIVEIS",
        )
        self.assertEqual(
            resultado["proximidade_rota"]["quantidade_grupos_distintos"],
            0,
        )

    def test_candidato_elegivel_mas_distante(self):
        self.base["grupos"][0][
            "ponto_para_integracao_experimental"
        ] = {
            "latitude": -23.60,
            "longitude": -46.63,
        }
        self.salvar_base()

        resultado = self.analisar()

        self.assertEqual(
            resultado["situacao_consulta"],
            "SEM_GRUPOS_PROXIMOS",
        )
        self.assertEqual(
            resultado["avaliacao_temporal"]["resumo"][
                "candidatos_elegiveis_na_data"
            ],
            1,
        )

    def test_nao_calcula_pontuacao(self):
        resultado = self.analisar()

        self.assertIsNone(resultado["pontuacao_seguranca"])
        self.assertEqual(resultado["situacao"], "EXPERIMENTAL")
        self.assertTrue(resultado["limitacoes"])

    def test_arquivo_original_preservado(self):
        antes = self.caminho.read_bytes()

        self.analisar()

        self.assertEqual(self.caminho.read_bytes(), antes)


if __name__ == "__main__":
    unittest.main(verbosity=2)