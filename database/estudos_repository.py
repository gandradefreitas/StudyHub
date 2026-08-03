from database.conexao import conectar
from datetime import datetime

def iniciar_estudo(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO estudos(usuario_id, inicio)
        VALUES(?, ?)
    """, (
        usuario_id,
        datetime.now().isoformat()
    ))

    conexao.commit()
    conexao.close()

def finalizar_estudo(estudo_id, fim, duracao):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE estudos
        SET fim = ?, 
            duracao = ?,
            ativa = 0
        WHERE id = ?
    """, (
        fim,
        duracao,
        estudo_id
    ))

    conexao.commit()
    conexao.close()

def obter_total_segundos(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT SUM(duracao)
        FROM estudos
        WHERE usuario_id = ?
    """, (usuario_id,))

    resultado = cursor.fetchone()

    conexao.close()

    if resultado[0] is None:
        return 0

    return resultado[0]

def obter_estudo_ativo(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, inicio
        FROM estudos
        WHERE usuario_id = ?
        AND ativa = 1
    """, (usuario_id,))

    estudo = cursor.fetchone()

    conexao.close()

    return estudo

def possui_estudo_ativo(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id
        FROM estudos
        WHERE usuario_id = ?
        AND ativa = 1
    """, (usuario_id,))

    resultado = cursor.fetchone()

    conexao.close()

    return resultado is not None