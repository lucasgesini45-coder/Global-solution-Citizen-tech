import unittest

from backend.src.rotas.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
    Perfil,
    Rota,
)
from backend.src.rotas.ranking import motivo_inviabilidade


class TestesRestricoesAcessibilidade(unittest.TestCase):
    def criar_rota(self, status):
        # Rota mínima para testar somente a regra de acessibilidade.
        return Rota(
            trechos=[],
            saida_s=0,
            chegada_s=600,
            acessibilidade=status,
        )

    def perfil_com_necessidade(self):
        return Perfil(
            acessibilidade=frozenset({"sem_degraus"})
        )

    def test_compativel_permitida(self):
        rota = self.criar_rota(ACESS_COMPATIVEL)

        resultado = motivo_inviabilidade(
            rota,
            self.perfil_com_necessidade(),
        )

        self.assertIsNone(resultado)

    def test_incompativel_bloqueada(self):
        rota = self.criar_rota(ACESS_INCOMPATIVEL)

        resultado = motivo_inviabilidade(
            rota,
            self.perfil_com_necessidade(),
        )

        self.assertEqual(
            resultado,
            "acessibilidade_incompativel",
        )

    def test_nao_verificada_bloqueada(self):
        rota = self.criar_rota(ACESS_NAO_VERIFICADA)

        resultado = motivo_inviabilidade(
            rota,
            self.perfil_com_necessidade(),
        )

        self.assertEqual(
            resultado,
            "acessibilidade_nao_confirmada",
        )

    def test_status_nao_solicitada_nao_ignora_necessidade(self):
        rota = self.criar_rota(ACESS_NAO_SOLICITADA)

        resultado = motivo_inviabilidade(
            rota,
            self.perfil_com_necessidade(),
        )

        self.assertEqual(
            resultado,
            "acessibilidade_nao_confirmada",
        )

    def test_sem_necessidade_nao_exige_confirmacao(self):
        rota = self.criar_rota(ACESS_NAO_VERIFICADA)
        perfil = Perfil()

        resultado = motivo_inviabilidade(rota, perfil)

        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main(verbosity=2)