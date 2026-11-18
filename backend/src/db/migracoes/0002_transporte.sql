-- Migração 0002: Tabelas de transporte público (GTFS)

CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sistema TEXT NOT NULL CHECK (sistema IN ('sptrans', 'metroferroviario', 'emtu')),
    fonte_url TEXT NOT NULL,
    arquivo_nome TEXT NOT NULL,
    arquivo_sha256 TEXT NOT NULL,
    versao TEXT NOT NULL,
    validade_inicio TEXT,
    validade_fim TEXT,
    origem_dados TEXT NOT NULL CHECK (origem_dados IN ('real', 'historico', 'teste')),
    importado_em TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 0 CHECK (ativo IN (0, 1)),
    n_paradas INTEGER NOT NULL,
    n_linhas INTEGER NOT NULL,
    n_padroes INTEGER NOT NULL,
    n_viagens INTEGER NOT NULL,
    UNIQUE (sistema, arquivo_sha256)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_ativo ON feeds(sistema) WHERE ativo = 1;

CREATE TABLE IF NOT EXISTS paradas (
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    nome TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    celula_x INTEGER NOT NULL,
    celula_y INTEGER NOT NULL,
    PRIMARY KEY (feed_id, id)
);

CREATE INDEX IF NOT EXISTS idx_paradas_celula ON paradas(feed_id, celula_x, celula_y);

CREATE TABLE IF NOT EXISTS linhas (
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    nome_curto TEXT NOT NULL,
    nome_longo TEXT,
    operador TEXT NOT NULL,
    modal TEXT NOT NULL CHECK (modal IN ('onibus', 'onibus_metropolitano', 'metro', 'trem')),
    PRIMARY KEY (feed_id, id)
);

CREATE TABLE IF NOT EXISTS servicos (
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    id TEXT NOT NULL,
    dia0 INTEGER NOT NULL CHECK (dia0 IN (0, 1)),
    dia1 INTEGER NOT NULL CHECK (dia1 IN (0, 1)),
    dia2 INTEGER NOT NULL CHECK (dia2 IN (0, 1)),
    dia3 INTEGER NOT NULL CHECK (dia3 IN (0, 1)),
    dia4 INTEGER NOT NULL CHECK (dia4 IN (0, 1)),
    dia5 INTEGER NOT NULL CHECK (dia5 IN (0, 1)),
    dia6 INTEGER NOT NULL CHECK (dia6 IN (0, 1)),
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    PRIMARY KEY (feed_id, id)
);

CREATE TABLE IF NOT EXISTS servicos_excecoes (
    feed_id INTEGER NOT NULL,
    servico_id TEXT NOT NULL,
    data TEXT NOT NULL,
    tipo INTEGER NOT NULL CHECK (tipo IN (1, 2)),
    PRIMARY KEY (feed_id, servico_id, data),
    FOREIGN KEY (feed_id, servico_id) REFERENCES servicos(feed_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS padroes (
    feed_id INTEGER NOT NULL,
    id INTEGER NOT NULL,
    linha_id TEXT NOT NULL,
    sentido TEXT NOT NULL,
    n_paradas INTEGER NOT NULL CHECK (n_paradas >= 2),
    duracao_s INTEGER NOT NULL,
    PRIMARY KEY (feed_id, id),
    FOREIGN KEY (feed_id, linha_id) REFERENCES linhas(feed_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS padrao_paradas (
    feed_id INTEGER NOT NULL,
    padrao_id INTEGER NOT NULL,
    posicao INTEGER NOT NULL,
    parada_id TEXT NOT NULL,
    deslocamento_s INTEGER NOT NULL CHECK (deslocamento_s >= 0),
    PRIMARY KEY (feed_id, padrao_id, posicao),
    FOREIGN KEY (feed_id, padrao_id) REFERENCES padroes(feed_id, id) ON DELETE CASCADE,
    FOREIGN KEY (feed_id, parada_id) REFERENCES paradas(feed_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_padrao_paradas ON padrao_paradas(feed_id, parada_id, padrao_id);

CREATE TABLE IF NOT EXISTS viagens (
    feed_id INTEGER NOT NULL,
    id TEXT NOT NULL,
    padrao_id INTEGER NOT NULL,
    servico_id TEXT NOT NULL,
    inicio_s INTEGER NOT NULL,
    PRIMARY KEY (feed_id, id),
    FOREIGN KEY (feed_id, padrao_id) REFERENCES padroes(feed_id, id) ON DELETE CASCADE,
    FOREIGN KEY (feed_id, servico_id) REFERENCES servicos(feed_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_viagens_servico ON viagens(feed_id, servico_id, inicio_s);
CREATE INDEX IF NOT EXISTS idx_viagens_padrao ON viagens(feed_id, padrao_id);
