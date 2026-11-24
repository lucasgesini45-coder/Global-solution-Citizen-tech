import csv
import hashlib
import json
import math
import unicodedata

from collections import Counter
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from pyproj import CRS, Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

from backend.src.geografia import (
    calcular_distancia_metros,
    classificar_ponto_no_contorno,
    validar_contorno,
)
from backend.src.seguranca import avaliar_atualidade


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if valor is None:
        return ""

    texto = unicodedata.normalize(
        "NFKD", str(valor).strip().upper()
    )

    texto = "".join(
        letra
        for letra in texto
        if not unicodedata.combining(letra)
    )

    return " ".join(texto.split())


def esta_ausente(valor):
    return normalizar_texto(valor) in ("", "NULL", "NONE")


def converter_numero(valor):
    return float(str(valor).strip().replace(",", "."))


def verificar_coordenadas(latitude, longitude):
    """Verifica formato e limites, sem confirmar localização."""
    if esta_ausente(latitude) or esta_ausente(longitude):
        return "AUSENTES"

    valores = []

    for valor in (latitude, longitude):
        if isinstance(valor, bool):
            return "INVALIDAS"

        try:
            numero = converter_numero(valor)
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


def obter_dia(valor):
    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    return None


def conferir(condicao, mensagem):
    """Interrompe a execução se uma conferência falhar."""
    if not condicao:
        raise ValueError(mensagem)


def carregar_contorno(pasta, codigo):
    caminho_geojson = pasta / f"municipio_{codigo}.geojson"
    caminho_fonte = pasta / f"municipio_{codigo}_fonte.json"

    conteudo = caminho_geojson.read_bytes()
    dados = json.loads(conteudo.decode("utf-8-sig"))
    fonte = json.loads(caminho_fonte.read_text(encoding="utf-8"))

    hash_atual = hashlib.sha256(conteudo).hexdigest()

    conferir(
        hash_atual == fonte.get("sha256"),
        "O contorno difere do download registrado.",
    )
    conferir(
        dados.get("type") == "FeatureCollection",
        "Era esperado um FeatureCollection.",
    )

    feicoes = dados.get("features")

    conferir(
        isinstance(feicoes, list) and len(feicoes) == 1,
        "Era esperada exatamente uma feição municipal.",
    )

    feicao = feicoes[0]

    conferir(
        str(feicao.get("properties", {}).get("codarea")) == codigo,
        "Código do município diferente do esperado.",
    )

    contorno = shape(feicao["geometry"])
    validar_contorno(contorno)

    return contorno, hash_atual


def proteger_celula_csv(valor):
    if isinstance(valor, str):
        if valor.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + valor

    return valor


# ============================================================
# CONFIGURAÇÕES
# ============================================================

raiz_projeto = Path(__file__).resolve().parent

caminho = (
    Path.home()
    / "Downloads"
    / "SPDadosCriminais_2026.xlsx"
)

municipio_alvo = normalizar_texto("S.PAULO")
codigo_municipio = "3550308"

abas_dados = ["JAN-JUN_2026", "JUL-DEZ_2026"]

campos_datas = ["DATA_OCORRENCIA_BO", "DATA_REGISTRO"]

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

data_consulta = date.today()
janela_dias = 90

situacoes_coordenadas = (
    "LIMITES_VALIDOS",
    "AUSENTES",
    "INVALIDAS",
    "SUSPEITAS_ZERO",
)

situacoes_geograficas = (
    "DENTRO_DO_CONTORNO",
    "FORA_DO_CONTORNO",
    "NA_BORDA_DO_CONTORNO",
)

pasta_limites = raiz_projeto / "backend" / "data" / "limites"

# Confere o contorno antes de percorrer a planilha grande.
contorno_municipal, hash_contorno = carregar_contorno(
    pasta_limites,
    codigo_municipio,
)


# ============================================================
# CONTADORES
# ============================================================

categorias = Counter()
tipos_locais = Counter()
municipios_encontrados = Counter()
qualidade_coordenadas = Counter()
resultados_atualidade = Counter()
recentes_por_coordenadas = Counter()
anos_ocorrencias = Counter()

total_municipio = 0
sem_categoria = 0
datas_invertidas = 0

