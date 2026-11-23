CREATE TABLE IF NOT EXISTS tentativas_provas_objetivas (
    id UUID PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    prova_id INTEGER NOT NULL,
    inicio TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resultado_id INTEGER REFERENCES resultados_provas(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS tentativas_provas_objetivas_ativas
    ON tentativas_provas_objetivas (usuario_id, prova_id) WHERE resultado_id IS NULL;
