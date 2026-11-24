import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Configuração específica desta fonte.
codigo_municipio = "3550308"

url = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/"
    f"{codigo_municipio}"
    "?formato=application/vnd.geo+json"
    "&qualidade=maxima"
)

pasta_destino = (
    Path(__file__).resolve().parent
    / "backend"
    / "data"
    / "limites"
)

arquivo_geojson = (
    pasta_destino / f"municipio_{codigo_municipio}.geojson"
)

arquivo_metadados = (
    pasta_destino / f"municipio_{codigo_municipio}_fonte.json"
)


def baixar_limite():
    # Evita substituir uma versão já existente sem revisão.
    if arquivo_geojson.exists() or arquivo_metadados.exists():
        print("Já existe um arquivo de limite ou de metadados.")
        print("Nenhum arquivo foi substituído.")
        print("Pasta:", pasta_destino)
        return

    print("Consultando o serviço de malhas do IBGE...", flush=True)

    requisicao = Request(
        url,
        headers={
            "User-Agent": "RotaViva-ProjetoAcademico/1.0",
            "Accept": "application/geo+json, application/json",
        },
    )

    try:
        with urlopen(requisicao, timeout=90) as resposta:
            conteudo = resposta.read()
            tipo_conteudo = resposta.headers.get("Content-Type")
            ultima_modificacao = resposta.headers.get("Last-Modified")

    except HTTPError as erro:
        print(f"Download não realizado: HTTP {erro.code}.")
        print("Nenhum arquivo foi criado.")
        return

    except (URLError, TimeoutError) as erro:
        print("Não foi possível acessar o serviço:", erro)
        print("Nenhum arquivo foi criado.")
        return

    try:
        dados = json.loads(conteudo.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print("A resposta recebida não é um JSON válido.")
        print("Nenhum arquivo foi criado.")
        return

    if not isinstance(dados, dict):
        print("Estrutura inesperada: o JSON não é um objeto.")
        return

    if dados.get("type") != "FeatureCollection":
        print("Estrutura inesperada:", dados.get("type"))
        print("Era esperado um GeoJSON do tipo FeatureCollection.")
        return

    elementos = dados.get("features")

    if not isinstance(elementos, list) or not elementos:
        print("O arquivo não contém uma lista de feições preenchida.")
        return

    tipos_geometria = set()

    for elemento in elementos:
        if not isinstance(elemento, dict):
            print("Foi encontrada uma feição inválida.")
            return

        propriedades = elemento.get("properties") or {}
        geometria = elemento.get("geometry") or {}

        if not isinstance(propriedades, dict):
            print("As propriedades da feição são inválidas.")
            return

        if not isinstance(geometria, dict):
            print("A geometria da feição é inválida.")
            return

        codigo_recebido = str(propriedades.get("codarea", ""))

        if codigo_recebido != codigo_municipio:
            print("Código do município diferente do esperado.")
            print("Esperado:", codigo_municipio)
            print("Recebido:", codigo_recebido)
            return

        tipo = geometria.get("type")

        if tipo not in ("Polygon", "MultiPolygon"):
            print("Tipo de geometria inesperado:", tipo)
            return

        coordenadas = geometria.get("coordinates")

        if not isinstance(coordenadas, list) or not coordenadas:
            print("A geometria não contém coordenadas preenchidas.")
            return

        tipos_geometria.add(tipo)

    metadados = {
        "fonte": "IBGE - API de Malhas",
        "url": url,
        "codigo_municipio": codigo_municipio,
        "coletado_em_utc": datetime.now(timezone.utc).isoformat(),
        "tipo_conteudo_http": tipo_conteudo,
        "ultima_modificacao_http": ultima_modificacao,
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "quantidade_feicoes": len(elementos),
        "tipos_geometria": sorted(tipos_geometria),
        "crs_informado_no_arquivo": dados.get("crs"),
        "situacao": "BAIXADO_COM_VERIFICACAO_ESTRUTURAL_BASICA",
        "pendencias": [
            "Confirmar a referência temporal da malha.",
            "Confirmar o sistema e a ordem das coordenadas.",
            "Validar a geometria antes de classificar pontos.",
            "Avaliar a simplificação do contorno e seus limites de uso.",
        ],
    }

    pasta_destino.mkdir(parents=True, exist_ok=True)

    # Preserva os bytes recebidos para permitir conferência do hash.
    arquivo_geojson.write_bytes(conteudo)

    arquivo_metadados.write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n--- LIMITE MUNICIPAL BAIXADO ---")
    print("Código do município:", codigo_municipio)
    print("Quantidade de feições:", len(elementos))
    print("Tipos de geometria:", ", ".join(sorted(tipos_geometria)))
    print("Referência espacial declarada:", dados.get("crs"))
    print("Tamanho do arquivo em bytes:", len(conteudo))
    print("GeoJSON salvo em:", arquivo_geojson)
    print("Metadados salvos em:", arquivo_metadados)
    print("PASSOU: Verificações básicas da estrutura e do código.")
    print(
        "O arquivo ainda não foi utilizado "
        "para aprovar ou rejeitar pontos."
    )


if __name__ == "__main__":
    baixar_limite()