tipos_datas = {campo: Counter() for campo in campos_datas}
exemplos_datas = {campo: [] for campo in campos_datas}
menores_datas = {campo: None for campo in campos_datas}
maiores_datas = {campo: None for campo in campos_datas}

linhas_vistas = set()
total_candidatas = 0
duplicatas_exatas = 0

contagem_por_boletim = Counter()
naturezas_por_boletim = {}
datas_por_boletim = {}
coordenadas_por_boletim = {}

linhas_sem_identificacao_boletim = 0
linhas_sem_natureza_boletim = 0


# ============================================================
# LEITURA DA PLANILHA
# ============================================================

if not caminho.is_file():
    raise FileNotFoundError(f"Planilha não encontrada: {caminho}")

print("Abrindo a planilha...", flush=True)
print("Data da consulta:", data_consulta)
print("Janela temporal:", janela_dias, "dias")

planilha = load_workbook(
    caminho,
    read_only=True,
    data_only=True,
)

try:
    for nome_aba in abas_dados:
        conferir(
            nome_aba in planilha.sheetnames,
            f"Aba não encontrada: {nome_aba}",
        )

        print(f"\nLendo aba: {nome_aba}", flush=True)

        linhas = planilha[nome_aba].iter_rows(values_only=True)
        cabecalho = next(linhas, None)

        conferir(
            cabecalho is not None,
            f"A aba {nome_aba} está vazia.",
        )

        colunas = {}

        for indice, nome in enumerate(cabecalho):
            nome = normalizar_texto(nome)

            if not nome:
                continue

            conferir(
                nome not in colunas,
                f"Coluna repetida na aba {nome_aba}: {nome}",
            )
            colunas[nome] = indice

        ausentes = [
            campo
            for campo in campos_obrigatorios
            if campo not in colunas
        ]

        conferir(
            not ausentes,
            f"Campos ausentes em {nome_aba}: {', '.join(ausentes)}",
        )

        colunas_assinatura = sorted(colunas.items())
        total_aba = 0

        for numero, linha in enumerate(linhas, start=1):
            if numero % 50000 == 0:
                print(
                    f"  {numero} linhas percorridas...",
                    flush=True,
                )

            if all(valor is None for valor in linha):
                continue

            municipio = normalizar_texto(
                linha[colunas["NOME_MUNICIPIO_CIRCUNSCRICAO"]]
            )
            municipios_encontrados[municipio] += 1

            if municipio != municipio_alvo:
                continue

            total_aba += 1
            total_municipio += 1

            # Tipos, exemplos e intervalos de datas.
            for campo in campos_datas:
                valor = linha[colunas[campo]]

                if esta_ausente(valor):
                    tipos_datas[campo]["AUSENTE"] += 1
                else:
                    tipos_datas[campo][type(valor).__name__] += 1
                    exemplo = repr(valor)

                    if (
                        len(exemplos_datas[campo]) < 3
                        and exemplo not in exemplos_datas[campo]
                    ):
                        exemplos_datas[campo].append(exemplo)

                dia = obter_dia(valor)

                if dia is not None:
                    if (
                        menores_datas[campo] is None
                        or dia < menores_datas[campo]
                    ):
                        menores_datas[campo] = dia

                    if (
                        maiores_datas[campo] is None
                        or dia > maiores_datas[campo]
                    ):
                        maiores_datas[campo] = dia

                    if campo == "DATA_OCORRENCIA_BO":
                        anos_ocorrencias[dia.year] += 1

            data_fato = linha[colunas["DATA_OCORRENCIA_BO"]]
            data_registro = linha[colunas["DATA_REGISTRO"]]

            dia_fato = obter_dia(data_fato)
            dia_registro = obter_dia(data_registro)

            if dia_fato is not None and dia_registro is not None:
                if dia_fato > dia_registro:
                    datas_invertidas += 1

            avaliacao = avaliar_atualidade(
                data_fato,
                data_registro,
                data_consulta,
                janela_dias=janela_dias,
            )
            resultados_atualidade[avaliacao["motivo"]] += 1

            latitude_original = linha[colunas["LATITUDE"]]
            longitude_original = linha[colunas["LONGITUDE"]]

            situacao = verificar_coordenadas(
                latitude_original,
                longitude_original,
            )
            qualidade_coordenadas[situacao] += 1

            if avaliacao["apta"]:
                recentes_por_coordenadas[situacao] += 1

            natureza_original = linha[colunas["NATUREZA_APURADA"]]

            # Candidatas à investigação geográfica.
            if avaliacao["apta"] and situacao == "LIMITES_VALIDOS":
                total_candidatas += 1

                assinatura = tuple(
                    (nome, linha[indice])
                    for nome, indice in colunas_assinatura
                )

                if assinatura in linhas_vistas:
                    duplicatas_exatas += 1
                else:
                    linhas_vistas.add(assinatura)

                chave = tuple(
                    normalizar_texto(linha[colunas[campo]])
                    for campo in ("NOME_DELEGACIA", "ANO_BO", "NUM_BO")
                )

                if any(esta_ausente(valor) for valor in chave):
                    linhas_sem_identificacao_boletim += 1
                else:
                    contagem_por_boletim[chave] += 1

                    if chave not in naturezas_por_boletim:
                        naturezas_por_boletim[chave] = set()
                        datas_por_boletim[chave] = set()
                        coordenadas_por_boletim[chave] = set()

                    conferir(
                        dia_fato is not None,
                        "Linha temporalmente apta sem data válida.",
                    )
                    datas_por_boletim[chave].add(dia_fato)

                    coordenadas_por_boletim[chave].add((
                        converter_numero(latitude_original),
                        converter_numero(longitude_original),
                    ))

                    if esta_ausente(natureza_original):
                        linhas_sem_natureza_boletim += 1
                    else:
                        naturezas_por_boletim[chave].add(
                            normalizar_texto(natureza_original)
                        )

            local = normalizar_texto(
                linha[colunas["DESCR_TIPOLOCAL"]]
            )

            if esta_ausente(local):
                local = "SEM INFORMACAO"

            tipos_locais[local] += 1

            if esta_ausente(natureza_original):
                sem_categoria += 1
            else:
                categorias[str(natureza_original).strip()] += 1

        print(f"Linhas de São Paulo nesta aba: {total_aba}")

