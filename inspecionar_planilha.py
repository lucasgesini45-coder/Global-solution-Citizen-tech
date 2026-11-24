from collections import Counter
from datetime import date, datetime
from pathlib import Path
import math
import unicodedata

from openpyxl import load_workbook

from backend.src.seguranca import avaliar_atualidade


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    """Padroniza textos para facilitar comparações."""
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


def verificar_coordenadas(latitude, longitude):
    """
    Verifica ausência, formato e limites numéricos.

    Não confirma se o ponto está dentro de São Paulo
    nem se a localização é precisa.
    """
    coordenadas = (latitude, longitude)

    for valor in coordenadas:
        if normalizar_texto(valor) in ("", "NULL", "NONE"):
            return "AUSENTES"

    valores = []

    for valor in coordenadas:
        if isinstance(valor, bool):
            return "INVALIDAS"

        try:
            numero = float(
                str(valor).strip().replace(",", ".")
            )
        except (ValueError, TypeError):
            return "INVALIDAS"

        if not math.isfinite(numero):
            return "INVALIDAS"

        valores.append(numero)

    latitude, longitude = valores

    if not -90 <= latitude <= 90:
        return "INVALIDAS"

    if not -180 <= longitude <= 180:
        return "INVALIDAS"

    if latitude == 0 and longitude == 0:
        return "SUSPEITAS_ZERO"

    return "LIMITES_VALIDOS"


# ============================================================
# CONFIGURAÇÕES
# ============================================================

caminho = (
    Path.home()
    / "Downloads"
    / "SPDadosCriminais_2026.xlsx"
)

# Nome utilizado nesta fonte para o município de São Paulo.
municipio_alvo = normalizar_texto("S.PAULO")

abas_dados = [
    "JAN-JUN_2026",
    "JUL-DEZ_2026",
]

campos_datas = [
    "DATA_OCORRENCIA_BO",
    "DATA_REGISTRO",
]

campos_obrigatorios = [
    "NOME_MUNICIPIO_CIRCUNSCRICAO",
    "NATUREZA_APURADA",
    "DESCR_TIPOLOCAL",
    "LATITUDE",
    "LONGITUDE",
] + campos_datas

# Usa a data local do computador.
# A janela de 90 dias é um parâmetro experimental.
data_consulta = date.today()
janela_dias = 90

situacoes_coordenadas = (
    "LIMITES_VALIDOS",
    "AUSENTES",
    "INVALIDAS",
    "SUSPEITAS_ZERO",
)


# ============================================================
# CONTADORES E ACUMULADORES
# ============================================================

categorias = Counter()
tipos_locais = Counter()
municipios_encontrados = Counter()
qualidade_coordenadas = Counter()
resultados_atualidade = Counter()
recentes_por_coordenadas = Counter()

total_municipio = 0
sem_categoria = 0
datas_invertidas = 0

tipos_datas = {
    campo: Counter()
    for campo in campos_datas
}

exemplos_datas = {
    campo: []
    for campo in campos_datas
}

menores_datas = {
    campo: None
    for campo in campos_datas
}

maiores_datas = {
    campo: None
    for campo in campos_datas
}

anos_ocorrencias = Counter()

# Acumulados entre as duas abas.
# Servem para identificar linhas com todos os campos iguais.
linhas_vistas = set()
total_candidatas = 0
duplicatas_exatas = 0


# ============================================================
# LEITURA DA PLANILHA
# ============================================================

if not caminho.is_file():
    raise FileNotFoundError(
        f"Planilha não encontrada: {caminho}"
    )

print("Abrindo a planilha...", flush=True)

