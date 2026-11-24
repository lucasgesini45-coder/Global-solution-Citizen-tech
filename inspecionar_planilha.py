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

# Nome utilizado nesta fonte para São Paulo.
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
    "NOME_DELEGACIA",
    "ANO_BO",
    "NUM_BO",
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

# Duplicidades exatas entre as linhas candidatas das duas abas.
linhas_vistas = set()
total_candidatas = 0
duplicatas_exatas = 0

# Investigação por chave provisória:
# delegacia + ano + número do boletim.
contagem_por_boletim = Counter()
naturezas_por_boletim = {}

linhas_sem_identificacao_boletim = 0
linhas_sem_natureza_boletim = 0


# ============================================================
# LEITURA DA PLANILHA
# ============================================================

if not caminho.is_file():
    raise FileNotFoundError(
        f"Planilha não encontrada: {caminho}"
    )

# Guarda as datas e coordenadas das linhas de cada chave provisória.
datas_por_boletim = {}
coordenadas_por_boletim = {}

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

        # Permite comparar linhas entre abas,
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

            # As análises abaixo usam somente São Paulo.
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
            # LINHAS CANDIDATAS:
            # ATUALIDADE APROVADA E LIMITES NUMÉRICOS VÁLIDOS
            # ------------------------------------------------

            if (
                avaliacao_temporal["apta"]
                and situacao == "LIMITES_VALIDOS"
            ):
                total_candidatas += 1

                # --------------------------------------------
                # DUPLICIDADES EXATAS
                # --------------------------------------------

                assinatura = tuple(
                    (nome, linha[indice])
                    for nome, indice in colunas_assinatura
                )

                if assinatura in linhas_vistas:
                    duplicatas_exatas += 1
                else:
                    linhas_vistas.add(assinatura)

                # --------------------------------------------
                # IDENTIFICAÇÃO PROVISÓRIA DO BOLETIM
                # --------------------------------------------

                delegacia = normalizar_texto(
                    linha[colunas["NOME_DELEGACIA"]]
                )
                ano_bo = normalizar_texto(
                    linha[colunas["ANO_BO"]]
                )
                numero_bo = normalizar_texto(
                    linha[colunas["NUM_BO"]]
                )

                identificadores = (
                    delegacia,
                    ano_bo,
                    numero_bo,
                )

                identificacao_incompleta = any(
                    valor in ("", "NULL", "NONE")
                    for valor in identificadores
                )

                if identificacao_incompleta:
                    linhas_sem_identificacao_boletim += 1
                else:
                    chave_boletim = identificadores

                    contagem_por_boletim[chave_boletim] += 1

                    if chave_boletim not in datas_por_boletim:
                        datas_por_boletim[chave_boletim] = set()
                        coordenadas_por_boletim[chave_boletim] = set()

                    # Compara o dia do fato, sem considerar o horário.
                    if isinstance(data_fato, datetime):
                        dia_fato = data_fato.date()
                    else:
                        dia_fato = data_fato

                    datas_por_boletim[chave_boletim].add(dia_fato)

                    # Estas coordenadas já passaram pela validação numérica.
                    latitude = float(
                        str(linha[indice_latitude]).strip().replace(",", ".")
                    )
                    longitude = float(
                        str(linha[indice_longitude]).strip().replace(",", ".")
                    )

                    coordenadas_por_boletim[chave_boletim].add(
                        (latitude, longitude)
                    )

                    if chave_boletim not in naturezas_por_boletim:
                        naturezas_por_boletim[chave_boletim] = set()

                    natureza = normalizar_texto(
                        linha[indice_categoria]
                    )

                    if natureza in ("", "NULL", "NONE"):
                        linhas_sem_natureza_boletim += 1
                    else:
                        naturezas_por_boletim[chave_boletim].add(
                            natureza
                        )

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
print(
    "Esta contagem compara somente pares de valores datetime."
)


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


print("\n--- IDENTIFICAÇÃO DOS BOLETINS ---")

combinacoes_repetidas = 0
linhas_em_combinacoes_repetidas = 0
combinacoes_com_multiplas_naturezas = 0