finally:
    planilha.close()


# ============================================================
# CONFERÊNCIAS DA LEITURA
# ============================================================

for nome, total in (
    ("tipos de local", sum(tipos_locais.values())),
    ("categorias", sum(categorias.values()) + sem_categoria),
    ("coordenadas", sum(qualidade_coordenadas.values())),
    ("atualidade", sum(resultados_atualidade.values())),
):
    conferir(
        total == total_municipio,
        f"Contagem inconsistente: {nome}.",
    )

for campo in campos_datas:
    conferir(
        sum(tipos_datas[campo].values()) == total_municipio,
        f"Contagem inconsistente: {campo}.",
    )

conferir(
    sum(recentes_por_coordenadas.values())
    == resultados_atualidade["DENTRO_DA_JANELA"],
    "Contagem inconsistente das coordenadas recentes.",
)

conferir(
    len(linhas_vistas) + duplicatas_exatas == total_candidatas,
    "Contagem inconsistente das duplicidades.",
)

conferir(
    total_candidatas == recentes_por_coordenadas["LIMITES_VALIDOS"],
    "Contagem inconsistente das linhas candidatas.",
)

conferir(
    sum(contagem_por_boletim.values())
    + linhas_sem_identificacao_boletim
    == total_candidatas,
    "Contagem inconsistente dos identificadores.",
)


# ============================================================
# RELATÓRIOS DA LEITURA
# ============================================================

print("\n--- TIPOS DE LOCAL EM SÃO PAULO ---")
for local, quantidade in tipos_locais.most_common():
    print(f"{local}: {quantidade}")

print("\n--- CATEGORIAS EM SÃO PAULO ---")
for categoria, quantidade in categorias.most_common():
    print(f"{categoria}: {quantidade}")

print("Total de linhas de São Paulo:", total_municipio)
print("Linhas sem categoria:", sem_categoria)
print("Categorias distintas:", len(categorias))
print("Atenção: linhas não equivalem a ocorrências únicas.")

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

print("Limites numéricos válidos não confirmam localização.")

