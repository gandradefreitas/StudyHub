CREATE TABLE IF NOT EXISTS experiencia_atividades (
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    origem TEXT NOT NULL,
    referencia TEXT NOT NULL,
    exp_decimos INTEGER NOT NULL CHECK (exp_decimos > 0),
    registrado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, origem, referencia)
);

CREATE TABLE IF NOT EXISTS niveis_notificados (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    nivel INTEGER NOT NULL CHECK (nivel > 0)
);
