from collections import Counter
from datetime import datetime
from pathlib import Path
from backend.src.seguranca import avaliar_atualidade
import math
import unicodedata

from openpyxl import load_workbook


# Padroniza textos para facilitar comparações.
def normalizar_texto(valor):
    if valor is None:
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        letra
        for letra in texto
        if not unicodedata.combining(letra)
    )

    return " ".join(texto.split())


# Verifica o formato e os limites numéricos das coordenadas.
# Não confirma se o ponto está dentro do município.
def verificar_coordenadas(latitude, longitude):
    coordenadas = (latitude, longitude)

    for valor in coordenadas:
        if normalizar_texto(valor) in ("", "NULL", "NONE"):
            return "AUSENTES"

    valores = []

    for valor in coordenadas:
        if isinstance(valor, bool):
            return "INVALIDAS"

        try:
            texto = str(valor).strip().replace(",", ".")
            numero = float(texto)
        except (ValueError, TypeError):
            return "INVALIDAS"

        if not math.isfinite(numero):
            return "INVALIDAS"

        valores.append(numero)

    latitude, longitude = valores

    if not (-90 <= latitude <= 90):
        return "INVALIDAS"

    if not (-180 <= longitude <= 180):
        return "INVALIDAS"

    if latitude == 0 and longitude == 0:
        return "SUSPEITAS_ZERO"

    return "LIMITES_VALIDOS"


# Configurações específicas desta fonte.
caminho = (
    Path.home()
    / "Downloads"
    / "SPDadosCriminais_2026.xlsx"
)

municipio_alvo = "S.PAULO"

abas_dados = [
    "JAN-JUN_2026",
    "JUL-DEZ_2026"
]

campos_datas = [
    "DATA_OCORRENCIA_BO",
    "DATA_REGISTRO"
]

campos_obrigatorios = [
    "NOME_MUNICIPIO_CIRCUNSCRICAO",
    "NATUREZA_APURADA",
    "DESCR_TIPOLOCAL",
    "LATITUDE",
    "LONGITUDE",
    "DATA_OCORRENCIA_BO",
    "DATA_REGISTRO"
]


# Contadores acumulados das duas abas.
categorias = Counter()
tipos_locais = Counter()
municipios_encontrados = Counter()
qualidade_coordenadas = Counter()

total_municipio = 0
sem_categoria = 0


# Cada campo de data possui seu próprio contador.
tipos_datas = {
    campo: Counter()
    for campo in campos_datas
}

# Cada campo possui uma lista de exemplos.
exemplos_datas = {
    campo: []
    for campo in campos_datas
}

# None indica que nenhuma data foi encontrada ainda.
menores_datas = {
    campo: None
    for campo in campos_datas
}

maiores_datas = {
    campo: None
    for campo in campos_datas
}


if not caminho.is_file():
    raise FileNotFoundError(
        f"Planilha não encontrada: {caminho}"
    )
anos_ocorrencias = Counter()

datas_invertidas = 0

# Referência da consulta, usando a data local do computador.
data_consulta = datetime.now().date()

# Configuração inicial de teste.
janela_dias = 90

resultados_atualidade = Counter()

recentes_por_coordenadas = Counter()

print("Abrindo a planilha...", flush=True)

planilha = load_workbook(
    caminho,
    read_only=True,
    data_only=True
)