print("\n--- DIAGNÓSTICO DAS DATAS ---")
for campo in campos_datas:
    print(f"\nCampo: {campo}")
    for tipo, quantidade in tipos_datas[campo].most_common():
        print(f"{tipo}: {quantidade}")
    print("Exemplos:")
    for exemplo in exemplos_datas[campo]:
        print(exemplo)

print("\n--- INTERVALO DAS DATAS ---")
for campo in campos_datas:
    print(f"\nCampo: {campo}")
    print("Menor data:", menores_datas[campo])
    print("Maior data:", maiores_datas[campo])

print("Intervalos consideram valores date e datetime.")
print("Os extremos não garantem cobertura completa dos dias.")

print("\n--- ANOS DOS FATOS REGISTRADOS ---")
for ano, quantidade in sorted(anos_ocorrencias.items()):
    print(f"{ano}: {quantidade}")

print("\n--- CONSISTÊNCIA DAS DATAS ---")
print("Linhas com fato posterior ao registro:", datas_invertidas)

print("\n--- ATUALIDADE DOS DADOS ---")
print("Data da consulta:", data_consulta)
print("Janela de análise em dias:", janela_dias)

for motivo, quantidade in resultados_atualidade.most_common():
    print(f"{motivo}: {quantidade}")

ultima_data = maiores_datas["DATA_REGISTRO"]

if ultima_data is not None:
    print("Maior data de registro encontrada:", ultima_data)
    print(
        "Diferença em dias até a consulta:",
        (data_consulta - ultima_data).days,
    )

print("A maior data de registro não comprova atualização da fonte.")

print("\n--- COORDENADAS DAS LINHAS RECENTES ---")
for situacao in situacoes_coordenadas:
    print(f"{situacao}: {recentes_por_coordenadas[situacao]}")

print("\n--- DUPLICIDADES EXATAS ---")
print("Linhas candidatas:", total_candidatas)
print("Repetições exatas:", duplicatas_exatas)
print("Linhas distintas:", len(linhas_vistas))
print("PASSOU: Conferências dos totais da leitura.")


# ============================================================
# IDENTIFICAÇÃO E CONSISTÊNCIA DOS BOLETINS
# ============================================================

combinacoes_repetidas = 0
linhas_repetidas = 0
multiplas_naturezas = 0
consistencia = Counter()

for chave, quantidade in contagem_por_boletim.items():
    if len(naturezas_por_boletim[chave]) > 1:
        multiplas_naturezas += 1

    if quantidade <= 1:
        continue

    combinacoes_repetidas += 1
    linhas_repetidas += quantidade

    datas_diferentes = len(datas_por_boletim[chave]) > 1
    pontos_diferentes = len(coordenadas_por_boletim[chave]) > 1

    if datas_diferentes and pontos_diferentes:
        consistencia["DATAS_E_COORDENADAS_DIFERENTES"] += 1
    elif datas_diferentes:
        consistencia["SOMENTE_DATAS_DIFERENTES"] += 1
    elif pontos_diferentes:
        consistencia["SOMENTE_COORDENADAS_DIFERENTES"] += 1
    else:
        consistencia["MESMA_DATA_MESMO_PONTO"] += 1

conferir(
    sum(consistencia.values()) == combinacoes_repetidas,
    "Contagem inconsistente das combinações repetidas.",
)

print("\n--- IDENTIFICAÇÃO DOS BOLETINS ---")
print("Linhas candidatas:", total_candidatas)
print(
    "Linhas com identificação preenchida:",
    sum(contagem_por_boletim.values()),
)
print("Linhas com identificação incompleta:", linhas_sem_identificacao_boletim)
print("Combinações distintas:", len(contagem_por_boletim))
print("Combinações repetidas:", combinacoes_repetidas)
print("Linhas nessas combinações:", linhas_repetidas)
print("Combinações com mais de uma natureza:", multiplas_naturezas)
print("Linhas identificadas sem natureza:", linhas_sem_natureza_boletim)
print("A chave delegacia + ano + número é provisória.")

print("\n--- CONSISTÊNCIA DAS COMBINAÇÕES REPETIDAS ---")
for situacao in (
    "MESMA_DATA_MESMO_PONTO",
    "SOMENTE_DATAS_DIFERENTES",
    "SOMENTE_COORDENADAS_DIFERENTES",
    "DATAS_E_COORDENADAS_DIFERENTES",
):
    print(f"{situacao}: {consistencia[situacao]}")

