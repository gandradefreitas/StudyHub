from database.conexao import conectar


def obter_dados_exportacao(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    usuario = cursor.fetchone()

    cursor.execute("""
        SELECT
            tema,
            meta_estudo,
            meta_questoes
        FROM configuracoes_usuario
        WHERE usuario_id = %s
    """, (usuario_id,))

    configuracoes = cursor.fetchone()

    cursor.execute("""
        SELECT
            inicio,
            fim,
            duracao,
            ativa
        FROM estudos
        WHERE usuario_id = %s
        ORDER BY inicio
    """, (usuario_id,))

    estudos = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            descricao,
            concluida,
            data_conclusao
        FROM tarefas
        WHERE usuario_id = %s
        ORDER BY id
    """, (usuario_id,))

    tarefas = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            data,
            texto
        FROM anotacoes
        WHERE usuario_id = %s
        ORDER BY data
    """, (usuario_id,))

    anotacoes = cursor.fetchall()

    cursor.execute("""
        SELECT
            prova_id,
            acertos,
            erros,
            nao_respondidas,
            total,
            tempo_gasto,
            porcentagem,
            data_realizacao
        FROM resultados_provas
        WHERE usuario_id = %s
        ORDER BY data_realizacao
    """, (usuario_id,))

    resultados_provas = cursor.fetchall()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            resposta,
            correta,
            data
        FROM respostas_provas
        WHERE usuario_id = %s
        ORDER BY data
    """, (usuario_id,))

    respostas_provas = cursor.fetchall()

    conexao.close()

    return {
        "usuario": usuario,
        "configuracoes": configuracoes,
        "estudos": estudos,
        "tarefas": tarefas,
        "anotacoes": anotacoes,
        "resultados_provas": resultados_provas,
        "respostas_provas": respostas_provas
    }


def limpar_historico(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            DELETE FROM respostas_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM resultados_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM estudos
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM anotacoes
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM tarefas
            WHERE usuario_id = %s
            AND concluida = 1
        """, (usuario_id,))

        conexao.commit()

        return True

    except Exception:

        conexao.rollback()

        return False

    finally:

        conexao.close()
