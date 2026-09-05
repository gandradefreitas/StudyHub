from database.conexao import conectar


def salvar_usuario(nome, email, senha):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO usuarios(nome, email, senha)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (nome, email, senha))

    usuario_id = cursor.fetchone()["id"]

    cursor.execute("""
        INSERT INTO configuracoes_usuario(usuario_id)
        VALUES (%s)
    """, (usuario_id,))

    conexao.commit()
    conexao.close()


def buscar_por_email(email):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE email = %s
    """, (email,))

    usuario = cursor.fetchone()

    conexao.close()

    return usuario


def obter_usuario_por_id(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    usuario = cursor.fetchone()

    conexao.close()

    return usuario


def obter_configuracoes(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM configuracoes_usuario
        WHERE usuario_id = %s
    """, (usuario_id,))

    configuracoes = cursor.fetchone()

    if configuracoes is None:

        cursor.execute("""
            INSERT INTO configuracoes_usuario(usuario_id)
            VALUES (%s)
        """, (usuario_id,))

        conexao.commit()

        cursor.execute("""
            SELECT *
            FROM configuracoes_usuario
            WHERE usuario_id = %s
        """, (usuario_id,))

        configuracoes = cursor.fetchone()

    conexao.close()

    return configuracoes


def atualizar_configuracoes(
    usuario_id,
    tema,
    meta_estudo,
    meta_questoes
):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE configuracoes_usuario
        SET
            tema = %s,
            meta_estudo = %s,
            meta_questoes = %s
        WHERE usuario_id = %s
    """, (
        tema,
        meta_estudo,
        meta_questoes,
        usuario_id
    ))

    conexao.commit()
    conexao.close()


def atualizar_usuario(usuario_id, nome, email):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET nome = %s, email = %s
        WHERE id = %s
    """, (
        nome,
        email,
        usuario_id
    ))

    conexao.commit()
    conexao.close()


def atualizar_senha(usuario_id, senha):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET senha = %s
        WHERE id = %s
    """, (
        senha,
        usuario_id
    ))

    conexao.commit()
    conexao.close()


def salvar_tema(usuario_id, tema):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET tema = %s
        WHERE id = %s
    """, (
        tema,
        usuario_id
    ))

    conexao.commit()
    conexao.close()


def salvar_metas(usuario_id, meta_estudo, meta_questoes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE configuracoes_usuario
        SET
            meta_estudo = %s,
            meta_questoes = %s
        WHERE usuario_id = %s
    """, (
        meta_estudo,
        meta_questoes,
        usuario_id
    ))

    conexao.commit()
    conexao.close()


def excluir_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        # Respostas das provas
        cursor.execute("""
            DELETE FROM respostas_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Resultados das provas
        cursor.execute("""
            DELETE FROM resultados_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Anotações
        cursor.execute("""
            DELETE FROM anotacoes
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Estudos
        cursor.execute("""
            DELETE FROM estudos
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Tarefas
        cursor.execute("""
            DELETE FROM tarefas
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Configurações
        cursor.execute("""
            DELETE FROM configuracoes_usuario
            WHERE usuario_id = %s
        """, (usuario_id,))

        # Usuário
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id = %s
        """, (usuario_id,))

        conexao.commit()

        return True

    except Exception:

        conexao.rollback()

        return False

    finally:

        conexao.close()
