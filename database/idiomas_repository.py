from contextlib import closing

from database.conexao import conectar


def obter_progresso(usuario_id):
    with closing(conectar()) as conexao:
        hoje = conexao.execute("""
            SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date AS hoje
        """).fetchone()["hoje"]
        leituras = conexao.execute("""
            SELECT texto_id, palavras, concluido_em, acertos,
                   GREATEST(0, CEIL(EXTRACT(EPOCH FROM
                       ultimo_envio_em + INTERVAL '10 minutes' - CURRENT_TIMESTAMP)))::integer
                       AS espera_segundos
            FROM leituras_idiomas
            WHERE usuario_id = %s
        """, (usuario_id,)).fetchall()
    return hoje, {leitura["texto_id"]: leitura for leitura in leituras}


def registrar_leitura(usuario_id, texto_id, palavras, acertos):
    with conectar() as conexao:
        envio = conexao.execute("""
            INSERT INTO leituras_idiomas (usuario_id, texto_id, palavras, acertos, ultimo_envio_em)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (usuario_id, texto_id)
            DO UPDATE SET acertos = EXCLUDED.acertos, ultimo_envio_em = EXCLUDED.ultimo_envio_em
            WHERE leituras_idiomas.ultimo_envio_em IS NULL
               OR EXCLUDED.ultimo_envio_em >= leituras_idiomas.ultimo_envio_em + INTERVAL '10 minutes'
            RETURNING texto_id
        """, (usuario_id, texto_id, palavras, acertos)).fetchone()
        return envio is not None
