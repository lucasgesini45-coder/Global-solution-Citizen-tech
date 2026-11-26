from datetime import date
from pathlib import Path

from backend.src.analise_rota import analisar_rota_experimental


def main():
    caminho_base = (
        Path.home()
        / "Downloads"
        / "rotaviva_revisao_local"
        / "20261124_225604_963080"
        / "seguranca_integracao.json"
    )

    # Trajeto fictício para testar a integração.
    # Não representa uma caminhada verificada nem um ponto real de ônibus.
    trechos = [
        {
            "id": "T1",
            "tipo": "CAMINHADA",
            "trajeto": [
                (-23.5500, -46.6300),
                (-23.5510, -46.6300),
                (-23.5510, -46.6290),
            ],
        },
        {
            "id": "T2",
            "tipo": "EMBARQUE",
            "ponto": {
                "latitude": -23.5510,
                "longitude": -46.6290,
            },
        },
    ]

    print("Analisando uma rota simulada com a base real...")

    resultado = analisar_rota_experimental(
        caminho_base,
        trechos,
        date.today(),
        raio_metros=200,
        permitir_experimental=True,
    )

    temporal = resultado["avaliacao_temporal"]
    resumo = temporal["resumo"]
    cobertura = temporal["cobertura_temporal"]
    proximidade = resultado["proximidade_rota"]

    print("\n--- CONTEXTO DA CONSULTA ---")
    print("Rota: SIMULADA")
    print("Base: REAL, COM USO EXPERIMENTAL")
    print("Data de uso:", temporal["data_uso"])
    print("Data da consulta da base:", temporal["data_consulta_base"])
    print("Janela temporal:", temporal["janela_dias"], "dias")
    print("Raio de consulta:", proximidade["raio_metros"], "metros")

    print("\n--- ATUALIDADE DOS DADOS ---")
    print("Candidatos antes:", resumo["candidatos_antes"])
    print(
        "Candidatos elegíveis na data:",
        resumo["candidatos_elegiveis_na_data"],
    )
    print(
        "Excluídos por idade:",
        resumo["candidatos_fora_da_janela"],
    )
    print(
        "Pendentes fora da seleção:",
        resumo["grupos_pendentes_na_base"],
    )
    print(
        "Maior data de registro:",
        cobertura["maior_data_registro_encontrada"],
    )
    print(
        "Dias desde o último registro:",
        cobertura["dias_desde_ultimo_registro"],
    )
    print(
        "Atualização da fonte confirmada:",
        cobertura["atualizacao_da_fonte_confirmada"],
    )

    print("\n--- RESULTADO POR TRECHO ---")

    for trecho in proximidade["trechos"]:
        print(
            f'{trecho["id_trecho"]} - {trecho["tipo"]}: '
            f'{trecho["quantidade_grupos_proximos"]} grupo(s) próximo(s)'
        )

    print("\n--- RESULTADO DA ROTA ---")
    print("Situação da consulta:", resultado["situacao_consulta"])
    print(
        "Grupos distintos na rota:",
        proximidade["quantidade_grupos_distintos"],
    )
    print(
        "Associações entre grupos e trechos:",
        proximidade["quantidade_associacoes_grupo_trecho"],
    )
    print("Pontuação de segurança:", resultado["pontuacao_seguranca"])

    print("\n--- LIMITAÇÕES ---")
    for limitacao in resultado["limitacoes"]:
        print("-", limitacao)

    print("\nConcluído: nenhum arquivo da base foi alterado.")


if __name__ == "__main__":
    main()