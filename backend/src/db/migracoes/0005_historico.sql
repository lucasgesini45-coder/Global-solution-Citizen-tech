-- Migração 0005: Histórico de buscas, rotas calculadas e cache de geocodificação

CREATE TABLE IF NOT EXISTS historico_buscas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessao_id TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    origem_lat REAL NOT NULL,
    origem_lon REAL NOT NULL,
    destino_lat REAL NOT NULL,
    destino_lon REAL NOT NULL,
    partida TEXT NOT NULL,
    n_rotas INTEGER NOT NULL,
    erro_codigo TEXT,
    origem_nome TEXT,
    destino_nome TEXT,
    feed_versao TEXT,
    regra_tarifa_versao TEXT,
    tempo_calculo_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_historico_sessao ON historico_buscas(sessao_id);

CREATE TABLE IF NOT EXISTS historico_rotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    busca_id INTEGER NOT NULL REFERENCES historico_buscas(id) ON DELETE CASCADE,
    ordem INTEGER NOT NULL,
    saida_s INTEGER NOT NULL,
    chegada_s INTEGER NOT NULL,
    tempo_total_s INTEGER NOT NULL,
    espera_s INTEGER NOT NULL,
    caminhada_m INTEGER NOT NULL,
    baldeacoes INTEGER NOT NULL,
    custo_centavos INTEGER,
    custo_confirmado INTEGER NOT NULL CHECK (custo_confirmado IN (0, 1)),
    escolhida INTEGER NOT NULL DEFAULT 0 CHECK (escolhida IN (0, 1)),
    UNIQUE (busca_id, ordem)
);

CREATE TABLE IF NOT EXISTS historico_rota_linhas (
    rota_id INTEGER NOT NULL REFERENCES historico_rotas(id) ON DELETE CASCADE,
    posicao INTEGER NOT NULL,
    linha_id TEXT NOT NULL,
    nome_linha TEXT NOT NULL,
    modal TEXT NOT NULL,
    operador TEXT NOT NULL,
    PRIMARY KEY (rota_id, posicao)
);

CREATE TABLE IF NOT EXISTS cache_geocodificacao (
    consulta TEXT PRIMARY KEY,
    resposta_json TEXT NOT NULL,
    obtido_em TEXT NOT NULL
);