for chave, quantidade in contagem_por_boletim.items():
    if quantidade > 1:
        combinacoes_repetidas += 1
        linhas_em_combinacoes_repetidas += quantidade

    if len(naturezas_por_boletim[chave]) > 1:
        combinacoes_com_multiplas_naturezas += 1

linhas_identificadas = sum(contagem_por_boletim.values())

print("Linhas candidatas:", total_candidatas)

print(
    "Linhas com identificação preenchida:",
    linhas_identificadas,
)
print(
    "Linhas com identificação incompleta:",
    linhas_sem_identificacao_boletim,
)
print(
    "Combinações distintas de delegacia, ano e número:",
    len(contagem_por_boletim),
)
print(
    "Combinações presentes em mais de uma linha:",
    combinacoes_repetidas,
)
print(
    "Total de linhas nessas combinações repetidas:",
    linhas_em_combinacoes_repetidas,
)
print(
    "Combinações com mais de uma natureza:",
    combinacoes_com_multiplas_naturezas,
)
print(
    "Linhas identificadas, mas sem natureza:",
    linhas_sem_natureza_boletim,
)

assert (
    linhas_identificadas + linhas_sem_identificacao_boletim
    == total_candidatas
)

assert (
    set(contagem_por_boletim)
    == set(naturezas_por_boletim)
)

print(
    "PASSOU: Todas as linhas candidatas "
    "foram contabilizadas."
)

