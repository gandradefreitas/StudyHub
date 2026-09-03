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
        VALUES (?, ?)
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
        WHERE usuario_id = ?
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
        SET descricao = ?
        WHERE id = ? AND usuario_id = ?
        """,
        (
            nova_tarefa,
            id_tarefa,
            usuario_id
        )
    )

    conexao.commit()

    conexao.close()

def atualizar_status(id_tarefa,concluida,usuario_id):

    conexao = conectar()

    cursor = conexao.cursor()


    if concluida == 1:

        cursor.execute(
            """
            UPDATE tarefas
            SET
                concluida = ?,
                data_conclusao = DATE('now', 'localtime')
            WHERE id = ?
            AND usuario_id = ?
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
                concluida = ?,
                data_conclusao = NULL
            WHERE id = ?
            AND usuario_id = ?
            """,
            (
                concluida,
                id_tarefa,
                usuario_id
            )
        )


    conexao.commit()

    conexao.close()

def obter_tarefas_por_data(usuario_id,data):

    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute(
        """
        SELECT
            id,
            descricao,
            data_conclusao
        FROM tarefas
        WHERE usuario_id = ?
        AND concluida = 1
        AND data_conclusao = ?
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
        WHERE id = ? AND usuario_id = ?
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
        WHERE id = ? AND usuario_id = ?
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
        WHERE usuario_id = ?
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
        SELECT COUNT(*)
        FROM tarefas
        WHERE usuario_id = ?
        AND concluida = 0
        """,
        (usuario_id,)
    )


    pendentes = cursor.fetchone()[0]


    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tarefas
        WHERE usuario_id = ?
        AND concluida = 1
        """,
        (usuario_id,)
    )


    concluidas = cursor.fetchone()[0]


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
        WHERE usuario_id = ?
        AND concluida = 0
        ORDER BY id ASC
        LIMIT ?
        """,
        (usuario_id, limite)
    )

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas

def obter_tarefas_por_mes(usuario_id, ano, mes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            data_conclusao AS data
        FROM tarefas
        WHERE usuario_id = ?
        AND concluida = 1
        AND strftime('%Y', data_conclusao) = ?
        AND strftime('%m', data_conclusao) = ?
        GROUP BY data_conclusao
        ORDER BY data_conclusao
    """, (
        usuario_id,
        str(ano),
        f"{mes:02d}"
    ))

    tarefas = cursor.fetchall()

    conexao.close()

    return tarefas