try:
    for nome_aba in abas_dados:
        if nome_aba not in planilha.sheetnames:
            raise ValueError(
                f"Aba não encontrada: {nome_aba}"
            )

        print(f"\nLendo aba: {nome_aba}", flush=True)

        aba = planilha[nome_aba]
        linhas = aba.iter_rows(values_only=True)
        cabecalho = next(linhas, None)

        if cabecalho is None:
            raise ValueError(
                f"A aba '{nome_aba}' está vazia."
            )

        # Relaciona o nome de cada coluna à sua posição.
        colunas = {
            normalizar_texto(nome): indice
            for indice, nome in enumerate(cabecalho)
            if nome is not None
        }

        campos_ausentes = [
            campo
            for campo in campos_obrigatorios
            if campo not in colunas
        ]

        if campos_ausentes:
            raise ValueError(
                f"Campos ausentes na aba '{nome_aba}': "
                + ", ".join(campos_ausentes)
            )

        indice_municipio = colunas[
            "NOME_MUNICIPIO_CIRCUNSCRICAO"
        ]
        indice_categoria = colunas["NATUREZA_APURADA"]
        indice_local = colunas["DESCR_TIPOLOCAL"]
        indice_latitude = colunas["LATITUDE"]
        indice_longitude = colunas["LONGITUDE"]

        total_aba = 0

        for numero, linha in enumerate(linhas, start=1):
            if numero % 50000 == 0:
                print(
                    f"  {numero} linhas percorridas...",
                    flush=True
                )

            # Ignora linhas totalmente vazias.
            if all(valor is None for valor in linha):
                continue

            municipio = normalizar_texto(
                linha[indice_municipio]
            )

            municipios_encontrados[municipio] += 1

            # As verificações seguintes usam apenas São Paulo.
            if municipio != municipio_alvo:
                continue

            total_aba += 1
            total_municipio += 1
            avaliacao_temporal = avaliar_atualidade(

            linha[colunas["DATA_OCORRENCIA_BO"]],
            
            linha[colunas["DATA_REGISTRO"]],
                            data_consulta,
                            janela_dias=janela_dias
                        )

            motivo = avaliacao_temporal["motivo"]
            resultados_atualidade[motivo] += 1

            data_fato = linha[colunas["DATA_OCORRENCIA_BO"]]
            data_registro = linha[colunas["DATA_REGISTRO"]]

            if (
                isinstance(data_fato, datetime)
                    and isinstance(data_registro, datetime)
            ):
                if data_fato.date() > data_registro.date():
                    datas_invertidas += 1

            # Inspeciona os dois campos de data.
            for campo in campos_datas:
                valor_data = linha[colunas[campo]]

                texto_data = normalizar_texto(valor_data)

                if texto_data in ("", "NULL", "NONE"):
                    tipos_datas[campo]["AUSENTE"] += 1
                else:
                    tipo = type(valor_data).__name__
                    tipos_datas[campo][tipo] += 1

                    exemplo = repr(valor_data)

                    if (
                        len(exemplos_datas[campo]) < 3
                        and exemplo not in exemplos_datas[campo]
                    ):
                        exemplos_datas[campo].append(exemplo)

                    # Compara somente valores reconhecidos
                    # como datetime, sem adivinhar formatos.
                    if isinstance(valor_data, datetime):
                        data = valor_data.date()

                        if (
                            menores_datas[campo] is None
                            or data < menores_datas[campo]
                        ):
                            menores_datas[campo] = data

                        if (
                            maiores_datas[campo] is None
                            or data > maiores_datas[campo]
                        ):
                            maiores_datas[campo] = data
                        if campo == "DATA_OCORRENCIA_BO": 

                                    anos_ocorrencias[data.year] += 1
           
            # Verifica as coordenadas.
            situacao = verificar_coordenadas(
                linha[indice_latitude],
                linha[indice_longitude]
            )

            qualidade_coordenadas[situacao] += 1
            if avaliacao_temporal["apta"]: recentes_por_coordenadas[situacao] += 1

            # Conta os tipos de local.
            local = normalizar_texto(
                linha[indice_local]
            )

            if local in ("", "NULL", "NONE"):
                local = "SEM INFORMACAO"

            tipos_locais[local] += 1

            # Conta as categorias criminais.
            valor_categoria = linha[indice_categoria]
            texto_categoria = normalizar_texto(valor_categoria)

            if texto_categoria in ("", "NULL", "NONE"):
                sem_categoria += 1
            else:
                categoria = str(valor_categoria).strip()
                categorias[categoria] += 1

        print(
            f"Linhas de São Paulo nesta aba: {total_aba}"
        )

finally:
    # Fecha a planilha mesmo se ocorrer erro na leitura.
    planilha.close()


# Exibe os resultados fora dos laços de leitura.
print("\n--- TIPOS DE LOCAL EM SÃO PAULO ---")

for local, quantidade in tipos_locais.most_common():
    print(f"{local}: {quantidade}")

assert sum(tipos_locais.values()) == total_municipio

print(
    "PASSOU: Todos os registros selecionados "
    "foram contabilizados por local."
)


print("\n--- CATEGORIAS EM SÃO PAULO ---")

