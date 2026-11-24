import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import shape
from shapely.validation import explain_validity


def validar_limite():
    pasta = (
        Path(__file__).resolve().parent
        / "backend"
        / "data"
        / "limites"
    )

    caminho_geojson = pasta / "municipio_3550308.geojson"
    caminho_fonte = pasta / "municipio_3550308_fonte.json"

    for caminho in (caminho_geojson, caminho_fonte):
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho}"
            )

    conteudo = caminho_geojson.read_bytes()

    dados = json.loads(conteudo.decode("utf-8-sig"))
    fonte = json.loads(caminho_fonte.read_text(encoding="utf-8"))

    # Confirma que o arquivo corresponde ao download registrado.
    hash_atual = hashlib.sha256(conteudo).hexdigest()

    if hash_atual != fonte.get("sha256"):
        raise ValueError(
            "O arquivo difere do download registrado nos metadados."
        )

    if dados.get("type") != "FeatureCollection":
        raise ValueError("Era esperado um FeatureCollection.")

    elementos = dados.get("features")

    if not isinstance(elementos, list) or len(elementos) != 1:
        raise ValueError(
            "Este diagnóstico espera exatamente uma feição municipal."
        )

    elemento = elementos[0]
    propriedades = elemento.get("properties") or {}

    if str(propriedades.get("codarea")) != "3550308":
        raise ValueError("O código recebido não corresponde ao esperado.")

    geometria_json = elemento.get("geometry")

    if not isinstance(geometria_json, dict):
        raise ValueError("Geometria ausente ou inválida.")

    tipo = geometria_json.get("type")

    if tipo not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"Tipo de geometria inesperado: {tipo}")

    coordenadas = geometria_json.get("coordinates")

    if not isinstance(coordenadas, list) or not coordenadas:
        raise ValueError("Coordenadas ausentes.")

    # Uniformiza a estrutura para percorrer Polygon e MultiPolygon.
    if tipo == "Polygon":
        poligonos = [coordenadas]
    else:
        poligonos = coordenadas

    total_aneis = 0
    total_posicoes = 0
    exemplos = []

    for poligono in poligonos:
        if not isinstance(poligono, list) or not poligono:
            raise ValueError("Polígono sem anéis.")

        for anel in poligono:
            total_aneis += 1

            if not isinstance(anel, list) or len(anel) < 4:
                raise ValueError(
                    "Um anel deve possuir pelo menos quatro posições."
                )

            if anel[0] != anel[-1]:
                raise ValueError(
                    "Anel aberto: a primeira e a última posição diferem."
                )

            for posicao in anel:
                if not isinstance(posicao, list) or len(posicao) != 2:
                    raise ValueError(
                        "Este diagnóstico espera posições com dois números."
                    )

                longitude, latitude = posicao

                for valor in (longitude, latitude):
                    if (
                        isinstance(valor, bool)
                        or not isinstance(valor, (int, float))
                        or not math.isfinite(valor)
                    ):
                        raise ValueError(
                            "Coordenada não numérica ou não finita."
                        )

                if not -180 <= longitude <= 180:
                    raise ValueError("Longitude fora dos limites.")

                if not -90 <= latitude <= 90:
                    raise ValueError("Latitude fora dos limites.")

                total_posicoes += 1

                if len(exemplos) < 3:
                    exemplos.append(posicao)

    geometria = shape(geometria_json)

    if geometria.is_empty:
        raise ValueError("A geometria está vazia.")

    if not geometria.is_valid:
        raise ValueError(
            "Geometria inválida: "
            + explain_validity(geometria)
        )

    oeste, sul, leste, norte = geometria.bounds

    print("\n--- VALIDAÇÃO DO CONTORNO MUNICIPAL ---")
    print("Código do município:", propriedades["codarea"])
    print("Tipo de geometria:", geometria.geom_type)
    print("Quantidade de polígonos:", len(poligonos))
    print("Quantidade de anéis:", total_aneis)
    print("Posições verificadas:", total_posicoes)

    print("\nExtremos numéricos, interpretados como longitude e latitude:")
    print(f"Longitude mínima: {oeste:.6f}")
    print(f"Longitude máxima: {leste:.6f}")
    print(f"Latitude mínima: {sul:.6f}")
    print(f"Latitude máxima: {norte:.6f}")

    print("\nExemplos de posições [longitude, latitude]:")
    for exemplo in exemplos:
        print(exemplo)

    print("\nReferência espacial declarada:", dados.get("crs"))
    print("Fonte registrada:", fonte.get("fonte"))
    print("URL registrada:", fonte.get("url"))
    print("Data de coleta:", fonte.get("coletado_em_utc"))

    print("\nPASSOU: Arquivo corresponde ao hash da coleta.")
    print("PASSOU: Estrutura e limites numéricos verificados.")
    print("PASSOU: Anéis fechados e geometria válida.")

    print(
        "\nA validade geométrica não comprova a precisão "
        "nem a referência temporal do contorno."
    )
    print(
        "A interpretação longitude/latitude segue a convenção "
        "do GeoJSON; os extremos serão conferidos antes do cruzamento."
    )
    print(
        "Também precisamos confirmar a referência espacial "
        "das coordenadas da planilha criminal."
    )
    print("Nenhum arquivo foi alterado.")


if __name__ == "__main__":
    validar_limite()