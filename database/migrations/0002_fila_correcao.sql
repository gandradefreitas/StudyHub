ALTER TABLE redacoes
    ADD COLUMN IF NOT EXISTS correcao_tentativas INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS correcao_reivindicada_ate TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS correcao_tentar_apos TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS correcao_falhou BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS chave_envio UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_redacoes_usuario_chave_envio
    ON redacoes(usuario_id, chave_envio)
    WHERE chave_envio IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_redacoes_fila
    ON redacoes (criado_em, id)
    WHERE nota IS NULL AND NOT correcao_falhou;

CREATE INDEX IF NOT EXISTS idx_discursivas_fila
    ON tentativas_provas_discursivas (data_finalizacao, id)
    WHERE status = 'finalizada'
      AND disciplina IN ('Matemática', 'Física', 'Química')
      AND (resultado_correcao IS NULL OR resultado_correcao->>'status' = 'indisponivel');
