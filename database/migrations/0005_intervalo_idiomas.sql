ALTER TABLE leituras_idiomas
    ADD COLUMN IF NOT EXISTS ultimo_envio_em TIMESTAMPTZ;
