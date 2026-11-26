import copy
import unittest

from backend.src.proximidade import buscar_grupos_proximos
from backend.src.proximidade_trajeto import (
    buscar_grupos_proximos_do_trajeto,
)


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


class TestesProximidadeTrajeto(unittest.TestCase):

    def setUp(self):
        # Trajeto fictício de aproximadamente 1,1 km.
        self.trajeto = [
            (-23.55, -46.63),
            (-23.56, -46.63),
        ]

        # Próximo do meio, mas longe das duas extremidades.
        self.grupo_meio = criar_grupo(
            "G_MEIO", -23.555, -46.6298
        )

        self.grupo_distante = criar_grupo(
            "G_DISTANTE", -23.555, -46.62
        )

    def test_encontra_grupo_proximo_do_meio(self):
        resultado = buscar_grupos_proximos_do_trajeto(
            self.trajeto,
            [self.grupo_meio, self.grupo_distante],
            raio_metros=100,
        )

        ids = [
            grupo["id_exportacao"]
            for grupo in resultado["grupos_proximos"]
        ]

        self.assertEqual(ids, ["G_MEIO"])

        # Confirma que consultar apenas as pontas perderia esse grupo.
        for latitude, longitude in self.trajeto:
            resultado_ponta = buscar_grupos_proximos(
                latitude,
                longitude,
                [self.grupo_meio],
                raio_metros=100,
            )
            self.assertEqual(
                resultado_ponta["quantidade_grupos_proximos"],
                0,
            )

    def test_respeita_curva_do_trajeto(self):
        trajeto_em_l = [
            (-23.55, -46.63),
            (-23.56, -46.63),
            (-23.56, -46.62),
        ]

        # Perto do meio da diagonal entre origem e destino,
        # mas longe dos dois segmentos do trajeto em L.
        grupo = criar_grupo(
            "G_DIAGONAL", -23.555, -46.625
        )

        resultado = buscar_grupos_proximos_do_trajeto(
            trajeto_em_l,
            [grupo],
            raio_metros=100,
        )

        self.assertEqual(
            resultado["quantidade_grupos_proximos"],
            0,
        )

    def test_conta_grupo_uma_vez_em_trajeto_de_ida_e_volta(self):
        trajeto = self.trajeto + [self.trajeto[0]]

        resultado = buscar_grupos_proximos_do_trajeto(
            trajeto,
            [self.grupo_meio],
            raio_metros=100,
        )

        self.assertEqual(
            resultado["quantidade_grupos_proximos"],
            1,
        )

    def test_lista_de_candidatos_vazia(self):
        resultado = buscar_grupos_proximos_do_trajeto(
            self.trajeto, []
        )
        self.assertEqual(resultado["grupos_proximos"], [])

    def test_trajetos_invalidos(self):
        casos = [
            [],
            [(-23.55, -46.63)],
            [(-23.55, -46.63), (-23.55, -46.63)],
            [(91, 0), (0, 0)],
        ]

        for trajeto in casos:
            with self.subTest(trajeto=trajeto):
                with self.assertRaises(ValueError):
                    buscar_grupos_proximos_do_trajeto(
                        trajeto, []
                    )

    def test_trajeto_fora_do_escopo_local(self):
        with self.assertRaises(ValueError):
            buscar_grupos_proximos_do_trajeto(
                [(0, 0), (1, 0)],
                [],
            )

    def test_raios_invalidos(self):
        for raio in (-1, True, "100", 2001, float("nan")):
            with self.subTest(raio=raio):
                with self.assertRaises(ValueError):
                    buscar_grupos_proximos_do_trajeto(
                        self.trajeto,
                        [],
                        raio_metros=raio,
                    )

    def test_grupo_pendente_bloqueado(self):
        grupo = copy.deepcopy(self.grupo_meio)
        grupo["situacao_integracao"] = "PENDENTE_REVISAO"

        with self.assertRaises(ValueError):
            buscar_grupos_proximos_do_trajeto(
                self.trajeto, [grupo]
            )

    def test_grupo_repetido_bloqueado(self):
        with self.assertRaises(ValueError):
            buscar_grupos_proximos_do_trajeto(
                self.trajeto,
                [self.grupo_meio, self.grupo_meio],
            )

    def test_entradas_nao_alteradas(self):
        grupos = [self.grupo_meio]
        trajeto_original = copy.deepcopy(self.trajeto)
        grupos_originais = copy.deepcopy(grupos)

        buscar_grupos_proximos_do_trajeto(
            self.trajeto, grupos
        )

        self.assertEqual(self.trajeto, trajeto_original)
        self.assertEqual(grupos, grupos_originais)


if __name__ == "__main__":
    unittest.main(verbosity=2)