print("A comparação das datas considera o dia, sem horário.")


# ============================================================
# DISTÂNCIA ENTRE PONTOS DIVERGENTES E TRIAGEM
# ============================================================

chaves_com_localizacao_pendente = set()
chaves_sem_divergencia_interna = set()

linhas_com_localizacao_pendente = 0
linhas_sem_divergencia_interna = 0

print("\n--- DISTÂNCIA ENTRE PONTOS DIVERGENTES ---")

for chave in sorted(contagem_por_boletim):
    pontos = sorted(coordenadas_por_boletim[chave])
    quantidade = contagem_por_boletim[chave]

    conferir(bool(pontos), "Combinação sem coordenadas.")

    if len(pontos) == 1:
        chaves_sem_divergencia_interna.add(chave)
        linhas_sem_divergencia_interna += quantidade
        continue

    chaves_com_localizacao_pendente.add(chave)
    linhas_com_localizacao_pendente += quantidade

    distancias = [
        calcular_distancia_metros(pontos[a], pontos[b])
        for a in range(len(pontos))
        for b in range(a + 1, len(pontos))
    ]

    print(
        f"\nCombinação divergente "
        f"{len(chaves_com_localizacao_pendente)}:"
    )
    print("Linhas:", quantidade)
    print("Pontos distintos:", len(pontos))
    print("Pares comparados:", len(distancias))
    print(f"Menor distância: {min(distancias):.2f} metros")
    print(f"Maior distância: {max(distancias):.2f} metros")

conferir(
    linhas_com_localizacao_pendente
    + linhas_sem_divergencia_interna
    + linhas_sem_identificacao_boletim
    == total_candidatas,
    "Contagem inconsistente da triagem.",
)

print("\n--- TRIAGEM DE LOCALIZAÇÃO ---")
print("Linhas candidatas:", total_candidatas)
print(
    "Combinações com coordenadas divergentes:",
    len(chaves_com_localizacao_pendente),
)
print("Linhas separadas por divergência:", linhas_com_localizacao_pendente)
print("Linhas sem identificação:", linhas_sem_identificacao_boletim)
print(
    "Combinações sem divergência interna:",
    len(chaves_sem_divergencia_interna),
)
print("Linhas sem divergência interna:", linhas_sem_divergencia_interna)
print("PASSOU: Todas as linhas candidatas foram contabilizadas.")


# ============================================================
# CLASSIFICAÇÃO GEOGRÁFICA EXPERIMENTAL
# ============================================================

linhas_por_posicao = Counter()
combinacoes_por_posicao = Counter()
classificacao_por_boletim = {}

for chave in sorted(chaves_sem_divergencia_interna):
    latitude, longitude = next(iter(coordenadas_por_boletim[chave]))

    classificacao = classificar_ponto_no_contorno(
        latitude,
        longitude,
        contorno_municipal,
    )

    classificacao_por_boletim[chave] = classificacao
    combinacoes_por_posicao[classificacao] += 1
    linhas_por_posicao[classificacao] += contagem_por_boletim[chave]

conferir(
    sum(linhas_por_posicao.values()) == linhas_sem_divergencia_interna,
    "Contagem inconsistente da classificação geográfica.",
)
conferir(
    sum(combinacoes_por_posicao.values())
    == len(chaves_sem_divergencia_interna),
    "Contagem inconsistente das combinações geográficas.",
)

print("\n--- CLASSIFICAÇÃO GEOGRÁFICA EXPERIMENTAL ---")

for situacao in situacoes_geograficas:
    print(f"\n{situacao}")
    print("Combinações provisórias:", combinacoes_por_posicao[situacao])
    print("Linhas:", linhas_por_posicao[situacao])

print("\nLinhas divergentes separadas:", linhas_com_localizacao_pendente)
print("Linhas sem identificação:", linhas_sem_identificacao_boletim)
print("Total de linhas candidatas:", total_candidatas)
print("PASSOU: Totais da classificação conferidos.")
print("A classificação pressupõe referências espaciais compatíveis.")
print("A referência da planilha criminal permanece não confirmada.")
print("A borda é geométrica, sem tolerância em metros.")


