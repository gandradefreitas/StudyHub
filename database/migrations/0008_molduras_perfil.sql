CREATE TABLE IF NOT EXISTS molduras_equipadas (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    nivel INTEGER NOT NULL CHECK (nivel > 0)
);
