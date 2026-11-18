"""Constantes do assistente de dúvidas.

Todas as constantes do assistente ficam somente neste arquivo (decisão da especificação,
seção 5). Nenhum destes valores pode aparecer escrito dentro de outro módulo.
"""
from pathlib import Path

# Raiz do repositório: .../backend/src/assistente/config.py -> parents[3] é a raiz.
RAIZ_REPOSITORIO = Path(__file__).resolve().parents[3]

# Constantes principais
LIMIAR_CONFIANCA = 0.40
MAX_SUGESTOES = 3
TOP_K = 3
PERGUNTA_MIN_CARACTERES = 3
PERGUNTA_MAX_CARACTERES = 300
FRASES_POR_INTENCAO = 12
N_INTENCOES = 15
RESPOSTA_MAX_CARACTERES = 350
RESPOSTA_MAX_FRASES = 3
SEMENTE_ALEATORIA = 42

# 13 valores: 0.20, 0.25, ..., 0.80
LIMIARES_CALIBRACAO = tuple(round(0.20 + 0.05 * i, 2) for i in range(13))

TEXTO_FALLBACK = (
    "Não encontrei uma resposta para essa pergunta. "
    "Este assistente responde apenas dúvidas sobre rotas, tarifas e histórico/privacidade no uso do app."
)
TEXTO_AVISO_TARIFAS = "Plataforma acadêmica, não é canal oficial."
TEXTO_BOAS_VINDAS_TERMINAL = "Assistente de dúvidas do app. Digite sua pergunta ou 'sair' para voltar."
TEXTO_ENTRADA_INVALIDA_TERMINAL = "Digite uma pergunta com 3 a 300 caracteres."
PALAVRA_SAIDA_TERMINAL = "sair"
TEXTO_PERGUNTA_INVALIDA = "Pergunta inválida."
TEXTO_ASSISTENTE_INDISPONIVEL = "Assistente indisponível."
TEXTO_VOCE_QUIS_DIZER = "Você quis dizer:"

# Caminhos (relativos à raiz do repositório)
CAMINHO_BASE = "backend/data/assistente/base_conhecimento.json"
CAMINHO_PERGUNTAS_TESTE = "backend/data/assistente/perguntas_teste.json"
CAMINHO_MODELO = "backend/models/assistente_intencoes.joblib"
CAMINHO_RELATORIO_AVALIACAO = "docs/relatorio_avaliacao_assistente.md"
CAMINHO_RELATORIO_CALIBRACAO = "docs/relatorio_calibracao_assistente.md"

# Verificação por palavra inteira, sem diferenciar maiúsculas de minúsculas.
PALAVRAS_PROIBIDAS = (
    "segura",
    "seguro",
    "garantida",
    "garantido",
    "pontual",
    "sem risco",
)

# Parâmetros do modelo
TFIDF_LOWERCASE = True
TFIDF_STRIP_ACCENTS = "unicode"
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_SUBLINEAR_TF = True
TFIDF_MIN_DF = 1
TFIDF_STOP_WORDS = None

LOGREG_C = 10.0
LOGREG_MAX_ITER = 1000
LOGREG_SOLVER = "lbfgs"
LOGREG_RANDOM_STATE = SEMENTE_ALEATORIA

PIPELINE_ETAPA_TFIDF = "tfidf"
PIPELINE_ETAPA_CLF = "clf"


def resolver_caminho(caminho) -> Path:
    """Caminho absoluto continua igual; relativo é resolvido a partir da raiz do repositório."""
    p = Path(caminho)
    if p.is_absolute():
        return p
    return RAIZ_REPOSITORIO / p