# ============================================================
# DISTÂNCIA DOS PONTOS EXTERNOS
# ============================================================

oeste, sul, leste, norte = contorno_municipal.bounds

projecao_local = CRS.from_proj4(
    f"+proj=aeqd "
    f"+lat_0={(sul + norte) / 2} "
    f"+lon_0={(oeste + leste) / 2} "
    "+datum=WGS84 +units=m +no_defs"
)

transformador = Transformer.from_crs(
    "EPSG:4326",
    projecao_local,
    always_xy=True,
)


def projetar_coordenadas(x, y, z=None):
    return transformador.transform(x, y, errcheck=True)


contorno_em_metros = transform(
    projetar_coordenadas,
    contorno_municipal,
)
validar_contorno(contorno_em_metros)

distancias_por_boletim = {}
faixas_distancia = Counter()

print("\n--- DISTÂNCIA DOS PONTOS EXTERNOS ---")
print("Hipótese experimental: coordenadas de entrada em WGS 84.")

for chave in sorted(classificacao_por_boletim):
    if classificacao_por_boletim[chave] != "FORA_DO_CONTORNO":
        continue

    latitude, longitude = next(iter(coordenadas_por_boletim[chave]))

    x, y = transformador.transform(
        longitude,
        latitude,
        errcheck=True,
    )

    conferir(
        math.isfinite(x) and math.isfinite(y),
        "A projeção produziu coordenadas não finitas.",
    )

    distancia = Point(x, y).distance(contorno_em_metros.boundary)

    conferir(
        math.isfinite(distancia),
        "A distância calculada não é finita.",
    )

    distancias_por_boletim[chave] = distancia

    if distancia <= 100:
        faixa = "ATE_100_METROS"
    elif distancia <= 1000:
        faixa = "MAIS_DE_100_ATE_1000_METROS"
    else:
        faixa = "MAIS_DE_1000_METROS"

    quantidade = contagem_por_boletim[chave]
    faixas_distancia[faixa] += quantidade

    print(
        f"Combinação externa {len(distancias_por_boletim)}: "
        f"{distancia:.1f} metros; {quantidade} linha(s)."
    )

conferir(
    len(distancias_por_boletim)
    == combinacoes_por_posicao["FORA_DO_CONTORNO"],
    "Contagem inconsistente das distâncias externas.",
)
conferir(
    sum(faixas_distancia.values())
    == linhas_por_posicao["FORA_DO_CONTORNO"],
    "Contagem inconsistente das faixas de distância.",
)

print("\nLinhas por faixa de distância:")
for faixa in (
    "ATE_100_METROS",
    "MAIS_DE_100_ATE_1000_METROS",
    "MAIS_DE_1000_METROS",
):
    print(f"{faixa}: {faixas_distancia[faixa]}")

if distancias_por_boletim:
    print(
        f"Menor distância: "
        f"{min(distancias_por_boletim.values()):.1f} metros"
    )
    print(
        f"Maior distância: "
        f"{max(distancias_por_boletim.values()):.1f} metros"
    )

print("PASSOU: Todos os registros externos foram contabilizados.")
print("Distâncias aproximadas na projeção local, não por ruas.")
print("As faixas não são limites automáticos de aceitação.")


# ============================================================
# EXPORTAÇÃO LOCAL DAS PENDÊNCIAS
# ============================================================

def montar_linha_revisao(chave, motivo):
    delegacia, ano_bo, numero_bo = chave

    distancia = distancias_por_boletim.get(chave)

    return {
        "motivo": motivo,
        "delegacia": delegacia,
        "ano_bo": ano_bo,
        "numero_bo": numero_bo,
        "quantidade_linhas": contagem_por_boletim[chave],
        "datas_fato": json.dumps([
            dia.isoformat()
            for dia in sorted(datas_por_boletim[chave])
        ]),
        "naturezas": json.dumps(
            sorted(naturezas_por_boletim[chave]),
            ensure_ascii=False,
        ),
        "pontos_latitude_longitude": json.dumps(
            sorted(coordenadas_por_boletim[chave])
        ),
        "distancia_aproximada_borda_m": (
            round(distancia, 1) if distancia is not None else ""
        ),
        "situacao_revisao": "PENDENTE",
        "observacao_revisor": "",
    }


pendencias_revisao = []

