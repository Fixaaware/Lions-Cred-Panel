-- ============================================================
--  Lions Cred  |  Schema do Banco de Dados (SQLite)
--  Nota: este arquivo é apenas referência.
--  O banco é criado automaticamente pelo app.py ao iniciar.
-- ============================================================

CREATE TABLE IF NOT EXISTS clientes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    cpf           TEXT    NOT NULL UNIQUE,
    telefone      TEXT,
    email         TEXT,
    endereco      TEXT,
    cidade        TEXT,
    uf            TEXT,
    status        TEXT    NOT NULL DEFAULT 'ativo'
                      CHECK(status IN ('ativo','inativo')),
    observacao    TEXT,
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    atualizado_em TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Trigger para atualizar timestamp automaticamente
CREATE TRIGGER IF NOT EXISTS trg_atualizado_em
AFTER UPDATE ON clientes
BEGIN
    UPDATE clientes SET atualizado_em = datetime('now','localtime')
    WHERE id = NEW.id;
END;

-- Índices
CREATE INDEX IF NOT EXISTS idx_nome   ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_cpf    ON clientes(cpf);
CREATE INDEX IF NOT EXISTS idx_status ON clientes(status);
