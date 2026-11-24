import math
import unittest

from shapely.geometry import Polygon

from backend.src.geografia import (
    calcular_distancia_metros,
    classificar_ponto_no_contorno,
)


class TestesGeografia(unittest.TestCase):

    def setUp(self):
        # Retângulo fictício em longitude/latitude.
        self.contorno = Polygon([
            (10, 20),
            (12, 20),
            (12, 22),
            (10, 22),
            (10, 20),
        ])

    def test_ponto_interno(self):
        resultado = classificar_ponto_no_contorno(
            21, 11, self.contorno
        )
        self.assertEqual(resultado, "DENTRO_DO_CONTORNO")

    def test_ponto_externo(self):
        resultado = classificar_ponto_no_contorno(
            21, 13, self.contorno
        )
        self.assertEqual(resultado, "FORA_DO_CONTORNO")

    def test_ponto_na_borda(self):
        resultado = classificar_ponto_no_contorno(
            21, 10, self.contorno
        )
        self.assertEqual(resultado, "NA_BORDA_DO_CONTORNO")

    def test_ordem_latitude_longitude(self):
        resultado = classificar_ponto_no_contorno(
            11, 21, self.contorno
        )
        self.assertEqual(resultado, "FORA_DO_CONTORNO")

    def test_ponto_em_buraco_do_poligono(self):
        contorno_com_buraco = Polygon(
            [
                (10, 20),
                (14, 20),
                (14, 24),
                (10, 24),
                (10, 20),
            ],
            holes=[[
                (11, 21),
                (13, 21),
                (13, 23),
                (11, 23),
                (11, 21),
            ]],
        )

        resultado = classificar_ponto_no_contorno(
            22, 12, contorno_com_buraco
        )
        self.assertEqual(resultado, "FORA_DO_CONTORNO")

    def test_coordenadas_invalidas(self):
        casos = [
            (91, 11),
            (21, 181),
            (True, 11),
            ("21", 11),
            (float("nan"), 11),
            (21, float("inf")),
        ]

        for latitude, longitude in casos:
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(ValueError):
                    classificar_ponto_no_contorno(
                        latitude,
                        longitude,
                        self.contorno,
                    )

    def test_contorno_vazio(self):
        with self.assertRaises(ValueError):
            classificar_ponto_no_contorno(21, 11, Polygon())

    def test_contorno_com_cruzamento(self):
        contorno_invalido = Polygon([
            (10, 20),
            (12, 22),
            (10, 22),
            (12, 20),
            (10, 20),
        ])

        with self.assertRaises(ValueError):
            classificar_ponto_no_contorno(
                21, 11, contorno_invalido
            )

    def test_distancia_entre_pontos_iguais(self):
        distancia = calcular_distancia_metros(
            (-23.5, -46.6),
            (-23.5, -46.6),
        )
        self.assertEqual(distancia, 0)

    def test_distancia_um_grau_no_equador(self):
        distancia = calcular_distancia_metros(
            (0, 0),
            (0, 1),
        )
        self.assertGreater(distancia, 111_000)
        self.assertLess(distancia, 111_300)

    def test_distancia_simetrica(self):
        ponto_a = (-23.5, -46.6)
        ponto_b = (-23.6, -46.7)

        ida = calcular_distancia_metros(ponto_a, ponto_b)
        volta = calcular_distancia_metros(ponto_b, ponto_a)

        self.assertTrue(math.isclose(ida, volta, rel_tol=1e-12))

    def test_distancia_com_ponto_invalido(self):
        with self.assertRaises(ValueError):
            calcular_distancia_metros((91, 0), (0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)

    