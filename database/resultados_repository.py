from datetime import datetime, timezone, timedelta

from studyhub.database.conexao import conectar
from studyhub.services.provas_service import obter_prova, listar_provas


def salvar_resultado(resultado):
    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""

    INSERT INTO resultados_provas
    (
        usuario_id,
        prova_id,
        acertos,
        erros,
        nao_respondidas,
        total,
        tempo_gasto,
        porcentagem
    )

    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """,

       (
           resultado["usuario_id"],
           resultado["prova_id"],
           resultado["acertos"],
           resultado["erros"],
           resultado["nao_respondidas"],
           resultado["total"],
           resultado["tempo_gasto"],
           resultado["porcentagem"]
       ))

    conexao.commit()

    conexao.close()

def formatar_data_realizacao(data):
    data_utc = datetime.strptime(
        data,
        "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=timezone.utc)

    horario_brasilia = data_utc.astimezone(
        timezone(timedelta(hours=-3))
    )

    return horario_brasilia.strftime(
        "%d/%m/%Y às %H:%M"
    )

def listar_resultados_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

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

        WHERE usuario_id = ?

        ORDER BY data_realizacao DESC

    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    provas = listar_provas()

    historico = []

    for resultado in resultados:

        prova = next(
            (
                prova
                for prova in provas
                if prova["id"] == resultado["prova_id"]
            ),
            None
        )

        historico.append({

              "data_realizacao":
                  formatar_data_realizacao(
                      resultado["data_realizacao"]
                  ),

              "prova":
                  (
                      f'{prova["nome"]} — {prova["dia"]}'
                      if prova
                      else "Prova não encontrada"
                  ),

              "acertos":
                  resultado["acertos"],

              "erros":
                  resultado["erros"],

              "nao_respondidas":
                  resultado["nao_respondidas"],

              "total":
                  resultado["total"],

              "tempo_gasto":
                  resultado["tempo_gasto"],

              "porcentagem":
                  resultado["porcentagem"]
        })

    return historico

def obter_resultados_por_data(usuario_id, data):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            acertos,
            erros,
            nao_respondidas,
            total,
            tempo_gasto,
            porcentagem,
            data

        FROM resultados_provas

        WHERE usuario_id = ?

        AND DATE(data) = ?

        ORDER BY data
    """, (
        usuario_id,
        data
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados

def obter_resultados_por_mes(usuario_id, ano, mes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            DATE(data) AS data
        FROM resultados_provas
        WHERE usuario_id = ?
        AND strftime('%Y', data) = ?
        AND strftime('%m', data) = ?
        GROUP BY DATE(data)
        ORDER BY DATE(data)
    """, (
        usuario_id,
        str(ano),
        f"{mes:02d}"
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados

def salvar_respostas_prova(usuario_id,prova_id,questoes,respostas):

    conexao = conectar()
    cursor = conexao.cursor()

    for indice, questao in enumerate(questoes):

        if str(indice) not in respostas:
            continue

        resposta_usuario = respostas[str(indice)]

        correta = (
            1
            if resposta_usuario == questao["resposta"]
            else 0
        )

        cursor.execute("""
            INSERT INTO respostas_provas
            (
                usuario_id,
                prova_id,
                questao_numero,
                resposta,
                correta
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            usuario_id,
            prova_id,
            questao["numero"],
            resposta_usuario,
            correta
        ))

    conexao.commit()
    conexao.close()

def obter_respostas_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            resposta,
            correta
        FROM respostas_provas
        WHERE usuario_id = ?
        ORDER BY data
    """, (usuario_id,))

    respostas = cursor.fetchall()

    conexao.close()

    return respostas


def obter_resumo_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    # =====================================================
    # RESUMO DAS PROVAS
    # =====================================================

    cursor.execute("""
        SELECT
            COUNT(*) AS provas,

            COALESCE(SUM(acertos), 0) AS acertos_provas,

            COALESCE(SUM(erros), 0) AS erros_provas,

            COALESCE(SUM(nao_respondidas), 0) AS nao_respondidas

        FROM resultados_provas

        WHERE usuario_id = ?
    """, (usuario_id,))

    resultado_provas = cursor.fetchone()


    # =====================================================
    # QUESTÕES DO MÓDULO DE ESTUDOS
    # =====================================================

    cursor.execute("""
        SELECT
            COUNT(*) AS questoes_estudos,

            COALESCE(SUM(correta), 0) AS acertos_estudos

        FROM respostas_questoes

        WHERE usuario_id = ?
    """, (usuario_id,))

    resultado_estudos = cursor.fetchone()


    # =====================================================
    # SOMAR ACERTOS E ERROS
    # =====================================================

    acertos = (resultado_provas["acertos_provas"]+resultado_estudos["acertos_estudos"])


    erros_provas = (resultado_provas["erros_provas"])


    questoes_estudos = (resultado_estudos["questoes_estudos"])


    # Nas questões de estudos:
    # cada resposta registrada é uma questão resolvida.
    # Portanto, as que não foram acertadas são erros.

    erros_estudos = (questoes_estudos - resultado_estudos["acertos_estudos"])


    erros = (erros_provas + erros_estudos)


    # =====================================================
    # QUESTÕES REALMENTE RESOLVIDAS
    # =====================================================

    questoes = (acertos + erros)


    # =====================================================
    # QUESTÕES EM BRANCO
    # =====================================================

    nao_respondidas = (resultado_provas["nao_respondidas"])


    conexao.close()


    return {

        "provas":
            resultado_provas["provas"],

        "questoes":
            questoes,

        "acertos":
            acertos,

        "erros":
            erros,

        "nao_respondidas":
            nao_respondidas

    }

def obter_desempenho_por_area(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            correta
        FROM respostas_provas
        WHERE usuario_id = ?
    """, (usuario_id,))

    respostas = cursor.fetchall()

    conexao.close()


    desempenho = {}


    for resposta in respostas:

        prova_id = resposta["prova_id"]
        numero = resposta["questao_numero"]
        correta = resposta["correta"]


        prova = obter_prova(prova_id)

        if prova is None:
            continue


        questao = next(
            (
                q for q in prova.questoes
                if q.numero == numero
            ),
            None
        )


        if questao is None:
            continue


        area = questao.area


        if area not in desempenho:

            desempenho[area] = {

                "questoes": 0,

                "acertos": 0,

                "erros": 0

            }


        desempenho[area]["questoes"] += 1


        if correta:

            desempenho[area]["acertos"] += 1

        else:

            desempenho[area]["erros"] += 1


    for area in desempenho:

        total = desempenho[area]["questoes"]

        desempenho[area]["porcentagem"] = round((desempenho[area]["acertos"]/ total) * 100,1)

    return desempenho

def obter_provas_realizadas(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT prova_id
        FROM resultados_provas
        WHERE usuario_id = ?
    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados

def obter_segundos_provas(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = ?
    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    total_segundos = 0

    for resultado in resultados:

        tempo = resultado["tempo_gasto"]

        if not tempo:
            continue

        horas, minutos, segundos = map(int,tempo.split(":"))

        total_segundos += (horas * 3600 + minutos * 60 + segundos)

    return total_segundos

def obter_provas_por_periodo(usuario_id,data_inicio,data_fim):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            DATE(data_realizacao) AS data,
            tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = ?
        AND DATE(data_realizacao) BETWEEN ? AND ?
        ORDER BY data_realizacao
    """, (
        usuario_id,
        data_inicio,
        data_fim
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados

def converter_tempo_para_segundos(tempo):

    if not tempo:
        return 0

    horas, minutos, segundos = map(int,tempo.split(":"))

    return (
        horas * 3600
        + minutos * 60
        + segundos
    )