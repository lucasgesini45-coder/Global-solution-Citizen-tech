"""Etapa de treino do assistente (6.3): TF-IDF + Regressão Logística (scikit-learn)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from . import config
from .base import obter_pares_treino


def criar_pipeline() -> Pipeline:
    """Pipeline com as etapas 'tfidf' e 'clf', nesta ordem, com os parâmetros da especificação."""
    return Pipeline([
        (config.PIPELINE_ETAPA_TFIDF, TfidfVectorizer(
            lowercase=config.TFIDF_LOWERCASE,
            strip_accents=config.TFIDF_STRIP_ACCENTS,
            ngram_range=config.TFIDF_NGRAM_RANGE,
            sublinear_tf=config.TFIDF_SUBLINEAR_TF,
            min_df=config.TFIDF_MIN_DF,
            stop_words=config.TFIDF_STOP_WORDS,
        )),
        (config.PIPELINE_ETAPA_CLF, LogisticRegression(
            C=config.LOGREG_C,
            max_iter=config.LOGREG_MAX_ITER,
            solver=config.LOGREG_SOLVER,
            random_state=config.LOGREG_RANDOM_STATE,
        )),
    ])


def treinar_modelo(frases, rotulos) -> Pipeline:
    pipeline = criar_pipeline()
    pipeline.fit(frases, rotulos)
    return pipeline


def treinar_a_partir_da_base(dados_base: dict) -> Pipeline:
    """Treina usando exclusivamente as frases de treino da base (sem divisão aleatória)."""
    frases, rotulos = obter_pares_treino(dados_base)
    return treinar_modelo(frases, rotulos)
