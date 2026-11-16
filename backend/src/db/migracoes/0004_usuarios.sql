-- Migração 0004: Usuários, consentimentos e preferências

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    token_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    ultimo_acesso_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consentimentos (
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    finalidade TEXT NOT NULL CHECK (finalidade IN ('historico_buscas', 'conversa_assistente', 'localizacao', 'melhoria_assistente')),
    concedido INTEGER NOT NULL CHECK (concedido IN (0, 1)),
    texto_versao TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    PRIMARY KEY (usuario_id, finalidade)
);

CREATE TABLE IF NOT EXISTS preferencias (
    usuario_id TEXT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    caminhada_max_m INTEGER NOT NULL DEFAULT 1000 CHECK (caminhada_max_m BETWEEN 0 AND 3000),
    baldeacoes_max INTEGER CHECK (baldeacoes_max IS NULL OR baldeacoes_max BETWEEN 0 AND 4),
    orcamento_max_centavos INTEGER CHECK (orcamento_max_centavos IS NULL OR orcamento_max_centavos >= 0),
    velocidade_caminhada_ms REAL NOT NULL DEFAULT 1.2 CHECK (velocidade_caminhada_ms BETWEEN 0.5 AND 2.0),
    perfil_tarifario TEXT NOT NULL DEFAULT 'padrao',
    atualizado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preferencias_acessibilidade (
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    necessidade TEXT NOT NULL,
    PRIMARY KEY (usuario_id, necessidade)
);