planilha = load_workbook(
    caminho,
    read_only=True,
    data_only=True,
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
        colunas = {}

        for indice, nome in enumerate(cabecalho):
            nome_normalizado = normalizar_texto(nome)

            if not nome_normalizado:
                continue

            if nome_normalizado in colunas:
                raise ValueError(
                    f"Coluna repetida na aba '{nome_aba}': "
                    f"{nome_normalizado}"
                )

            colunas[nome_normalizado] = indice

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

        # Ordenação fixa para comparar linhas entre abas,
        # mesmo que a ordem das colunas seja diferente.
        colunas_assinatura = sorted(colunas.items())

        total_aba = 0

        for numero, linha in enumerate(linhas, start=1):
            if numero % 50000 == 0:
                print(
                    f"  {numero} linhas percorridas...",
                    flush=True,
                )

            # Ignora linhas totalmente vazias.
            if all(valor is None for valor in linha):
                continue

            municipio = normalizar_texto(
                linha[indice_municipio]
            )

            municipios_encontrados[municipio] += 1

            # As análises abaixo usam somente o município escolhido.
            if municipio != municipio_alvo:
                continue

            total_aba += 1
            total_municipio += 1

            # ------------------------------------------------
            # DATAS: TIPOS, EXEMPLOS E INTERVALOS
            # ------------------------------------------------

            for campo in campos_datas:
                valor_data = linha[colunas[campo]]

                if normalizar_texto(valor_data) in (
                    "",
                    "NULL",
                    "NONE",
                ):
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

                # Este diagnóstico considera apenas datetime.
                if isinstance(valor_data, datetime):
                    data_convertida = valor_data.date()

                    if (
                        menores_datas[campo] is None
                        or data_convertida < menores_datas[campo]
                    ):
                        menores_datas[campo] = data_convertida

                    if (
                        maiores_datas[campo] is None
                        or data_convertida > maiores_datas[campo]
                    ):
                        maiores_datas[campo] = data_convertida

                    if campo == "DATA_OCORRENCIA_BO":
                        anos_ocorrencias[data_convertida.year] += 1

            data_fato = linha[colunas["DATA_OCORRENCIA_BO"]]
            data_registro = linha[colunas["DATA_REGISTRO"]]

            # ------------------------------------------------
            # CONSISTÊNCIA ENTRE AS DATAS
            # ------------------------------------------------

            if (
                isinstance(data_fato, datetime)
                and isinstance(data_registro, datetime)
            ):
                if data_fato.date() > data_registro.date():
                    datas_invertidas += 1

            # ------------------------------------------------
            # ATUALIDADE
            # ------------------------------------------------

            avaliacao_temporal = avaliar_atualidade(
                data_fato,
                data_registro,
                data_consulta,
                janela_dias=janela_dias,
            )

            resultados_atualidade[
                avaliacao_temporal["motivo"]
            ] += 1

            # ------------------------------------------------
            # COORDENADAS
            # ------------------------------------------------

            situacao = verificar_coordenadas(
                linha[indice_latitude],
                linha[indice_longitude],
            )

            qualidade_coordenadas[situacao] += 1

            if avaliacao_temporal["apta"]:
                recentes_por_coordenadas[situacao] += 1

            # ------------------------------------------------
            # DUPLICIDADES EXATAS DAS LINHAS CANDIDATAS
            # ------------------------------------------------

            if (
                avaliacao_temporal["apta"]
                and situacao == "LIMITES_VALIDOS"
            ):
                total_candidatas += 1

                # Compara todos os campos com cabeçalho.
                # Não usa apenas o número do boletim.
                assinatura = tuple(
                    (nome, linha[indice])
                    for nome, indice in colunas_assinatura
                )

                # A assinatura é criada antes desta verificação.
                if assinatura in linhas_vistas:
                    duplicatas_exatas += 1
                else:
                    linhas_vistas.add(assinatura)

            # ------------------------------------------------
            # TIPOS DE LOCAL
            # ------------------------------------------------

            local = normalizar_texto(
                linha[indice_local]
            )

            if local in ("", "NULL", "NONE"):
                local = "SEM INFORMACAO"

            tipos_locais[local] += 1

            # ------------------------------------------------
            # CATEGORIAS
            # ------------------------------------------------

            valor_categoria = linha[indice_categoria]

            if normalizar_texto(valor_categoria) in (
                "",
                "NULL",
                "NONE",
            ):
                sem_categoria += 1
            else:
                categoria = str(valor_categoria).strip()
                categorias[categoria] += 1

        print(
            f"Linhas de São Paulo nesta aba: {total_aba}",
            flush=True,
        )

finally:
    # Fecha o arquivo mesmo se ocorrer um erro.
    planilha.close()


# ============================================================
# RELATÓRIOS
# Todos os relatórios ficam fora dos laços de leitura.
# ============================================================

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
    "não de ocorrências únicas."
)


print("\n--- DIAGNÓSTICO DOS MUNICÍPIOS ---")

print(
    "Total de linhas não vazias analisadas:",
    sum(municipios_encontrados.values()),
)
print("Filtro utilizado:", repr(municipio_alvo))

