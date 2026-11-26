from database.conexao import conectar


# Limite das provas discursivas do ITA 2025, inclusive para envios tardios.
DURACAO_DISCURSIVA_SQL = """
    CASE
        WHEN status IN ('finalizada', 'corrigida')
             AND data_inicio IS NOT NULL AND data_finalizacao IS NOT NULL
        THEN LEAST(
            14400,
            GREATEST(0, FLOOR(EXTRACT(EPOCH FROM (data_finalizacao - data_inicio))))
        )::integer
    END
"""


class LimiteDiarioTentativaAtingido(Exception):
    """O usuário já iniciou a prova desta disciplina no dia local atual."""


def obter_tentativa_em_andamento(
    usuario_id,
    instituicao,
    ano,
    fase,
    disciplina,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
              AND status = 'em_andamento'
            ORDER BY data_inicio DESC, id DESC
            LIMIT 1
            """,
            (
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina,
            ),
        )

        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return resultado["id"]

    finally:
        conexao.close()


def criar_tentativa(
    usuario_id,
    instituicao,
    ano,
    fase,
    disciplina,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO tentativas_provas_discursivas (
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina,
            ),
        )

        resultado = cursor.fetchone()
        tentativa_id = resultado["id"]

        conexao.commit()

        return tentativa_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def obter_ou_criar_tentativa(
    usuario_id,
    instituicao,
    ano,
    fase,
    disciplina,
):
    conexao = conectar()
    try:
        cursor = conexao.cursor()
        chave_lock = (
            f"tentativa_diaria:{usuario_id}:{instituicao}:{ano}:"
            f"{fase}:{disciplina}"
        )
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (chave_lock,),
        )

        cursor.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
              AND status = 'em_andamento'
            ORDER BY data_inicio DESC, id DESC
            LIMIT 1
            """,
            (usuario_id, instituicao, ano, fase, disciplina),
        )
        tentativa_em_andamento = cursor.fetchone()
        if tentativa_em_andamento is not None:
            conexao.commit()
            return tentativa_em_andamento["id"]

        cursor.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
              AND status IN ('finalizada', 'corrigida')
              AND (
                    (data_inicio AT TIME ZONE current_setting('TimeZone'))
                    AT TIME ZONE 'America/Sao_Paulo'
                  )::date =
                  (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date
            ORDER BY data_inicio DESC, id DESC
            LIMIT 1
            """,
            (usuario_id, instituicao, ano, fase, disciplina),
        )
        tentativa_do_dia = cursor.fetchone()
        if tentativa_do_dia is not None:
            conexao.commit()
            raise LimiteDiarioTentativaAtingido(
                "Você já iniciou uma prova desta disciplina hoje."
            )

        cursor.execute(
            """
            INSERT INTO tentativas_provas_discursivas (
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (usuario_id, instituicao, ano, fase, disciplina),
        )
        tentativa_id = cursor.fetchone()["id"]
        conexao.commit()
        return tentativa_id
    except LimiteDiarioTentativaAtingido:
        raise
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def salvar_resposta(tentativa_id, questao_numero, item_letra, resposta):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        # Bloqueia a linha da tentativa durante a operação.
        # Isso também coordena o salvamento com a finalização.
        cursor.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND status = 'em_andamento'
            FOR UPDATE
            """,
            (tentativa_id,),
        )

        tentativa = cursor.fetchone()

        if tentativa is None:
            raise ValueError(
                "Não é possível alterar respostas de uma tentativa "
                "que não está em andamento."
            )

        # Procura uma resposta existente para evitar duplicações.
        if item_letra is None:
            cursor.execute(
                """
                SELECT id
                FROM respostas_discursivas
                WHERE tentativa_id = %s
                  AND questao_numero = %s
                  AND item_letra IS NULL
                LIMIT 1
                """,
                (tentativa_id, questao_numero),
            )
        else:
            cursor.execute(
                """
                SELECT id
                FROM respostas_discursivas
                WHERE tentativa_id = %s
                  AND questao_numero = %s
                  AND item_letra = %s
                LIMIT 1
                """,
                (tentativa_id, questao_numero, item_letra),
            )

        registro = cursor.fetchone()

        if registro is None:
            cursor.execute(
                """
                INSERT INTO respostas_discursivas (
                    tentativa_id,
                    questao_numero,
                    item_letra,
                    resposta
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    tentativa_id,
                    questao_numero,
                    item_letra,
                    resposta,
                ),
            )
        else:
            cursor.execute(
                """
                UPDATE respostas_discursivas
                SET resposta = %s,
                    data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (resposta, registro["id"]),
            )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def obter_respostas(tentativa_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT questao_numero, item_letra, resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            ORDER BY questao_numero, item_letra
        """, (tentativa_id,))

        registros = cursor.fetchall()

        return {
            (registro["questao_numero"], registro["item_letra"]): registro["resposta"]
            for registro in registros
        }

    finally:
        conexao.close()


