import sqlite3

from studyhub.database.conexao import conectar


def salvar_usuario(nome, email, senha):
    conexao = conectar()
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO usuarios(nome, email, senha)
        VALUES (?, ?, ?)
    """, (nome, email, senha))

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