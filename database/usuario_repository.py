import sqlite3
from database.conexao import conectar

def salvar_usuario(nome, email, senha):
    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO usuarios(nome, email, senha)
        VALUES (?, ?, ?)
    """, (nome, email, senha))

    usuario_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO configuracoes_usuario(usuario_id)
        VALUES (?)
    """, (usuario_id,))

    conexao.commit()
    conexao.close()

def buscar_por_email(email):
    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE email = ?
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
        WHERE id = ?
    """, (usuario_id,))

    usuario = cursor.fetchone()

    conexao.close()

    return usuario

def obter_configuracoes(usuario_id):

    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM configuracoes_usuario
        WHERE usuario_id = ?
    """, (usuario_id,))

    configuracoes = cursor.fetchone()

    if configuracoes is None:

        cursor.execute("""
            INSERT INTO configuracoes_usuario(usuario_id)
            VALUES (?)
        """, (usuario_id,))

        conexao.commit()

        cursor.execute("""
            SELECT *
            FROM configuracoes_usuario
            WHERE usuario_id = ?
        """, (usuario_id,))

        configuracoes = cursor.fetchone()

    conexao.close()

    return configuracoes

def atualizar_configuracoes(usuario_id,tema,meta_estudo,meta_questoes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE configuracoes_usuario
        SET
            tema = ?,
            meta_estudo = ?,
            meta_questoes = ?
        WHERE usuario_id = ?
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
        SET nome = ?, email = ?
        WHERE id = ?
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
        SET senha = ?
        WHERE id = ?
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
        SET tema = ?
        WHERE id = ?
    """, (
        tema,
        usuario_id
    ))

    conexao.commit()
    conexao.close()

def salvar_metas(usuario_id,meta_estudo,meta_questoes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE configuracoes_usuario
        SET
            meta_estudo = ?,
            meta_questoes = ?
        WHERE usuario_id = ?
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
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Resultados das provas
        cursor.execute("""
            DELETE FROM resultados_provas
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Anotações
        cursor.execute("""
            DELETE FROM anotacoes
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Estudos
        cursor.execute("""
            DELETE FROM estudos
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Tarefas
        cursor.execute("""
            DELETE FROM tarefas
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Configurações
        cursor.execute("""
            DELETE FROM configuracoes_usuario
            WHERE usuario_id = ?
        """, (usuario_id,))


        # Usuário
        cursor.execute("""
            DELETE FROM usuarios
            WHERE id = ?
        """, (usuario_id,))


        conexao.commit()

        return True

    except Exception:

        conexao.rollback()

        return False

    finally:

        conexao.close()