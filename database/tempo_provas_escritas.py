from database.conexao import conectar
from database.respostas_discursivas_repository import obter_duracao_discursiva_por_dia
from collections import Counter


def obter_duracao_provas_escritas_por_dia(usuario_id, inicio=None, fim=None, *, hoje=False):
    duracoes = Counter({dia["data"]: dia["duracao"] for dia in
                        obter_duracao_discursiva_por_dia(usuario_id, inicio, fim, hoje=hoje)})
    with conectar() as conexao:
        redacoes = conexao.execute("""
            SELECT criado_em::date AS data, SUM(tempo_segundos) AS duracao
            FROM redacoes
            WHERE usuario_id = %s AND tempo_segundos IS NOT NULL
              AND (NOT %s OR criado_em::date = (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date)
              AND (%s::date IS NULL OR criado_em::date >= %s::date)
              AND (%s::date IS NULL OR criado_em::date <= %s::date)
            GROUP BY criado_em::date
        """, (usuario_id, hoje, inicio, inicio, fim, fim)).fetchall()
    for dia in redacoes:
        duracoes[dia["data"]] += dia["duracao"]
    return [{"data": data, "duracao": duracao} for data, duracao in duracoes.items()]