print(
    "\nA combinação utilizada é provisória. "
    "Não comprova a quantidade de ocorrências únicas."
)
print(
    "Uma combinação repetida pode conter informações "
    "complementares. Nenhuma linha foi excluída."
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
    print("\n--- CONSISTÊNCIA DAS COMBINAÇÕES REPETIDAS ---")

mesma_data_mesmo_ponto = 0
somente_datas_diferentes = 0
somente_coordenadas_diferentes = 0
datas_e_coordenadas_diferentes = 0

for chave, quantidade in contagem_por_boletim.items():
    if quantidade <= 1:
        continue

    datas_diferentes = len(datas_por_boletim[chave]) > 1
    coordenadas_diferentes = len(coordenadas_por_boletim[chave]) > 1

    if datas_diferentes and coordenadas_diferentes:
        datas_e_coordenadas_diferentes += 1
    elif datas_diferentes:
        somente_datas_diferentes += 1
    elif coordenadas_diferentes:
        somente_coordenadas_diferentes += 1
    else:
        mesma_data_mesmo_ponto += 1

print("Combinações repetidas:", combinacoes_repetidas)
print("Mesma data e mesmo ponto:", mesma_data_mesmo_ponto)
print("Somente datas diferentes:", somente_datas_diferentes)
print(
    "Somente coordenadas diferentes:",
    somente_coordenadas_diferentes,
)
print(
    "Datas e coordenadas diferentes:",
    datas_e_coordenadas_diferentes,
)

assert (
    mesma_data_mesmo_ponto
    + somente_datas_diferentes
    + somente_coordenadas_diferentes
    + datas_e_coordenadas_diferentes
    == combinacoes_repetidas
)

print("PASSOU: Todas as combinações repetidas foram classificadas.")

print(
    "\nA comparação usa o dia do fato e os valores numéricos "
    "das coordenadas, sem arredondamento."
)
print(
    "Diferenças não comprovam erro: podem representar "
    "informações distintas ou imprecisão da fonte."
)
print(
    "Mesma data e mesmo ponto também não comprovam "
    "que as linhas representam um único evento."
)
print("Nenhum registro foi excluído ou alterado.")

# ============================================================
# DISTÂNCIA ENTRE COORDENADAS DIVERGENTES
# ============================================================

def calcular_distancia_metros(ponto_a, ponto_b):
    """
    Calcula a distância aproximada sobre a superfície terrestre.

    Cada ponto deve estar no formato (latitude, longitude),
    em graus, com valores numéricos previamente validados.

    Usa a fórmula de Haversine e uma Terra esférica.
    Não calcula distância por ruas.
    """
    raio_terra_metros = 6_371_000

    latitude_a, longitude_a = ponto_a
    latitude_b, longitude_b = ponto_b

    latitude_a = math.radians(latitude_a)
    longitude_a = math.radians(longitude_a)
    latitude_b = math.radians(latitude_b)
    longitude_b = math.radians(longitude_b)

    diferenca_latitude = latitude_b - latitude_a
    diferenca_longitude = longitude_b - longitude_a

    valor = (
        math.sin(diferenca_latitude / 2) ** 2
        + math.cos(latitude_a)
        * math.cos(latitude_b)
        * math.sin(diferenca_longitude / 2) ** 2
    )

    # Evita valores fora do intervalo por arredondamento numérico.
    valor = min(1.0, max(0.0, valor))

    angulo = 2 * math.atan2(
        math.sqrt(valor),
        math.sqrt(1 - valor),
    )

    return raio_terra_metros * angulo


# Verificações básicas do cálculo.
assert calcular_distancia_metros(
    (-23.5, -46.6),
    (-23.5, -46.6),
) == 0

# Um grau de longitude no Equador corresponde a cerca de 111 km.
distancia_teste = calcular_distancia_metros(
    (0.0, 0.0),
    (0.0, 1.0),
)

assert 111_000 < distancia_teste < 111_300

assert math.isclose(
    calcular_distancia_metros(
        (-23.5, -46.6),
        (-23.6, -46.7),
    ),
    calcular_distancia_metros(
        (-23.6, -46.7),
        (-23.5, -46.6),
    ),
    rel_tol=1e-12,
)

print("\n--- DISTÂNCIA ENTRE PONTOS DIVERGENTES ---")
print("PASSOU: Verificações básicas do cálculo de distância.")

total_combinacoes_divergentes = 0

for chave, pontos in coordenadas_por_boletim.items():
    if len(pontos) <= 1:
        continue

    total_combinacoes_divergentes += 1

    # Ordena para manter a comparação reproduzível.
    lista_pontos = sorted(pontos)

    menor_distancia = None
    maior_distancia = 0.0
    pares_comparados = 0

    # Compara cada par de pontos uma única vez.
    for indice_a in range(len(lista_pontos)):
        for indice_b in range(indice_a + 1, len(lista_pontos)):
            distancia = calcular_distancia_metros(
                lista_pontos[indice_a],
                lista_pontos[indice_b],
            )

            pares_comparados += 1

            if (
                menor_distancia is None
                or distancia < menor_distancia
            ):
                menor_distancia = distancia

            maior_distancia = max(
                maior_distancia,
                distancia,
            )

    print(
        f"\nCombinação divergente "
        f"{total_combinacoes_divergentes}:"
    )
    print("Linhas nessa combinação:", contagem_por_boletim[chave])
    print("Pontos distintos:", len(lista_pontos))
    print("Pares de pontos comparados:", pares_comparados)
    print(f"Menor distância: {menor_distancia:.2f} metros")
    print(f"Maior distância: {maior_distancia:.2f} metros")

assert (
    total_combinacoes_divergentes
    == (
        somente_coordenadas_diferentes
        + datas_e_coordenadas_diferentes
    )
)

print(
    "\nTotal de combinações com pontos divergentes:",
    total_combinacoes_divergentes,
)
print("PASSOU: Todas as combinações divergentes foram analisadas.")

print(
    "\nAs distâncias são aproximadas e não representam "
    "o percurso pelas ruas."
)
print(
    "Este cálculo não identifica qual ponto está correto "
    "nem confirma a precisão das coordenadas."
)
print("Nenhum registro foi alterado ou excluído.")

# ============================================================
# TRIAGEM DAS DIVERGÊNCIAS DE LOCALIZAÇÃO
# ============================================================

# Guarda as chaves provisórias para uso nas próximas etapas.
chaves_com_localizacao_pendente = set()
chaves_sem_divergencia_interna = set()

linhas_com_localizacao_pendente = 0
linhas_sem_divergencia_interna = 0

for chave, quantidade in contagem_por_boletim.items():
    pontos = coordenadas_por_boletim[chave]

    # Toda combinação identificada deve possuir pelo menos um ponto.
    assert len(pontos) >= 1

    if len(pontos) > 1:
        chaves_com_localizacao_pendente.add(chave)
        linhas_com_localizacao_pendente += quantidade
    else:
        chaves_sem_divergencia_interna.add(chave)
        linhas_sem_divergencia_interna += quantidade


# Verifica que nenhuma chave ficou nos dois grupos.
assert chaves_com_localizacao_pendente.isdisjoint(
    chaves_sem_divergencia_interna
)

# Verifica que todas as chaves foram classificadas.
assert (
    chaves_com_localizacao_pendente
    | chaves_sem_divergencia_interna
) == set(contagem_por_boletim)

# Verifica que todas as linhas candidatas foram contabilizadas.
assert (
    linhas_com_localizacao_pendente
    + linhas_sem_divergencia_interna
    + linhas_sem_identificacao_boletim
    == total_candidatas
)


print("\n--- TRIAGEM DE LOCALIZAÇÃO ---")

print("Linhas candidatas:", total_candidatas)

print(
    "Combinações com coordenadas divergentes:",
    len(chaves_com_localizacao_pendente),
)
print(
    "Linhas separadas por divergência de localização:",
    linhas_com_localizacao_pendente,
)
print(
    "Linhas com identificação incompleta:",
    linhas_sem_identificacao_boletim,
)
print(
    "Combinações sem divergência interna de coordenadas:",
    len(chaves_sem_divergencia_interna),
)
print(
    "Linhas sem divergência interna de coordenadas:",
    linhas_sem_divergencia_interna,
)

print("PASSOU: Todas as linhas candidatas foram contabilizadas.")

print(
    "\nAs combinações com coordenadas divergentes "
    "ficam pendentes para avaliação espacial automática."
)
print(
    "Ausência de divergência interna não comprova "
    "que a localização esteja correta."
)
print(
    "Ainda é necessário verificar o limite geográfico "
    "do município e a qualidade da localização."
)
print(
    "A triagem foi realizada em memória. "
    "Nenhum registro da planilha foi alterado ou excluído."
)
# ============================================================
# CLASSIFICAÇÃO GEOGRÁFICA EXPERIMENTAL
# ============================================================

import hashlib
import json

from shapely.geometry import Point, Polygon, shape
from shapely.validation import explain_validity


def classificar_ponto_no_contorno(latitude, longitude, contorno):
    """
    Classifica a posição em relação ao contorno fornecido.

    A ordem de entrada é latitude, longitude.
    O Shapely recebe longitude, latitude.

    Não confirma a precisão do ponto nem a segurança do local.
    """
    ponto = Point(longitude, latitude)

    if contorno.contains(ponto):
        return "DENTRO_DO_CONTORNO"

    if contorno.touches(ponto):
        return "NA_BORDA_DO_CONTORNO"

    return "FORA_DO_CONTORNO"


# ------------------------------------------------------------
# TESTES COM UM POLÍGONO SIMULADO
# ------------------------------------------------------------

# Retângulo fictício:
# longitude entre 10 e 12; latitude entre 20 e 22.
contorno_teste = Polygon([
    (10, 20),
    (12, 20),
    (12, 22),
    (10, 22),
    (10, 20),
])

assert classificar_ponto_no_contorno(
    21, 11, contorno_teste
) == "DENTRO_DO_CONTORNO"

assert classificar_ponto_no_contorno(
    21, 13, contorno_teste
) == "FORA_DO_CONTORNO"

assert classificar_ponto_no_contorno(
    21, 10, contorno_teste
) == "NA_BORDA_DO_CONTORNO"

# Confere que a troca de latitude e longitude não passa despercebida.
assert classificar_ponto_no_contorno(
    11, 21, contorno_teste
) == "FORA_DO_CONTORNO"


# ------------------------------------------------------------
# CARREGAMENTO E VERIFICAÇÃO DO CONTORNO
# ------------------------------------------------------------

pasta_limites = (
    Path(__file__).resolve().parent
    / "backend"
    / "data"
    / "limites"
)

caminho_contorno = pasta_limites / "municipio_3550308.geojson"
caminho_metadados = pasta_limites / "municipio_3550308_fonte.json"

conteudo_contorno = caminho_contorno.read_bytes()

dados_contorno = json.loads(
    conteudo_contorno.decode("utf-8-sig")
)

metadados_contorno = json.loads(
    caminho_metadados.read_text(encoding="utf-8")
)

hash_contorno = hashlib.sha256(conteudo_contorno).hexdigest()

if hash_contorno != metadados_contorno.get("sha256"):
    raise ValueError(
        "O contorno foi alterado desde o download registrado."
    )

if dados_contorno.get("type") != "FeatureCollection":
    raise ValueError("O contorno deve ser um FeatureCollection.")

feicoes = dados_contorno.get("features")

if not isinstance(feicoes, list) or len(feicoes) != 1:
    raise ValueError("Era esperada uma única feição municipal.")

feicao = feicoes[0]

if str(feicao.get("properties", {}).get("codarea")) != "3550308":
    raise ValueError("Código municipal diferente do esperado.")

contorno_municipal = shape(feicao["geometry"])

if contorno_municipal.geom_type not in ("Polygon", "MultiPolygon"):
    raise ValueError("O contorno deve ser Polygon ou MultiPolygon.")

if contorno_municipal.is_empty:
    raise ValueError("O contorno está vazio.")

if not contorno_municipal.is_valid:
    raise ValueError(
        "Contorno inválido: "
        + explain_validity(contorno_municipal)
    )


# ------------------------------------------------------------
# CLASSIFICAÇÃO DAS COMBINAÇÕES SEM DIVERGÊNCIA
# ------------------------------------------------------------

linhas_por_posicao = Counter()
combinacoes_por_posicao = Counter()
classificacao_por_boletim = {}

for chave in chaves_sem_divergencia_interna:
    pontos = coordenadas_por_boletim[chave]

    # Cada combinação deste grupo deve ter exatamente um ponto.
    if len(pontos) != 1:
        raise ValueError(
            "Uma combinação sem divergência possui "
            "quantidade inesperada de pontos."
        )

    latitude, longitude = next(iter(pontos))

    classificacao = classificar_ponto_no_contorno(
        latitude,
        longitude,
        contorno_municipal,
    )

    classificacao_por_boletim[chave] = classificacao

    combinacoes_por_posicao[classificacao] += 1

    # Preserva a contagem de todas as linhas da combinação.
    linhas_por_posicao[classificacao] += contagem_por_boletim[chave]


# ------------------------------------------------------------
# CONFERÊNCIA DOS TOTAIS
# ------------------------------------------------------------

assert (
    sum(combinacoes_por_posicao.values())
    == len(chaves_sem_divergencia_interna)
)

assert (
    sum(linhas_por_posicao.values())
    == linhas_sem_divergencia_interna
)

assert (
    sum(linhas_por_posicao.values())
    + linhas_com_localizacao_pendente
    + linhas_sem_identificacao_boletim
    == total_candidatas
)

assert chaves_com_localizacao_pendente.isdisjoint(
    classificacao_por_boletim
)


# ------------------------------------------------------------
# RELATÓRIO
# ------------------------------------------------------------

print("\n--- CLASSIFICAÇÃO GEOGRÁFICA EXPERIMENTAL ---")
print("PASSOU: Testes com pontos dentro, fora e na borda.")
print("PASSOU: Teste da ordem latitude e longitude.")
print("PASSOU: Integridade e validade do contorno verificadas.")

for classificacao in (
    "DENTRO_DO_CONTORNO",
    "FORA_DO_CONTORNO",
    "NA_BORDA_DO_CONTORNO",
):
    print(f"\n{classificacao}")
    print(
        "Combinações provisórias:",
        combinacoes_por_posicao[classificacao],
    )
    print(
        "Linhas:",
        linhas_por_posicao[classificacao],
    )

print(
    "\nLinhas separadas por divergência de localização:",
    linhas_com_localizacao_pendente,
)
print(
    "Linhas com identificação incompleta:",
    linhas_sem_identificacao_boletim,
)
print("Total de linhas candidatas:", total_candidatas)

print("PASSOU: Todas as linhas candidatas foram contabilizadas.")

print(
    "\nResultado experimental: pressupõe compatibilidade "
    "entre as referências espaciais da planilha e do contorno."
)
print(
    "A referência espacial da planilha criminal "
    "ainda precisa ser confirmada."
)
print(
    "NA_BORDA indica contato geométrico com o contorno, "
    "sem uma faixa de tolerância em metros."
)
print(
    "Estar fora não confirma erro; estar dentro "
    "não confirma precisão nem segurança."
)
print(
    "Nenhum registro foi excluído. "
    "A classificação foi mantida apenas em memória."
)
