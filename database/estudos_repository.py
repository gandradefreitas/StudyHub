from studyhub.database.conexao import conectar
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

def obter_estudos_por_data(usuario_id, data):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            inicio,
            fim,
            duracao
        FROM estudos
        WHERE usuario_id = ?
        AND DATE(inicio) = ?
        ORDER BY inicio
    """, (
        usuario_id,
        data
    ))

    estudos = cursor.fetchall()

    conexao.close()

    return estudos

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

def obter_estudos_por_mes(usuario_id, ano, mes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            DATE(inicio) AS data
        FROM estudos
        WHERE usuario_id = ?
        AND strftime('%Y', inicio) = ?
        AND strftime('%m', inicio) = ?
        AND duracao > 0
        GROUP BY DATE(inicio)
        ORDER BY DATE(inicio)
    """, (
        usuario_id,
        str(ano),
        f"{mes:02d}"
    ))

    estudos = cursor.fetchall()

    conexao.close()

    return estudos

def obter_estudos_por_periodo(usuario_id, inicio, fim):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            DATE(inicio) AS data,
            SUM(duracao) AS duracao
        FROM estudos
        WHERE usuario_id = ?
        AND DATE(inicio) BETWEEN ? AND ?
        AND duracao > 0
        GROUP BY DATE(inicio)
        ORDER BY DATE(inicio)
    """, (
        usuario_id,
        inicio,
        fim
    ))

    estudos = cursor.fetchall()

    conexao.close()

    return estudos

def obter_segundos_estudados_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(duracao), 0)
        FROM estudos
        WHERE usuario_id = ?
        AND DATE(inicio) = DATE('now', 'localtime')
    """, (usuario_id,))

    segundos = cursor.fetchone()[0]

    conexao.close()

    return segundos

def obter_questoes_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM resultados_provas
        WHERE usuario_id = ?
        AND DATE(data) = DATE('now', 'localtime')
    """, (usuario_id,))

    questoes = cursor.fetchone()[0]

    conexao.close()

    return questoes

def obter_questoes_respondidas_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM respostas_provas
        WHERE usuario_id = ?
        AND DATE(data) = DATE('now', 'localtime')
    """, (usuario_id,))

    questoes = cursor.fetchone()[0]

    conexao.close()

    return questoes

def obter_segundos_provas_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = ?
        AND DATE(data_realizacao) = DATE('now', 'localtime')
    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    total_segundos = 0

    for resultado in resultados:

        tempo = resultado["tempo_gasto"]

        if not tempo:
            continue

        horas, minutos, segundos = map(
            int,
            tempo.split(":")
        )

        total_segundos += (
            horas * 3600
            + minutos * 60
            + segundos
        )

    return total_segundos