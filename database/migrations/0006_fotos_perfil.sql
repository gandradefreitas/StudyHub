CREATE TABLE IF NOT EXISTS fotos_perfil (
    usuario_id INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    imagem BYTEA NOT NULL CHECK (octet_length(imagem) BETWEEN 1 AND 262144)
);
