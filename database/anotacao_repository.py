from database.conexao import conectar

def obter_anotacao_por_data(usuario_id,data):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id,
            data,
            texto
        FROM anotacoes
        WHERE usuario_id = ?
        AND data = ?
        """,
        (
            usuario_id,
            data
        )
    )

    anotacao = cursor.fetchone()

    conexao.close()

    return anotacao

def salvar_anotacao(usuario_id,data,texto):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO anotacoes(
            usuario_id,
            data,
            texto
        )
        VALUES (?, ?, ?)
        ON CONFLICT(usuario_id, data)
        DO UPDATE SET
            texto = excluded.texto
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
        WHERE usuario_id = ?
        AND strftime('%Y', data) = ?
        AND strftime('%m', data) = ?
        AND texto != ''
        GROUP BY data
        ORDER BY data
    """, (
        usuario_id,
        str(ano),
        f"{mes:02d}"
    ))

    anotacoes = cursor.fetchall()

    conexao.close()

    return anotacoes