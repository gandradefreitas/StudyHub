from database.conexao import conectar
from database.respostas_discursivas_repository import DURACAO_DISCURSIVA_SQL


def ranking_questoes():
    with conectar() as banco:
        return banco.execute("""
            WITH atividades AS (
                SELECT usuario_id, COUNT(*) AS resolvidas, COALESCE(SUM(correta), 0) AS acertos
                FROM respostas_questoes GROUP BY usuario_id
                UNION ALL
                SELECT usuario_id, SUM(acertos::bigint + erros), SUM(acertos)
                FROM resultados_provas GROUP BY usuario_id
            ), totais AS (
                SELECT usuario_id, SUM(resolvidas)::bigint AS resolvidas, SUM(acertos)::bigint AS acertos
                FROM atividades GROUP BY usuario_id
            )
            SELECT u.id, u.nome, f.usuario_id IS NOT NULL AS tem_foto, t.resolvidas,
                   100 * t.acertos::numeric / t.resolvidas AS aproveitamento
            FROM totais t JOIN usuarios u ON u.id = t.usuario_id
            LEFT JOIN fotos_perfil f ON f.usuario_id = u.id
            WHERE t.resolvidas > 0
            ORDER BY t.resolvidas DESC, aproveitamento DESC, u.id
            LIMIT 50
        """).fetchall()


def ranking_nivel():
    with conectar() as banco:
        return banco.execute("""
            WITH totais AS (
                SELECT usuario_id, SUM(exp_decimos) AS exp_decimos
                FROM experiencia_atividades GROUP BY usuario_id
            )
            SELECT u.id, u.nome, f.usuario_id IS NOT NULL AS tem_foto, t.exp_decimos
            FROM totais t JOIN usuarios u ON u.id = t.usuario_id
            LEFT JOIN fotos_perfil f ON f.usuario_id = u.id
            ORDER BY t.exp_decimos DESC, u.id
            LIMIT 50
        """).fetchall()


def ranking_tempo():
    with conectar() as banco:
        return banco.execute(f"""
            WITH atividades AS (
                SELECT usuario_id, SUM(duracao)::bigint AS segundos
                FROM estudos WHERE duracao > 0 GROUP BY usuario_id
                UNION ALL
                SELECT usuario_id, SUM(
                    split_part(tempo_gasto, ':', 1)::bigint * 3600
                    + split_part(tempo_gasto, ':', 2)::integer * 60
                    + split_part(tempo_gasto, ':', 3)::integer
                )::bigint
                FROM resultados_provas
                WHERE tempo_gasto ~ '^[0-9]{{1,8}}:[0-5][0-9]:[0-5][0-9]$'
                GROUP BY usuario_id
                UNION ALL
                SELECT usuario_id, SUM({DURACAO_DISCURSIVA_SQL})::bigint
                FROM tentativas_provas_discursivas GROUP BY usuario_id
                UNION ALL
                SELECT usuario_id, SUM(tempo_segundos)::bigint
                FROM redacoes WHERE tempo_segundos > 0 GROUP BY usuario_id
            ), totais AS (
                SELECT usuario_id, SUM(segundos)::bigint AS segundos
                FROM atividades GROUP BY usuario_id
            )
            SELECT u.id, u.nome, f.usuario_id IS NOT NULL AS tem_foto, t.segundos
            FROM totais t JOIN usuarios u ON u.id = t.usuario_id
            LEFT JOIN fotos_perfil f ON f.usuario_id = u.id
            WHERE t.segundos > 0
            ORDER BY t.segundos DESC, u.id
            LIMIT 50
        """).fetchall()
