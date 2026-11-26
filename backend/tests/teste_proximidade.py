import copy
import unittest

from backend.src.geografia import calcular_distancia_metros
from backend.src.proximidade import buscar_grupos_proximos


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


class TestesProximidade(unittest.TestCase):

    def setUp(self):
        # Pontos fictícios para verificar a lógica.
        self.latitude = -23.55
        self.longitude = -46.63

        self.mesmo_ponto = criar_grupo(
            "G1", -23.55, -46.63
        )
        self.proximo = criar_grupo(
            "G2", -23.5505, -46.63
        )
        self.distante = criar_grupo(
            "G3", -23.57, -46.63
        )

    def consultar(self, grupos, raio=200):
        return buscar_grupos_proximos(
            self.latitude,
            self.longitude,
            grupos,
            raio_metros=raio,
        )

    def test_encontra_proximos_e_exclui_distante(self):
        resultado = self.consultar([
            self.distante,
            self.proximo,
            self.mesmo_ponto,
        ])

        ids = [
            item["id_exportacao"]
            for item in resultado["grupos_proximos"]
        ]

        self.assertEqual(ids, ["G1", "G2"])
        self.assertEqual(resultado["grupos_consultados"], 3)

    def test_raio_zero_encontra_mesmo_ponto(self):
        resultado = self.consultar([
            self.mesmo_ponto,
            self.proximo,
        ], raio=0)

        self.assertEqual(
            resultado["quantidade_grupos_proximos"], 1
        )

    def test_limite_do_raio_inclusivo(self):
        distancia = calcular_distancia_metros(
            (self.latitude, self.longitude),
            (-23.5505, -46.63),
        )

        resultado = self.consultar(
            [self.proximo],
            raio=distancia,
        )

        self.assertEqual(
            resultado["quantidade_grupos_proximos"], 1
        )

    def test_raio_menor_que_distancia(self):
        distancia = calcular_distancia_metros(
            (self.latitude, self.longitude),
            (-23.5505, -46.63),
        )

        resultado = self.consultar(
            [self.proximo],
            raio=distancia - 0.01,
        )

        self.assertEqual(
            resultado["quantidade_grupos_proximos"], 0
        )

    def test_lista_vazia(self):
        resultado = self.consultar([])

        self.assertEqual(resultado["grupos_proximos"], [])
        self.assertEqual(resultado["situacao"], "EXPERIMENTAL")

    def test_raios_invalidos(self):
        for raio in (-1, True, "200", float("nan"), float("inf")):
            with self.subTest(raio=raio):
                with self.assertRaises(ValueError):
                    self.consultar([], raio=raio)

    def test_pendente_bloqueado(self):
        grupo = copy.deepcopy(self.proximo)
        grupo["situacao_integracao"] = "PENDENTE_REVISAO"

        with self.assertRaises(ValueError):
            self.consultar([grupo])

    def test_identificador_repetido_bloqueado(self):
        with self.assertRaises(ValueError):
            self.consultar([
                self.proximo,
                copy.deepcopy(self.proximo),
            ])

    def test_coordenada_consulta_invalida(self):
        with self.assertRaises(ValueError):
            buscar_grupos_proximos(91, -46.63, [])

    def test_coordenada_grupo_invalida(self):
        grupo = copy.deepcopy(self.proximo)
        grupo["ponto_para_integracao_experimental"]["longitude"] = 181

        with self.assertRaises(ValueError):
            self.consultar([grupo])

    def test_entrada_nao_alterada(self):
        grupos = [self.proximo, self.mesmo_ponto]
        original = copy.deepcopy(grupos)

        self.consultar(grupos)

        self.assertEqual(grupos, original)


if __name__ == "__main__":
    unittest.main(verbosity=2)