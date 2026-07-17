from studyhub.database.conexao import conectar

def salvar_tarefa(descricao, usuario_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO tarefas(descricao, usuario_id)
        VALUES(?, ?)
    """, (descricao, usuario_id))

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
        (nova_tarefa, id_tarefa, usuario_id)
    )

    conexao.commit()
    conexao.close()

def atualizar_status(id_tarefa, concluida, usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE tarefas
        SET concluida = ?
        WHERE id = ? AND usuario_id = ?
        """,
        (concluida, id_tarefa, usuario_id)
    )

    conexao.commit()
    conexao.close()

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