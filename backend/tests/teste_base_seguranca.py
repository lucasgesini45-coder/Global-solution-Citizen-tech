import copy
import json
import tempfile
import unittest

from pathlib import Path

from backend.src.base_seguranca import (
    carregar_base_seguranca,
    selecionar_candidatos,
    validar_base_seguranca,
)


def criar_base_simulada():
    candidato = {
        "id_exportacao": "G000001",
        "situacao_integracao": "CANDIDATO_EXPERIMENTAL",
        "motivos_pendencia": [],
        "quantidade_linhas_origem": 1,
        "datas_fato": ["2026-11-20"],
        "naturezas": ["CATEGORIA SIMULADA"],
        "quantidade_pontos_distintos": 1,
        "classificacao_geografica": "DENTRO_DO_CONTORNO",
        "ponto_para_integracao_experimental": {
            "latitude": -23.55,
            "longitude": -46.63,
        },
        "distancia_aproximada_borda_m": None,
    }

    pendente = copy.deepcopy(candidato)
    pendente.update({
        "id_exportacao": "G000002",
        "situacao_integracao": "PENDENTE_REVISAO",
        "motivos_pendencia": ["FORA_DO_CONTORNO"],
        "classificacao_geografica": "FORA_DO_CONTORNO",
        "ponto_para_integracao_experimental": None,
    })

    return {
        "versao_esquema": "1.0",
        "situacao_base": "EXPERIMENTAL",
        "contexto": {
            "data_consulta": "2026-11-24",
            "janela_dias": 90,
        },
        "resumo": {
            "linhas_municipio": 2,
            "linhas_candidatas_antes_da_triagem": 2,
            "grupos_provisorios_exportados": 2,
            "grupos_candidatos_experimentais": 1,
            "grupos_pendentes": 1,
            "linhas_em_grupos_candidatos": 1,
            "linhas_em_grupos_pendentes": 1,
            "linhas_sem_identificacao_nao_exportadas": 0,
        },
        "limitacoes": ["Base fictícia para testes."],
        "grupos": [candidato, pendente],
    }


class TestesBaseSeguranca(unittest.TestCase):

    def setUp(self):
        self.base = criar_base_simulada()

    def test_base_valida(self):
        self.assertEqual(
            validar_base_seguranca(self.base),
            self.base,
        )

    def test_selecao_bloqueada_por_padrao(self):
        with self.assertRaises(ValueError):
            selecionar_candidatos(self.base)

    def test_selecao_exclui_pendentes(self):
        candidatos = selecionar_candidatos(
            self.base,
            permitir_experimental=True,
        )
        self.assertEqual(len(candidatos), 1)
        self.assertEqual(candidatos[0]["id_exportacao"], "G000001")

    def test_pendente_com_ponto_bloqueado(self):
        self.base["grupos"][1]["ponto_para_integracao_experimental"] = {
            "latitude": -23.55,
            "longitude": -46.63,
        }
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_candidato_externo_bloqueado(self):
        self.base["grupos"][0]["classificacao_geografica"] = (
            "FORA_DO_CONTORNO"
        )
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_resumo_inconsistente(self):
        self.base["resumo"]["grupos_provisorios_exportados"] = 99
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_identificador_repetido(self):
        self.base["grupos"][1]["id_exportacao"] = "G000001"
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_coordenada_invalida(self):
        ponto = self.base["grupos"][0]["ponto_para_integracao_experimental"]
        ponto["latitude"] = 91
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_data_fora_da_janela(self):
        self.base["grupos"][0]["datas_fato"] = ["2020-01-01"]
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_versao_desconhecida(self):
        self.base["versao_esquema"] = "999"
        with self.assertRaises(ValueError):
            validar_base_seguranca(self.base)

    def test_leitura_de_arquivo_valido(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "base.json"
            caminho.write_text(
                json.dumps(self.base),
                encoding="utf-8",
            )
            self.assertEqual(
                carregar_base_seguranca(caminho),
                self.base,
            )

    def test_arquivo_inexistente(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ValueError):
                carregar_base_seguranca(
                    Path(pasta) / "inexistente.json"
                )

    def test_json_malformado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "invalido.json"
            caminho.write_text('{"grupos": ', encoding="utf-8")

            with self.assertRaises(ValueError):
                carregar_base_seguranca(caminho)


if __name__ == "__main__":
    unittest.main(verbosity=2)