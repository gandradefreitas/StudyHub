from contextlib import closing

from database.conexao import conectar


def obter_progresso(usuario_id):
    with closing(conectar()) as conexao:
        hoje = conexao.execute("""
            SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date AS hoje
        """).fetchone()["hoje"]
        leituras = conexao.execute("""
            SELECT texto_id, palavras, concluido_em, acertos
            FROM leituras_idiomas
            WHERE usuario_id = %s
        """, (usuario_id,)).fetchall()
    return hoje, {leitura["texto_id"]: leitura for leitura in leituras}


def registrar_leitura(usuario_id, texto_id, palavras, acertos):
    with conectar() as conexao:
        conexao.execute("""
            INSERT INTO leituras_idiomas (usuario_id, texto_id, palavras, acertos)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (usuario_id, texto_id)
            DO UPDATE SET acertos = EXCLUDED.acertos
        """, (usuario_id, texto_id, palavras, acertos))
