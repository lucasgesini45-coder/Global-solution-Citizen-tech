import copy
import unittest

from datetime import date, timedelta

from backend.src.atualidade_base import selecionar_candidatos_na_data
from backend.tests.teste_base_seguranca import criar_base_simulada


class TestesAtualidadeBase(unittest.TestCase):

    def setUp(self):
        self.base = criar_base_simulada()
        self.data_consulta = date(2026, 11, 24)

        # O candidato tem exatamente 90 dias na consulta.
        data_fato = self.data_consulta - timedelta(days=90)

        self.base["grupos"][0]["datas_fato"] = [
            data_fato.isoformat()
        ]
        self.base["contexto"]["maior_data_registro_encontrada"] = (
            self.data_consulta.isoformat()
        )

    def avaliar(self, data_uso):
        return selecionar_candidatos_na_data(
            self.base,
            data_uso,
            permitir_experimental=True,
        )

    def test_exatamente_90_dias_permanece(self):
        resultado = self.avaliar(self.data_consulta)

        self.assertEqual(
            resultado["resumo"]["candidatos_elegiveis_na_data"],
            1,
        )

    def test_91_dias_sai_da_janela(self):
        resultado = self.avaliar(
            self.data_consulta + timedelta(days=1)
        )

        self.assertEqual(resultado["candidatos"], [])
        self.assertEqual(
            resultado["excluidos_por_idade"][0]["idade_dias"],
            91,
        )

    def test_pendente_nao_entra_na_selecao(self):
        resultado = self.avaliar(self.data_consulta)

        ids = [
            grupo["id_exportacao"]
            for grupo in resultado["candidatos"]
        ]

        self.assertEqual(ids, ["G000001"])
        self.assertEqual(
            resultado["resumo"]["grupos_pendentes_na_base"],
            1,
        )

    def test_data_anterior_a_consulta_bloqueada(self):
        with self.assertRaises(ValueError):
            self.avaliar(
                self.data_consulta - timedelta(days=1)
            )

    def test_uso_experimental_bloqueado_por_padrao(self):
        with self.assertRaises(ValueError):
            selecionar_candidatos_na_data(
                self.base,
                self.data_consulta,
            )

    def test_defasagem_do_ultimo_registro(self):
        resultado = self.avaliar(
            self.data_consulta + timedelta(days=10)
        )

        self.assertEqual(
            resultado["cobertura_temporal"]["dias_desde_ultimo_registro"],
            10,
        )
        self.assertFalse(
            resultado["cobertura_temporal"]["atualizacao_da_fonte_confirmada"]
        )

    def test_sem_data_do_ultimo_registro(self):
        del self.base["contexto"]["maior_data_registro_encontrada"]

        resultado = self.avaliar(self.data_consulta)

        self.assertEqual(
            resultado["cobertura_temporal"]["situacao"],
            "SEM_DATA_DE_REGISTRO",
        )
        self.assertIsNone(
            resultado["cobertura_temporal"]["dias_desde_ultimo_registro"]
        )

    def test_registro_posterior_a_consulta_sinalizado(self):
        self.base["contexto"]["maior_data_registro_encontrada"] = (
            self.data_consulta + timedelta(days=1)
        ).isoformat()

        resultado = self.avaliar(self.data_consulta)

        self.assertEqual(
            resultado["cobertura_temporal"]["situacao"],
            "DATA_DE_REGISTRO_INCONSISTENTE",
        )

    def test_base_original_nao_alterada(self):
        original = copy.deepcopy(self.base)

        self.avaliar(
            self.data_consulta + timedelta(days=1)
        )

        self.assertEqual(self.base, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)