for chave in sorted(chaves_com_localizacao_pendente):
    pendencias_revisao.append(
        montar_linha_revisao(chave, "COORDENADAS_DIVERGENTES")
    )

for chave in sorted(distancias_por_boletim):
    pendencias_revisao.append(
        montar_linha_revisao(chave, "FORA_DO_CONTORNO")
    )

total_linhas_representadas = sum(
    item["quantidade_linhas"]
    for item in pendencias_revisao
)

conferir(
    len(pendencias_revisao)
    == len(chaves_com_localizacao_pendente)
    + combinacoes_por_posicao["FORA_DO_CONTORNO"],
    "Quantidade inconsistente de pendências.",
)
conferir(
    total_linhas_representadas
    == linhas_com_localizacao_pendente
    + linhas_por_posicao["FORA_DO_CONTORNO"],
    "Quantidade inconsistente de linhas representadas.",
)

instante_exportacao = datetime.now().astimezone()

pasta_revisao = (
    Path.home()
    / "Downloads"
    / "rotaviva_revisao_local"
    / instante_exportacao.strftime("%Y%m%d_%H%M%S_%f")
)
pasta_revisao.mkdir(parents=True, exist_ok=False)

caminho_csv = pasta_revisao / "pendencias_geograficas.csv"

campos_csv = [
    "motivo",
    "delegacia",
    "ano_bo",
    "numero_bo",
    "quantidade_linhas",
    "datas_fato",
    "naturezas",
    "pontos_latitude_longitude",
    "distancia_aproximada_borda_m",
    "situacao_revisao",
    "observacao_revisor",
]

with caminho_csv.open(
    "w", encoding="utf-8-sig", newline=""
) as arquivo:
    escritor = csv.DictWriter(
        arquivo,
        fieldnames=campos_csv,
        delimiter=";",
    )
    escritor.writeheader()

    for item in pendencias_revisao:
        escritor.writerow({
            campo: proteger_celula_csv(valor)
            for campo, valor in item.items()
        })

contexto_revisao = {
    "gerado_em": instante_exportacao.isoformat(),
    "data_consulta": data_consulta.isoformat(),
    "janela_dias": janela_dias,
    "arquivo_criminal": caminho.name,
    "abas_analisadas": abas_dados,
    "municipio_filtro": municipio_alvo,
    "codigo_municipio_contorno": codigo_municipio,
    "sha256_contorno": hash_contorno,
    "quantidade_combinacoes_pendentes": len(pendencias_revisao),
    "quantidade_linhas_representadas": total_linhas_representadas,
    "hipotese_espacial": "WGS84_NAO_CONFIRMADO_PARA_BASE_CRIMINAL",
    "projecao_distancias": projecao_local.to_string(),
    "limitacoes": [
        "Identificação dos boletins provisória.",
        "Distâncias aproximadas até a malha baixada.",
        "Resumo não preserva associações entre campos de cada linha.",
        "Nenhuma correção automática aplicada.",
        "CSV para revisão local, não para publicação no aplicativo.",
        "Hash do arquivo criminal ainda não registrado.",
        "Não há cálculo de segurança das rotas nesta etapa.",
    ],
}

caminho_contexto = pasta_revisao / "contexto_revisao.json"

caminho_contexto.write_text(
    json.dumps(contexto_revisao, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

with caminho_csv.open(
    "r", encoding="utf-8-sig", newline=""
) as arquivo:
    quantidade_gravada = sum(
        1 for _ in csv.DictReader(arquivo, delimiter=";")
    )

conferir(
    quantidade_gravada == len(pendencias_revisao),
    "Quantidade gravada no CSV diferente da esperada.",
)

print("\n--- RELATÓRIO LOCAL DE PENDÊNCIAS ---")
print("Combinações para revisão:", len(pendencias_revisao))
print("Linhas originais representadas:", total_linhas_representadas)
print("CSV salvo em:", caminho_csv)
print("Contexto salvo em:", caminho_contexto)
print("PASSOU: Todas as combinações foram gravadas.")
print("A planilha original não foi alterada.")

if total_municipio == 0:
    print(
        "\nATENÇÃO: Nenhuma linha passou pelo filtro municipal. "
        "Confira a fonte e o nome do município."
    )