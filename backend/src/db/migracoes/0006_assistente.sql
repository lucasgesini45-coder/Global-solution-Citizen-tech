-- Migração 0006: Conversas, mensagens, contexto do assistente e feedback

CREATE TABLE IF NOT EXISTS conversas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    titulo TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversas_usuario ON conversas(usuario_id, atualizado_em);

CREATE TABLE IF NOT EXISTS mensagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id TEXT NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('usuario', 'assistente')),
    texto TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    intencao_id TEXT,
    tema TEXT,
    confianca REAL,
    fallback INTEGER CHECK (fallback IN (0, 1)),
    usou_contexto INTEGER CHECK (usou_contexto IN (0, 1)),
    tempo_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id, id);

CREATE TABLE IF NOT EXISTS conversas_contexto (
    conversa_id TEXT PRIMARY KEY REFERENCES conversas(id) ON DELETE CASCADE,
    ultima_intencao_id TEXT,
    ultima_busca_id INTEGER REFERENCES historico_buscas(id) ON DELETE SET NULL,
    acao_pendente TEXT CHECK (acao_pendente IS NULL OR acao_pendente IN ('apagar_dados')),
    pendente_expira_em TEXT,
    atualizado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_mensagens (
    mensagem_id INTEGER PRIMARY KEY REFERENCES mensagens(id) ON DELETE CASCADE,
    util INTEGER NOT NULL CHECK (util IN (0, 1)),
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS perguntas_sem_resposta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    confianca REAL NOT NULL,
    intencao_sugerida TEXT,
    revisada INTEGER NOT NULL DEFAULT 0 CHECK (revisada IN (0, 1))
);
