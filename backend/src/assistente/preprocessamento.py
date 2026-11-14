"""Etapa de pré-processamento do assistente."""
import re
import unicodedata


def normalizar_para_comparacao(texto: str) -> str:
    """Normaliza texto para comparações estritas de duplicatas e vazamento de teste.

    Aplica casefold, remove acentos (decomposição Unicode e remoção das marcas combinantes),
    troca qualquer caractere que não seja letra ou dígito por espaço e colapsa espaços.
    Usada somente para comparar textos; o modelo usa a normalização do próprio TfidfVectorizer.
    """
    texto = texto.casefold()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()
