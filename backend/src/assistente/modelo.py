"""Persistência do modelo (seção 8.3): carregar o .joblib quando válido, re-treinar quando não.

O arquivo salvo guarda: o Pipeline treinado, o hash da base, a versão do scikit-learn e os IDs
das intenções. Se o arquivo faltar, não abrir, estiver incompleto ou for de outra base/versão,
o modelo é treinado de novo e o arquivo é sobrescrito (escrita em arquivo temporário + renomeação).
"""
import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import sklearn

from . import treino
from .base import carregar_base, obter_intencoes_por_id
from .config import CAMINHO_BASE, CAMINHO_MODELO, resolver_caminho

logger = logging.getLogger(__name__)

CHAVES_ARQUIVO = ("pipeline", "hash_base", "versao_sklearn", "ids_intencoes")


@dataclass
class ModeloAssistente:
    pipeline: object
    intencoes: dict                 # id -> objeto da intenção (da base)
    hash_base: str
    versao_base: str
    origem: str = "treinado"        # "carregado" ou "treinado"
    ids: list = field(default_factory=list)


def calcular_hash_base(caminho_base=None) -> str:
    """SHA-256 (hexadecimal) dos bytes do arquivo base_conhecimento.json."""
    caminho = resolver_caminho(caminho_base or CAMINHO_BASE)
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _conteudo_valido(conteudo, hash_base: str, ids: list) -> bool:
    if not isinstance(conteudo, dict) or any(chave not in conteudo for chave in CHAVES_ARQUIVO):
        return False
    return (
        conteudo["hash_base"] == hash_base
        and conteudo["versao_sklearn"] == sklearn.__version__
        and sorted(conteudo["ids_intencoes"]) == sorted(ids)
        and hasattr(conteudo["pipeline"], "predict_proba")
    )


def salvar_modelo(pipeline, hash_base: str, ids: list, caminho_modelo=None) -> None:
    """Grava em arquivo temporário na mesma pasta e depois renomeia (escrita atômica)."""
    destino = resolver_caminho(caminho_modelo or CAMINHO_MODELO)
    destino.parent.mkdir(parents=True, exist_ok=True)
    descritor, caminho_tmp = tempfile.mkstemp(dir=destino.parent, suffix=".tmp")
    os.close(descritor)
    try:
        joblib.dump({
            "pipeline": pipeline,
            "hash_base": hash_base,
            "versao_sklearn": sklearn.__version__,
            "ids_intencoes": list(ids),
        }, caminho_tmp)
        os.replace(caminho_tmp, destino)
    finally:
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)


def carregar_ou_treinar(caminho_modelo=None, caminho_base=None, caminho_testes=None,
                        funcao_treino=None, raiz_repositorio=None) -> ModeloAssistente:
    """Devolve o modelo pronto. `funcao_treino` é injetável para testes (recebe dados_base)."""
    destino = resolver_caminho(caminho_modelo or CAMINHO_MODELO)
    dados_base, _ = carregar_base(caminho_base, caminho_testes, validar=True, raiz_repositorio=raiz_repositorio)
    intencoes = obter_intencoes_por_id(dados_base)
    ids = sorted(intencoes)
    hash_base = calcular_hash_base(caminho_base)

    if destino.is_file():
        try:
            conteudo = joblib.load(destino)
        except Exception:  # noqa: BLE001 - arquivo corrompido: re-treinar
            logger.warning("Modelo do assistente não pôde ser aberto; será treinado de novo.")
            conteudo = None
        if conteudo is not None and _conteudo_valido(conteudo, hash_base, ids):
            logger.info("Modelo do assistente carregado do arquivo.")
            return ModeloAssistente(conteudo["pipeline"], intencoes, hash_base, dados_base["versao"],
                                    origem="carregado", ids=ids)

    treinar = funcao_treino or treino.treinar_a_partir_da_base
    pipeline = treinar(dados_base)
    try:
        salvar_modelo(pipeline, hash_base, ids, destino)
    except OSError:
        logger.warning("Não foi possível salvar o modelo do assistente; seguindo com o modelo em memória.")
    logger.info("Modelo do assistente treinado.")
    return ModeloAssistente(pipeline, intencoes, hash_base, dados_base["versao"], origem="treinado", ids=ids)
