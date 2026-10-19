from datetime import datetime, timedelta

from database.conexao import conectar


TEMPO_INATIVIDADE = 300  # 5 minutos


def iniciar_estudo(usuario_id):
    agora = datetime.now()

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO estudos (
                usuario_id,
                inicio,
                duracao,
                ativa,
                inicio_segmento,
                ultima_atividade
            )
            VALUES (%s, %s, 0, 1, %s, %s)
            RETURNING id, inicio, duracao,
                      inicio_segmento, ultima_atividade
        """, (usuario_id, agora, agora, agora))

        estudo = cursor.fetchone()

        conexao.commit()

        return estudo

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def finalizar_estudo(estudo_id, fim, duracao, usuario_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE estudos
            SET fim = %s,
                duracao = %s,
                ativa = 0,
                inicio_segmento = NULL
            WHERE id = %s
              AND usuario_id = %s
              AND ativa = 1
        """, (fim, duracao, estudo_id, usuario_id))

        conexao.commit()

        return cursor.rowcount > 0

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def obter_total_segundos(usuario_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(duracao), 0) AS total
            FROM estudos
            WHERE usuario_id = %s
        """, (usuario_id,))

        resultado = cursor.fetchone()

        return resultado["total"]

    finally:
        conexao.close()


def obter_estudos_por_data(usuario_id, data):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT inicio, fim, duracao
            FROM estudos
            WHERE usuario_id = %s
              AND inicio::date = %s
            ORDER BY inicio
        """, (usuario_id, data))

        return cursor.fetchall()

    finally:
        conexao.close()


def obter_estudo_ativo(usuario_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                inicio,
                fim,
                duracao,
                ativa,
                inicio_segmento,
                ultima_atividade
            FROM estudos
            WHERE usuario_id = %s
              AND ativa = 1
            ORDER BY id DESC
            LIMIT 1
        """, (usuario_id,))

        return cursor.fetchone()

    finally:
        conexao.close()


def possui_estudo_ativo(usuario_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id
            FROM estudos
            WHERE usuario_id = %s
              AND ativa = 1
            LIMIT 1
        """, (usuario_id,))

        return cursor.fetchone() is not None

    finally:
        conexao.close()


def registrar_atividade_estudo(usuario_id, tipo_evento):
    """
    Atualiza o tempo acumulado de uma sessão de estudo.

    tipo_evento:
        - atividade: interação real do usuário.
        - heartbeat: atualização periódica do cronômetro.

    inicio_segmento indica quando começou o trecho atual.
    ultima_atividade indica a última interação real.

    Retorna os dados atualizados da sessão.
    """
    if tipo_evento not in ("atividade", "heartbeat"):
        raise ValueError("Tipo de evento inválido.")

    agora = datetime.now()

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                id,
                duracao,
                inicio_segmento,
                ultima_atividade
            FROM estudos
            WHERE usuario_id = %s
              AND ativa = 1
            ORDER BY id DESC
            LIMIT 1
            FOR UPDATE
        """, (usuario_id,))

        estudo = cursor.fetchone()

        if estudo is None:
            conexao.commit()
            return None

        estudo_id = estudo["id"]
        duracao = int(estudo["duracao"] or 0)
        inicio_segmento = estudo["inicio_segmento"]
        ultima_atividade = estudo["ultima_atividade"]

        # Recuperação de sessões antigas que não possuem
        # os campos adicionados para o cronômetro automático.
        if ultima_atividade is None:
            ultima_atividade = agora

        # A sessão está pausada.
        if inicio_segmento is None:
            if tipo_evento == "atividade":
                # Retoma a contagem somente após interação real.
                cursor.execute("""
                    UPDATE estudos
                    SET inicio_segmento = %s,
                        ultima_atividade = %s
                    WHERE id = %s
                      AND usuario_id = %s
                      AND ativa = 1
                """, (
                    agora,
                    agora,
                    estudo_id,
                    usuario_id,
                ))

                pausado = False

            else:
                # Heartbeat não retoma uma sessão pausada.
                cursor.execute("""
                    UPDATE estudos
                    SET ultima_atividade = %s
                    WHERE id = %s
                      AND usuario_id = %s
                      AND ativa = 1
                """, (
                    ultima_atividade,
                    estudo_id,
                    usuario_id,
                ))

                pausado = True

            conexao.commit()

            return {
                "id": estudo_id,
                "duracao": duracao,
                "pausado": pausado,
            }

        # Limite de tempo que pode ser contabilizado após
        # a última interação real do usuário.
        limite_inatividade = (
            ultima_atividade
            + timedelta(seconds=TEMPO_INATIVIDADE)
        )

        # Não contabiliza além do limite de inatividade.
        fim_segmento = min(agora, limite_inatividade)

        if fim_segmento > inicio_segmento:
            segundos_adicionais = int(
                (fim_segmento - inicio_segmento).total_seconds()
            )

            duracao += max(0, segundos_adicionais)

        # Se houve uma interação real, ela pode renovar
        # o período de atividade.
        if tipo_evento == "atividade":
            cursor.execute("""
                UPDATE estudos
                SET duracao = %s,
                    inicio_segmento = %s,
                    ultima_atividade = %s
                WHERE id = %s
                  AND usuario_id = %s
                  AND ativa = 1
            """, (
                duracao,
                agora,
                agora,
                estudo_id,
                usuario_id,
            ))

            pausado = False

        elif agora >= limite_inatividade:
            # O tempo de inatividade foi atingido.
            cursor.execute("""
                UPDATE estudos
                SET duracao = %s,
                    inicio_segmento = NULL
                WHERE id = %s
                  AND usuario_id = %s
                  AND ativa = 1
            """, (
                duracao,
                estudo_id,
                usuario_id,
            ))

            pausado = True

        else:
            # Ainda há atividade recente. Avança o segmento
            # para impedir que o próximo heartbeat conte
            # novamente o tempo já contabilizado.
            cursor.execute("""
                UPDATE estudos
                SET duracao = %s,
                    inicio_segmento = %s
                WHERE id = %s
                  AND usuario_id = %s
                  AND ativa = 1
            """, (
                duracao,
                agora,
                estudo_id,
                usuario_id,
            ))

            pausado = False

        conexao.commit()

        return {
            "id": estudo_id,
            "duracao": duracao,
            "pausado": pausado,
        }

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def obter_estudos_por_mes(usuario_id, ano, mes):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT inicio::date AS data
            FROM estudos
            WHERE usuario_id = %s
              AND EXTRACT(YEAR FROM inicio) = %s
              AND EXTRACT(MONTH FROM inicio) = %s
              AND duracao > 0
            GROUP BY inicio::date
            ORDER BY inicio::date
        """, (usuario_id, ano, mes))

        return cursor.fetchall()

    finally:
        conexao.close()


def obter_estudos_por_periodo(usuario_id, inicio, fim):
    conexao = conectar()

    try:
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
        """, (usuario_id, inicio, fim))

        return cursor.fetchall()

    finally:
        conexao.close()


def obter_segundos_estudados_hoje(usuario_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(duracao), 0) AS segundos
            FROM estudos
            WHERE usuario_id = %s
              AND inicio::date = CURRENT_DATE
        """, (usuario_id,))

        resultado = cursor.fetchone()

        return resultado["segundos"]

    finally:
        conexao.close()

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
