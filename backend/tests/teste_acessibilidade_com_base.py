import unittest
from datetime import date
from pathlib import Path

from backend.src.acessibilidade_com_base import (
    criar_verificador_com_base,
)
from backend.src.base_acessibilidade import (
    carregar_base_acessibilidade,
)
from backend.src.rotas.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_VERIFICADA,
    Rota,
    Trecho,
)


class TestesAcessibilidadeComBase(unittest.TestCase):
    def setUp(self):
        caminho = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "acessibilidade_simulada.json"
        )

        self.base = carregar_base_acessibilidade(caminho)

        # Associações exclusivas desta pequena rede fictícia.
        # Não representam ruas, paradas ou linhas reais.
        self.associacoes = {
            ("caminhada", "A", "B"): "TRECHO_SIMULADO_01",
            ("caminhada", "B", "C"): "TRECHO_SIMULADO_02",
            ("caminhada", "C", "D"): "TRECHO_SIMULADO_03",
        }

    def identificar(self, trecho):
        chave = (trecho.tipo, trecho.de, trecho.para)
        return self.associacoes.get(chave)

    def criar_rota(self, pares):
        trechos = []

        for numero, (origem, destino) in enumerate(pares):
            trechos.append(
                Trecho(
                    tipo="caminhada",
                    inicio_s=numero * 60,
                    fim_s=(numero + 1) * 60,
                    de=origem,
                    para=destino,
                )
            )

        return Rota(
            trechos=trechos,
            saida_s=0,
            chegada_s=len(trechos) * 60,
        )

    def avaliar(self, pares, data_consulta=None):
        if data_consulta is None:
            data_consulta = date(2026, 11, 27)

        verificar = criar_verificador_com_base(
            self.base,
            self.identificar,
            data_consulta,
            permitir_simulada=True,
        )

        return verificar(
            self.criar_rota(pares),
            frozenset({"sem_degraus"}),
        )

    def test_passagem_valida(self):
        self.assertEqual(
            self.avaliar([("A", "B")]),
            ACESS_COMPATIVEL,
        )

    def test_barreira_na_rota(self):
        self.assertEqual(
            self.avaliar([("A", "B"), ("B", "C")]),
            ACESS_INCOMPATIVEL,
        )

    def test_informacao_ausente(self):
        self.assertEqual(
            self.avaliar([("C", "D")]),
            ACESS_NAO_VERIFICADA,
        )

    def test_trecho_sem_associacao(self):
        self.assertEqual(
            self.avaliar([("X", "Y")]),
            ACESS_NAO_VERIFICADA,
        )

    def test_nao_reutiliza_associacao_no_sentido_inverso(self):
        self.assertEqual(
            self.avaliar([("B", "A")]),
            ACESS_NAO_VERIFICADA,
        )

    def test_informacao_vencida(self):
        self.assertEqual(
            self.avaliar(
                [("A", "B")],
                date(2026, 12, 5),
            ),
            ACESS_NAO_VERIFICADA,
        )

    def test_barreira_prevalece_sobre_trecho_desconhecido(self):
        self.assertEqual(
            self.avaliar([("B", "C"), ("X", "Y")]),
            ACESS_INCOMPATIVEL,
        )

    def test_identificador_inexistente_na_base(self):
        self.associacoes[("caminhada", "A", "B")] = "INEXISTENTE"

        self.assertEqual(
            self.avaliar([("A", "B")]),
            ACESS_NAO_VERIFICADA,
        )

    def test_base_simulada_bloqueada_por_padrao(self):
        with self.assertRaises(ValueError):
            criar_verificador_com_base(
                self.base,
                self.identificar,
                date(2026, 11, 27),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)