for categoria, quantidade in categorias.most_common():
    print(f"{categoria}: {quantidade}")

print("\nTotal de linhas de São Paulo:", total_municipio)
print("Linhas sem categoria:", sem_categoria)
print("Categorias distintas:", len(categorias))

assert (
    sum(categorias.values()) + sem_categoria
    == total_municipio
)

print(
    "\nAtenção: são contagens de linhas, "
    "ainda sem deduplicação."
)


print("\n--- DIAGNÓSTICO DOS MUNICÍPIOS ---")

print(
    "Total de linhas não vazias analisadas:",
    sum(municipios_encontrados.values())
)
print("Filtro utilizado:", repr(municipio_alvo))

municipios_frequentes = municipios_encontrados.most_common(20)

for municipio, quantidade in municipios_frequentes:
    print(repr(municipio), ":", quantidade)


print("\n--- QUALIDADE DAS COORDENADAS ---")

situacoes_coordenadas = [
    "LIMITES_VALIDOS",
    "AUSENTES",
    "INVALIDAS",
    "SUSPEITAS_ZERO"
]

for situacao in situacoes_coordenadas:
    print(f"{situacao}: {qualidade_coordenadas[situacao]}")

assert (
    sum(qualidade_coordenadas.values())
    == total_municipio
)

print(
    "PASSOU: Todos os registros selecionados "
    "tiveram as coordenadas verificadas."
)

print(
    "\nLIMITES_VALIDOS indica somente que os números "
    "estão dentro dos limites de latitude e longitude."
)
print(
    "Ainda não confirma a localização em São Paulo "
    "nem a precisão do ponto."
)


print("\n--- DIAGNÓSTICO DAS DATAS ---")

for campo in campos_datas:
    print(f"\nCampo: {campo}")

    contagem = tipos_datas[campo].most_common()

    for tipo, quantidade in contagem:
        print(f"{tipo}: {quantidade}")

    print("Exemplos de valores:")

    for exemplo in exemplos_datas[campo]:
        print(exemplo)

    assert (
        sum(tipos_datas[campo].values())
        == total_municipio
    )

    print(
        "PASSOU: Todas as linhas selecionadas "
        "foram contabilizadas."
    )


print("\n--- INTERVALO DAS DATAS ---")

for campo in campos_datas:
    print(f"\nCampo: {campo}")

    menor = menores_datas[campo]
    maior = maiores_datas[campo]

    if menor is None:
        print("Nenhum valor datetime disponível para comparação.")
    else:
        print("Menor data:", menor.isoformat())
        print("Maior data:", maior.isoformat())

print(
    "\nO intervalo considera somente valores datetime."
)
print(
    "Os extremos não garantem cobertura completa "
    "de todos os dias nem ausência de erros nas datas."
)


"\nO intervalo considera somente valores datetime."

print(
    "Os extremos não garantem cobertura completa "
    "de todos os dias nem ausência de erros nas datas."
)

if total_municipio == 0:
    print(
        "\nATENÇÃO: Nenhuma linha passou pelo filtro. "
        "Confira o diagnóstico dos municípios."
    )

print("\n--- ANOS DOS FATOS REGISTRADOS ---")

for ano, quantidade in sorted(anos_ocorrencias.items()):
    print(f"{ano}: {quantidade}")

print(
    "Total de linhas com data datetime:",
    sum(anos_ocorrencias.values())
)
print("\n---CONSITÊNCIA DAS DATAS ===")
print("Linhas com fato posterior ao registro", datas_invertidas)
print("\n---ATUALIDADE DOS DADOS ---")
print("Data da consulta:", data_consulta)
print("Janela de análise em dias:", janela_dias)

for motivo, quantidade in resultados_atualidade.most_common():
    print(f"{motivo}: {quantidade}")

assert (
    sum(resultados_atualidade.values()) == total_municipio
)

print("PASSOU: Todas as linhas selecionadas foram classificadas.")
print("\n---COORDENADAS DAS LINHAS RECENTES ---")

for situacao in situacoes_coordenadas:
    print(f"{situacao}: {recentes_por_coordenadas[situacao]}")

assert (
    sum(recentes_por_coordenadas.values())
    ==
resultados_atualidade["DENTRO_DA_JANELA"]
)

print("PASSOU: Todas as linhas recentes foram contabilizadas.")