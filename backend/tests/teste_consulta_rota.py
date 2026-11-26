import copy
import unittest

from backend.src.consulta_rota import consultar_proximidade_rota


def criar_grupo(identificador, latitude, longitude):
    return {
        "id_exportacao": identificador,
        "situacao_integracao": "CANDIDATO_EXPERIMENTAL",
        "motivos_pendencia": [],
        "classificacao_geografica": "DENTRO_DO_CONTORNO",
        "ponto_para_integracao_experimental": {
            "latitude": latitude,
            "longitude": longitude,
        },
    }


class TestesConsultaRota(unittest.TestCase):

    def setUp(self):
        self.trechos = [
            {
                "id": "T1",
                "tipo": "CAMINHADA",
                "trajeto": [
                    (-23.55, -46.63),
                    (-23.56, -46.63),
                ],
            },
            {
                "id": "T2",
                "tipo": "EMBARQUE",
                "ponto": {
                    "latitude": -23.56,
                    "longitude": -46.63,
                },
            },
        ]

        # Este grupo está perto do final da caminhada
        # e também do embarque.
        self.grupos = [
            criar_grupo("G1", -23.56, -46.6299),
        ]

    def consultar(self):
        return consultar_proximidade_rota(
            self.trechos,
            self.grupos,
            raio_metros=100,
        )

    def test_grupo_contado_uma_vez_na_rota(self):
        resultado = self.consultar()

        self.assertEqual(
            resultado["quantidade_grupos_distintos"], 1
        )
        self.assertEqual(
            resultado["quantidade_associacoes_grupo_trecho"], 2
        )

    def test_preserva_os_trechos_associados(self):
        resultado = self.consultar()

        associacoes = resultado["grupos_distintos"][0][
            "trechos_proximos"
        ]

        self.assertEqual(
            [item["id_trecho"] for item in associacoes],
            ["T1", "T2"],
        )

    def test_resultado_individual_por_trecho(self):
        resultado = self.consultar()

        self.assertEqual(
            [
                trecho["quantidade_grupos_proximos"]
                for trecho in resultado["trechos"]
            ],
            [1, 1],
        )

    def test_dois_grupos_distintos(self):
        # Próximo apenas do começo da caminhada.
        self.grupos.append(
            criar_grupo("G2", -23.5501, -46.63)
        )

        resultado = self.consultar()

        self.assertEqual(
            resultado["quantidade_grupos_distintos"], 2
        )
        self.assertEqual(
            resultado["quantidade_associacoes_grupo_trecho"], 3
        )

    def test_sem_candidatos(self):
        self.grupos = []
        resultado = self.consultar()

        self.assertEqual(resultado["grupos_distintos"], [])
        self.assertEqual(resultado["quantidade_trechos"], 2)

    def test_rota_vazia_bloqueada(self):
        with self.assertRaises(ValueError):
            consultar_proximidade_rota([], self.grupos)

    def test_id_de_trecho_repetido(self):
        self.trechos[1]["id"] = "T1"

        with self.assertRaises(ValueError):
            self.consultar()

    def test_tipo_desconhecido(self):
        self.trechos[1]["tipo"] = "TIPO_INVALIDO"

        with self.assertRaises(ValueError):
            self.consultar()

    def test_embarque_sem_coordenadas(self):
        self.trechos[1]["ponto"] = {}

        with self.assertRaises(ValueError):
            self.consultar()

    def test_pendente_bloqueado(self):
        self.grupos[0]["situacao_integracao"] = "PENDENTE_REVISAO"

        with self.assertRaises(ValueError):
            self.consultar()

    def test_entradas_nao_alteradas(self):
        trechos_originais = copy.deepcopy(self.trechos)
        grupos_originais = copy.deepcopy(self.grupos)

        self.consultar()

        self.assertEqual(self.trechos, trechos_originais)
        self.assertEqual(self.grupos, grupos_originais)


if __name__ == "__main__":
    unittest.main(verbosity=2)