def obter_status_tentativa(
    tentativa_id,
    usuario_id,
    instituicao,
    ano,
    fase,
    disciplina,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT status
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
            """,
            (
                tentativa_id,
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina,
            ),
        )

        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return resultado["status"]

    finally:
        conexao.close()


def obter_ultima_tentativa(
    usuario_id,
    instituicao,
    ano,
    fase,
    disciplina,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id, status
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
            ORDER BY data_inicio DESC, id DESC
            LIMIT 1
            """,
            (
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina,
            ),
        )

        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return {
            "id": resultado["id"],
            "status": resultado["status"],
        }

    finally:
        conexao.close()



def salvar_respostas_em_lote(tentativa_id, respostas, *, usuario_id, prova, finalizar=False):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        # Bloqueia a tentativa e verifica seu status.
        cursor.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE id = %s AND usuario_id = %s
              AND instituicao = %s AND ano = %s AND fase = %s AND disciplina = %s
              AND status = 'em_andamento'
            FOR UPDATE
            """,
            (tentativa_id, usuario_id, prova.instituicao, prova.ano, prova.fase, prova.disciplina),
        )

        tentativa = cursor.fetchone()

        if tentativa is None:
            raise ValueError(
                "Tentativa não encontrada, já finalizada ou sem permissão."
            )

        # Salva todas as respostas na mesma transação.
        for resposta in respostas:
            questao_numero = resposta["questao_numero"]
            item_letra = resposta["item_letra"]
            texto = resposta["resposta"]

            cursor.execute(
                """
                SELECT id
                FROM respostas_discursivas
                WHERE tentativa_id = %s AND questao_numero = %s
                  AND item_letra IS NOT DISTINCT FROM %s
                LIMIT 1
                """,
                (tentativa_id, questao_numero, item_letra),
            )

            registro = cursor.fetchone()

            if registro is None:
                cursor.execute(
                    """
                    INSERT INTO respostas_discursivas (
                        tentativa_id,
                        questao_numero,
                        item_letra,
                        resposta
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        tentativa_id,
                        questao_numero,
                        item_letra,
                        texto,
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE respostas_discursivas
                    SET resposta = %s,
                        data_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (texto, registro["id"]),
                )

        if finalizar:
            cursor.execute(
                """
                UPDATE tentativas_provas_discursivas
                SET status = 'finalizada', data_finalizacao = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (tentativa_id,),
            )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def obter_tentativa_discursiva_por_id(
    tentativa_id,
    usuario_id,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                id,
                usuario_id,
                instituicao,
                ano,
                fase,
                disciplina,
                status,
                nota_total,
                nota_maxima,
                data_inicio,
                data_finalizacao,
                data_correcao,
                resultado_correcao,
                tentativas_correcao,
                proxima_tentativa_correcao,
                correcao_reivindicada_ate
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
            """,
            (
                tentativa_id,
                usuario_id,
            ),
        )

        return cursor.fetchone()

    finally:
        conexao.close()


def obter_segundos_restantes_tentativa(
    tentativa_id,
    usuario_id,
    duracao_segundos,
):
    """Calcula o tempo restante a partir do início persistido no banco."""
    conexao = conectar()

    try:
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT GREATEST(
                0,
                CEIL(EXTRACT(EPOCH FROM (
                    data_inicio
                    + (%s * INTERVAL '1 second')
                    - LOCALTIMESTAMP
                )))
            )::INTEGER AS segundos_restantes
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
              AND status = 'em_andamento'
            """,
            (duracao_segundos, tentativa_id, usuario_id),
        )
        resultado = cursor.fetchone()
        return (
            int(resultado["segundos_restantes"])
            if resultado is not None
            else 0
        )
    finally:
        conexao.close()


def salvar_resultado_correcao_discursiva(
    tentativa_id, usuario_id, pacote, status, nota=None, nota_maxima=None, *,
    reivindicada_ate, tentar_em=None,
):
    from psycopg.types.json import Jsonb

    with conectar() as conexao:
        return conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET resultado_correcao = %s, status = %s, nota_total = %s, nota_maxima = %s,
                proxima_tentativa_correcao = CURRENT_TIMESTAMP + %s * INTERVAL '1 second',
                correcao_reivindicada_ate = NULL,
                data_correcao = CASE WHEN %s = 'corrigida' THEN CURRENT_TIMESTAMP END
            WHERE id = %s AND usuario_id = %s AND status = 'finalizada'
              AND correcao_reivindicada_ate = %s
              AND correcao_reivindicada_ate > CURRENT_TIMESTAMP
        """, (Jsonb(pacote), status, nota, nota_maxima, tentar_em, status,
              tentativa_id, usuario_id, reivindicada_ate)).rowcount == 1


