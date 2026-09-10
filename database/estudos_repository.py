from database.conexao import conectar
from datetime import datetime


def iniciar_estudo(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO estudos(usuario_id, inicio)
        VALUES(%s, %s)
    """, (
        usuario_id,
        datetime.now()
    ))

    conexao.commit()
    conexao.close()


def finalizar_estudo(estudo_id, fim, duracao, usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        UPDATE estudos
        SET
            fim = %s,
            duracao = %s,
            ativa = 0
        WHERE id = %s
        AND usuario_id = %s
    """, (
        fim,
        duracao,
        estudo_id,
        usuario_id
    ))

    conexao.commit()
    conexao.close()

def obter_total_segundos(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(duracao), 0) AS total
        FROM estudos
        WHERE usuario_id = %s
    """, (usuario_id,))

    resultado = cursor.fetchone()

    conexao.close()

    return resultado["total"]


def obter_estudos_por_data(usuario_id, data):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            inicio,
            fim,
            duracao
        FROM estudos
        WHERE usuario_id = %s
        AND inicio::date = %s
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
        SELECT
            id,
            inicio
        FROM estudos
        WHERE usuario_id = %s
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
        WHERE usuario_id = %s
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
            inicio::date AS data
        FROM estudos
        WHERE usuario_id = %s
        AND EXTRACT(YEAR FROM inicio) = %s
        AND EXTRACT(MONTH FROM inicio) = %s
        AND duracao > 0
        GROUP BY inicio::date
        ORDER BY inicio::date
    """, (
        usuario_id,
        ano,
        mes
    ))

    estudos = cursor.fetchall()

    conexao.close()

    return estudos


def obter_estudos_por_periodo(usuario_id, inicio, fim):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            inicio::date AS data,
            SUM(duracao) AS duracao
        FROM estudos
        WHERE usuario_id = %s
        AND inicio::date BETWEEN %s AND %s
        AND duracao > 0
        GROUP BY inicio::date
        ORDER BY inicio::date
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
        SELECT COALESCE(SUM(duracao), 0) AS segundos
        FROM estudos
        WHERE usuario_id = %s
        AND inicio::date = CURRENT_DATE
    """, (usuario_id,))

    segundos = cursor.fetchone()["segundos"]

    conexao.close()

    return segundos


def obter_questoes_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    # Questões respondidas na área de Estudos
    cursor.execute("""
        SELECT COUNT(*) AS questoes
        FROM respostas_questoes
        WHERE usuario_id = %s
        AND data_resposta::date = CURRENT_DATE
    """, (usuario_id,))

    questoes_estudos = cursor.fetchone()["questoes"]


    # Questões realizadas em Provas
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS questoes
        FROM resultados_provas
        WHERE usuario_id = %s
        AND data_realizacao::date = CURRENT_DATE
    """, (usuario_id,))

    questoes_provas = cursor.fetchone()["questoes"]


    conexao.close()


    return (
        questoes_estudos
        + questoes_provas
    )

def obter_questoes_respondidas_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS questoes
        FROM respostas_provas
        WHERE usuario_id = %s
        AND data::date = CURRENT_DATE
    """, (usuario_id,))

    questoes = cursor.fetchone()["questoes"]

    conexao.close()

    return questoes


def obter_segundos_provas_hoje(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = %s
        AND data_realizacao::date = CURRENT_DATE
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
