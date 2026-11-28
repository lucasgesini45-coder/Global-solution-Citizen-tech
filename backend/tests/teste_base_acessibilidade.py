import copy
import unittest
from datetime import date
from pathlib import Path

from backend.src.base_acessibilidade import (
    carregar_base_acessibilidade,
    consultar_acessibilidade,
    validar_base_acessibilidade,
)


class TestesBaseAcessibilidade(unittest.TestCase):
    def setUp(self):
        caminho = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "acessibilidade_simulada.json"
        )

        self.base = carregar_base_acessibilidade(caminho)
        self.data = date(2026, 11, 27)

    def consultar(self, identificador, data=None):
        return consultar_acessibilidade(
            self.base,
            identificador,
            self.data if data is None else data,
        )

    def test_passagem_informada(self):
        resultado = self.consultar("TRECHO_SIMULADO_01")

        self.assertIs(resultado["passagem_sem_degraus"], True)
        self.assertEqual(
            resultado["motivo"],
            "INFORMACAO_DENTRO_DA_VALIDADE",
        )

    def test_barreira_preservada(self):
        resultado = self.consultar("TRECHO_SIMULADO_02")

        self.assertIs(resultado["passagem_sem_degraus"], False)

    def test_informacao_ausente(self):
        resultado = self.consultar("TRECHO_SIMULADO_03")

        self.assertIsNone(resultado["passagem_sem_degraus"])
        self.assertEqual(resultado["motivo"], "INFORMACAO_AUSENTE")

    def test_trecho_nao_encontrado(self):
        resultado = self.consultar("INEXISTENTE")

        self.assertIsNone(resultado["passagem_sem_degraus"])
        self.assertEqual(
            resultado["motivo"],
            "TRECHO_NAO_ENCONTRADO",
        )

    def test_ultimo_dia_da_validade(self):
        resultado = self.consultar(
            "TRECHO_SIMULADO_01",
            date(2026, 12, 4),
        )

        self.assertIs(resultado["passagem_sem_degraus"], True)

    def test_informacao_vencida(self):
        for identificador in (
            "TRECHO_SIMULADO_01",
            "TRECHO_SIMULADO_02",
        ):
            with self.subTest(trecho=identificador):
                resultado = self.consultar(
                    identificador,
                    date(2026, 12, 5),
                )

                self.assertIsNone(
                    resultado["passagem_sem_degraus"]
                )
                self.assertEqual(
                    resultado["motivo"],
                    "INFORMACAO_VENCIDA",
                )

    def test_verificacao_futura(self):
        resultado = self.consultar(
            "TRECHO_SIMULADO_01",
            date(2026, 11, 26),
        )

        self.assertIsNone(resultado["passagem_sem_degraus"])
        self.assertEqual(
            resultado["motivo"],
            "VERIFICACAO_FUTURA",
        )

    def test_identificador_repetido(self):
        self.base["registros"].append(
            copy.deepcopy(self.base["registros"][0])
        )

        with self.assertRaises(ValueError):
            validar_base_acessibilidade(self.base)

    def test_condicao_sem_fonte(self):
        self.base["registros"][0]["fonte"] = None

        with self.assertRaises(ValueError):
            validar_base_acessibilidade(self.base)

    def test_validade_anterior_a_verificacao(self):
        self.base["registros"][0]["valido_ate"] = "2026-11-26"

        with self.assertRaises(ValueError):
            validar_base_acessibilidade(self.base)

    def test_numero_nao_e_booleano(self):
        self.base["registros"][0]["passagem_sem_degraus"] = 1

        with self.assertRaises(ValueError):
            validar_base_acessibilidade(self.base)

    def test_consulta_nao_altera_base(self):
        original = copy.deepcopy(self.base)

        self.consultar(
            "TRECHO_SIMULADO_01",
            date(2026, 12, 5),
        )

        self.assertEqual(self.base, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)