for municipio, quantidade in municipios_encontrados.most_common(20):
    print(repr(municipio), ":", quantidade)


print("\n--- QUALIDADE DAS COORDENADAS ---")

for situacao in situacoes_coordenadas:
    print(f"{situacao}: {qualidade_coordenadas[situacao]}")

assert sum(qualidade_coordenadas.values()) == total_municipio

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

    for tipo, quantidade in tipos_datas[campo].most_common():
        print(f"{tipo}: {quantidade}")

    print("Exemplos de valores:")

    for exemplo in exemplos_datas[campo]:
        print(exemplo)

    assert sum(tipos_datas[campo].values()) == total_municipio

    print(
        "PASSOU: Todas as linhas selecionadas "
        "foram contabilizadas."
    )


print("\n--- INTERVALO DAS DATAS ---")

for campo in campos_datas:
    print(f"\nCampo: {campo}")
    print("Menor data:", menores_datas[campo])
    print("Maior data:", maiores_datas[campo])

print(
    "\nO intervalo considera somente valores datetime."
)
print(
    "Os extremos não garantem cobertura completa "
    "de todos os dias nem ausência de erros nas datas."
)


print("\n--- ANOS DOS FATOS REGISTRADOS ---")

for ano, quantidade in sorted(anos_ocorrencias.items()):
    print(f"{ano}: {quantidade}")

print(
    "Total de linhas com data do fato em datetime:",
    sum(anos_ocorrencias.values()),
)

assert (
    sum(anos_ocorrencias.values())
    == tipos_datas["DATA_OCORRENCIA_BO"]["datetime"]
)


print("\n--- CONSISTÊNCIA DAS DATAS ---")

print(
    "Linhas com fato posterior ao registro:",
    datas_invertidas,
)
print("Esta contagem compara somente pares de valores datetime.")


print("\n--- ATUALIDADE DOS DADOS ---")

print("Data da consulta:", data_consulta)
print("Janela de análise em dias:", janela_dias)

for motivo, quantidade in resultados_atualidade.most_common():
    print(f"{motivo}: {quantidade}")

assert sum(resultados_atualidade.values()) == total_municipio

print(
    "PASSOU: Todas as linhas selecionadas "
    "foram classificadas."
)

ultima_data_registro = maiores_datas["DATA_REGISTRO"]

if ultima_data_registro is not None:
    diferenca_dias = (
        data_consulta - ultima_data_registro
    ).days

    print(
        "Maior data de registro encontrada:",
        ultima_data_registro,
    )

    if diferenca_dias >= 0:
        print(
            "Dias entre essa data e a consulta:",
            diferenca_dias,
        )
    else:
        print(
            "ATENÇÃO: Existe data de registro "
            "posterior à data da consulta."
        )

print(
    "A maior data de registro não comprova "
    "a data de atualização da fonte."
)


print("\n--- COORDENADAS DAS LINHAS RECENTES ---")

for situacao in situacoes_coordenadas:
    print(f"{situacao}: {recentes_por_coordenadas[situacao]}")

assert (
    sum(recentes_por_coordenadas.values())
    == resultados_atualidade["DENTRO_DA_JANELA"]
)

print(
    "PASSOU: Todas as linhas recentes "
    "foram contabilizadas."
)


print("\n--- DUPLICIDADES EXATAS ---")

print("Linhas candidatas:", total_candidatas)
print("Repetições exatas:", duplicatas_exatas)
print("Linhas distintas:", len(linhas_vistas))

assert (
    len(linhas_vistas) + duplicatas_exatas
    == total_candidatas
)

assert (
    total_candidatas
    == recentes_por_coordenadas["LIMITES_VALIDOS"]
)

print("PASSOU: Contagem de duplicidades consistente.")

print(
    "\nCandidatas são linhas dentro da janela temporal "
    "e com coordenadas numericamente válidas."
)
print(
    "Repetições exatas são cópias adicionais de uma linha, "
    "considerando todos os campos com cabeçalho."
)
print(
    "Linhas distintas ainda não significam ocorrências únicas."
)
print(
    "A planilha original não foi alterada. "
    "Esta etapa apenas inspeciona e contabiliza os dados."
)


if total_municipio == 0:
    print(
        "\nATENÇÃO: Nenhuma linha passou pelo filtro. "
        "Confira o diagnóstico dos municípios."
    )