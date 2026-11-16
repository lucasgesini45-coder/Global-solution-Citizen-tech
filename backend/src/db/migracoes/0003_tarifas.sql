-- Migração 0003: Tabelas de tarifas e regras tarifárias

CREATE TABLE IF NOT EXISTS tarifas_regras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao TEXT NOT NULL UNIQUE,
    fonte_descricao TEXT NOT NULL,
    fonte_url TEXT NOT NULL,
    verificada_em TEXT,
    confirmada INTEGER NOT NULL CHECK (confirmada IN (0, 1)),
    origem_dados TEXT NOT NULL CHECK (origem_dados IN ('real', 'teste')),
    vigencia_inicio TEXT NOT NULL,
    vigencia_fim TEXT,
    janela_s INTEGER NOT NULL CHECK (janela_s > 0),
    max_embarques_por_janela INTEGER NOT NULL CHECK (max_embarques_por_janela > 0),
    janela_integrada_s INTEGER,
    max_onibus_integrada INTEGER,
    max_trilho_integrada INTEGER,
    CHECK (confirmada = 0 OR (verificada_em IS NOT NULL AND fonte_url <> ''))
);

CREATE TABLE IF NOT EXISTS tarifas_base (
    regra_id INTEGER NOT NULL REFERENCES tarifas_regras(id) ON DELETE CASCADE,
    modal TEXT NOT NULL,
    centavos INTEGER NOT NULL CHECK (centavos >= 0),
    PRIMARY KEY (regra_id, modal)
);

CREATE TABLE IF NOT EXISTS tarifas_integracao (
    regra_id INTEGER NOT NULL REFERENCES tarifas_regras(id) ON DELETE CASCADE,
    de_modal TEXT NOT NULL,
    para_modal TEXT NOT NULL,
    centavos INTEGER NOT NULL CHECK (centavos >= 0),
    PRIMARY KEY (regra_id, de_modal, para_modal)
);

CREATE TABLE IF NOT EXISTS tarifas_perfis (
    regra_id INTEGER NOT NULL REFERENCES tarifas_regras(id) ON DELETE CASCADE,
    perfil TEXT NOT NULL,
    percentual INTEGER NOT NULL CHECK (percentual >= 0),
    PRIMARY KEY (regra_id, perfil)
);
