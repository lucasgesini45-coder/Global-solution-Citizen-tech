import unittest

from backend.src.integracao_acessibilidade import (
    criar_verificador_acessibilidade,
)
from backend.src.rotas.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
    Rota,
    Trecho,
)


class TestesIntegracaoAcessibilidade(unittest.TestCase):
    def criar_rota(self, quantidade):
        trechos = []

        for numero in range(quantidade):
            trechos.append(
                Trecho(
                    tipo="caminhada",
                    inicio_s=numero * 60,
                    fim_s=(numero + 1) * 60,
                    de=f"P{numero}",
                    para=f"P{numero + 1}",
                )
            )

        return Rota(
            trechos=trechos,
            saida_s=0,
            chegada_s=quantidade * 60,
        )

    def avaliar(self, valores, necessidades=None):
        if necessidades is None:
            necessidades = frozenset({"sem_degraus"})

        rota = self.criar_rota(len(valores))

        # Dados simulados associados ao início de cada trecho.
        dados = {
            f"P{numero}": valor
            for numero, valor in enumerate(valores)
        }

        def consultar_passagem(trecho):
            return dados.get(trecho.de)

        verificar = criar_verificador_acessibilidade(
            consultar_passagem
        )

        return verificar(rota, necessidades)

    def test_todos_os_trechos_compativeis(self):
        self.assertEqual(
            self.avaliar([True, True]),
            ACESS_COMPATIVEL,
        )

    def test_barreira_prevalece_sobre_ausencia(self):
        self.assertEqual(
            self.avaliar([False, None]),
            ACESS_INCOMPATIVEL,
        )

    def test_informacao_ausente(self):
        self.assertEqual(
            self.avaliar([True, None]),
            ACESS_NAO_VERIFICADA,
        )

    def test_dado_invalido_nao_confirma_acessibilidade(self):
        self.assertEqual(
            self.avaliar([True, "sim"]),
            ACESS_NAO_VERIFICADA,
        )

    def test_rota_vazia(self):
        self.assertEqual(
            self.avaliar([]),
            ACESS_NAO_VERIFICADA,
        )

    def test_sem_necessidade(self):
        self.assertEqual(
            self.avaliar([None], frozenset()),
            ACESS_NAO_SOLICITADA,
        )

    def test_requisito_adicional_nao_e_confirmado(self):
        necessidades = frozenset({
            "sem_degraus",
            "orientacao_visual",
        })

        self.assertEqual(
            self.avaliar([True], necessidades),
            ACESS_NAO_VERIFICADA,
        )

    def test_requisito_nao_suportado(self):
        self.assertEqual(
            self.avaliar(
                [True],
                frozenset({"orientacao_visual"}),
            ),
            ACESS_NAO_VERIFICADA,
        )

    def test_consulta_ausente(self):
        with self.assertRaises(ValueError):
            criar_verificador_acessibilidade(None)


if __name__ == "__main__":
    unittest.main(verbosity=2)