def reivindicar_correcao_discursiva(tentativa_id=None, usuario_id=None):
    """Reserva apenas uma tentativa elegível, inclusive com workers concorrentes."""
    from database.fila_redacoes_repository import MAX_TENTATIVAS

    with conectar() as conexao:
        return conexao.execute("""
            WITH candidata AS (
                SELECT id FROM tentativas_provas_discursivas
                WHERE status = 'finalizada'
                  AND disciplina IN ('Matemática', 'Física', 'Química')
                  AND (resultado_correcao IS NULL OR resultado_correcao->>'status' = 'indisponivel')
                  AND tentativas_correcao < %s
                  AND (%s::integer IS NULL OR id = %s)
                  AND (%s::integer IS NULL OR usuario_id = %s)
                  AND (proxima_tentativa_correcao IS NULL OR proxima_tentativa_correcao <= CURRENT_TIMESTAMP)
                  AND (correcao_reivindicada_ate IS NULL OR correcao_reivindicada_ate <= CURRENT_TIMESTAMP)
                ORDER BY data_finalizacao NULLS LAST, id
                LIMIT 1 FOR UPDATE SKIP LOCKED
            )
            UPDATE tentativas_provas_discursivas AS t
            SET correcao_reivindicada_ate = CURRENT_TIMESTAMP + INTERVAL '10 minutes',
                tentativas_correcao = tentativas_correcao + 1
            FROM candidata WHERE t.id = candidata.id
            RETURNING t.id, t.usuario_id, t.disciplina, t.tentativas_correcao, t.correcao_reivindicada_ate
        """, (MAX_TENTATIVAS, tentativa_id, tentativa_id, usuario_id, usuario_id)).fetchone()


def reagendar_correcao_discursiva(tentativa_id, usuario_id):
    with conectar() as conexao:
        return conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET resultado_correcao = NULL, tentativas_correcao = 0,
                proxima_tentativa_correcao = NULL, correcao_reivindicada_ate = NULL
            WHERE id = %s AND usuario_id = %s AND status = 'finalizada'
              AND resultado_correcao->>'status' = 'falha_definitiva'
        """, (tentativa_id, usuario_id)).rowcount == 1


def recuperar_discursivas_esgotadas():
    from database.fila_redacoes_repository import MAX_TENTATIVAS

    with conectar() as conexao:
        conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET resultado_correcao = '{"status":"falha_definitiva"}'::jsonb,
                correcao_reivindicada_ate = NULL, proxima_tentativa_correcao = NULL
            WHERE status = 'finalizada' AND disciplina IN ('Matemática', 'Física', 'Química')
              AND tentativas_correcao >= %s
              AND (resultado_correcao IS NULL OR resultado_correcao->>'status' = 'indisponivel')
              AND (correcao_reivindicada_ate IS NULL OR correcao_reivindicada_ate <= CURRENT_TIMESTAMP)
        """, (MAX_TENTATIVAS,))


def listar_tentativas_discursivas_usuario(
    usuario_id,
):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            f"""
            SELECT
                id,
                instituicao,
                ano,
                fase,
                disciplina,
                status,
                nota_total,
                nota_maxima,
                data_inicio,
                data_finalizacao,
                data_correcao,
                resultado_correcao,
                {DURACAO_DISCURSIVA_SQL} AS duracao_segundos
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
            ORDER BY data_inicio DESC, id DESC
            """,
            (usuario_id,),
        )

        return cursor.fetchall()

    finally:
        conexao.close()


def obter_duracao_discursiva_por_dia(usuario_id, inicio=None, fim=None, *, hoje=False):
    """Soma as durações das tentativas concluídas no dia da finalização."""
    with conectar() as conexao:
        return conexao.execute(
            f"""
            SELECT data_finalizacao::date AS data,
                   SUM({DURACAO_DISCURSIVA_SQL}) AS duracao
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND status IN ('finalizada', 'corrigida')
              AND data_inicio IS NOT NULL AND data_finalizacao IS NOT NULL
              AND (NOT %s OR data_finalizacao::date = CURRENT_DATE)
              AND (%s::date IS NULL OR data_finalizacao >= %s::date)
              AND (%s::date IS NULL OR data_finalizacao < %s::date + 1)
            GROUP BY data_finalizacao::date
            """,
            (usuario_id, hoje, inicio, inicio, fim, fim),
        ).fetchall()
