from database.conexao import conectar


def adicionar_tarefa_controller(usuario_id, descricao):

    descricao = descricao.strip()

    if not descricao:

        return False, "Informe a descrição da tarefa."

    salvar_tarefa(usuario_id, descricao)

    return True, "Tarefa criada com sucesso."


def salvar_tarefa(usuario_id, descricao):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO tarefas (
            usuario_id,
            descricao
        )
        VALUES (%s, %s)
        """,
        (usuario_id, descricao)
    )

    conexao.commit()

    conexao.close()


def listar_tarefas(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, descricao, concluida
        FROM tarefas
        WHERE usuario_id = %s
    """, (usuario_id,))

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas


def atualizar_tarefa(id_tarefa, nova_tarefa, usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE tarefas
        SET descricao = %s
        WHERE id = %s AND usuario_id = %s
        """,
        (
            nova_tarefa,
            id_tarefa,
            usuario_id
        )
    )

    conexao.commit()

    conexao.close()


def atualizar_status(id_tarefa, concluida, usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    if concluida == 1:

        cursor.execute(
            """
            UPDATE tarefas
            SET
                concluida = %s,
                data_conclusao = CURRENT_DATE
            WHERE id = %s
            AND usuario_id = %s
            """,
            (
                concluida,
                id_tarefa,
                usuario_id
            )
        )

    else:

        cursor.execute(
            """
            UPDATE tarefas
            SET
                concluida = %s,
                data_conclusao = NULL
            WHERE id = %s
            AND usuario_id = %s
            """,
            (
                concluida,
                id_tarefa,
                usuario_id
            )
        )

    conexao.commit()

    conexao.close()


def obter_tarefas_por_data(usuario_id, data):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id,
            descricao,
            data_conclusao
        FROM tarefas
        WHERE usuario_id = %s
        AND concluida = 1
        AND data_conclusao = %s
        ORDER BY id
        """,
        (
            usuario_id,
            data
        )
    )

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas


def remover_tarefa(id_tarefa, usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        DELETE FROM tarefas
        WHERE id = %s AND usuario_id = %s
        """,
        (id_tarefa, usuario_id)
    )

    conexao.commit()

    conexao.close()


def buscar_tarefa(id_tarefa, usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, descricao, concluida
        FROM tarefas
        WHERE id = %s AND usuario_id = %s
    """, (id_tarefa, usuario_id))

    tarefa = cursor.fetchone()

    conexao.close()

    return tarefa


def obter_tarefas_usuario(usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tarefas
        WHERE usuario_id = %s
        """,
        (usuario_id,)
    )

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas


def contar_tarefas_usuario(usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM tarefas
        WHERE usuario_id = %s
        AND concluida = 0
        """,
        (usuario_id,)
    )

    pendentes = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM tarefas
        WHERE usuario_id = %s
        AND concluida = 1
        """,
        (usuario_id,)
    )

    concluidas = cursor.fetchone()["total"]

    conexao.close()

    return {
        "pendentes": pendentes,
        "concluidas": concluidas,
        "tempo_estudado": 0,
        "sequencia": 0
    }


def obter_proximas_tarefas(usuario_id, limite=3):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            id,
            descricao,
            concluida,
            usuario_id,
            data_conclusao
        FROM tarefas
        WHERE usuario_id = %s
        AND concluida = 0
        ORDER BY id ASC
        LIMIT %s
        """,
        (usuario_id, limite)
    )

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas


def obter_tarefas_por_mes(usuario_id, ano, mes):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        SELECT
            data_conclusao AS data
        FROM tarefas
        WHERE usuario_id = %s
        AND concluida = 1
        AND EXTRACT(YEAR FROM data_conclusao::date) = %s
        AND EXTRACT(MONTH FROM data_conclusao::date) = %s
        GROUP BY data_conclusao
        ORDER BY data_conclusao
        """,
        (
            usuario_id,
            ano,
            mes
        )
    )

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas
