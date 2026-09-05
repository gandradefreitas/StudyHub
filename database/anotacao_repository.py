from database.conexao import conectar


def obter_anotacao_por_data(usuario_id, data):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id,
            data,
            texto
        FROM anotacoes
        WHERE usuario_id = %s
        AND data = %s
        """,
        (
            usuario_id,
            data
        )
    )

    anotacao = cursor.fetchone()

    conexao.close()

    return anotacao


def salvar_anotacao(usuario_id, data, texto):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO anotacoes(
            usuario_id,
            data,
            texto
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (usuario_id, data)
        DO UPDATE SET
            texto = EXCLUDED.texto
        """,
        (
            usuario_id,
            data,
            texto
        )
    )

    conexao.commit()

    conexao.close()


def obter_anotacoes_por_mes(usuario_id, ano, mes):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            data
        FROM anotacoes
        WHERE usuario_id = %s
        AND EXTRACT(YEAR FROM data::date) = %s
        AND EXTRACT(MONTH FROM data::date) = %s
        AND texto != ''
        GROUP BY data
        ORDER BY data
    """, (
        usuario_id,
        ano,
        mes
    ))

    anotacoes = cursor.fetchall()

    conexao.close()

    return anotacoes
