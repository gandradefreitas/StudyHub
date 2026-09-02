from studyhub.database.conexao import conectar

def registrar_resposta_questao(usuario_id,questao_numero,resposta,correta,data_resposta,proxima_tentativa):

    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute("""
        INSERT INTO respostas_questoes (

            usuario_id,

            questao_numero,

            resposta,

            correta,

            data_resposta,

            proxima_tentativa

        )

        VALUES (?, ?, ?, ?, ?, ?)

    """, (

        usuario_id,

        questao_numero,

        resposta,

        correta,

        data_resposta,

        proxima_tentativa

    ))


    conexao.commit()

    conexao.close()

def obter_ultima_resposta_questao(usuario_id,questao_numero):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            resposta,
            correta,
            data_resposta,
            proxima_tentativa

        FROM respostas_questoes

        WHERE usuario_id = ?
        AND questao_numero = ?

        ORDER BY data_resposta DESC

        LIMIT 1

    """, (
        usuario_id,
        questao_numero
    ))

    resultado = cursor.fetchone()

    conexao.close()

    return resultado