from calendar import monthrange
from datetime import date

from services.dados import preparar_exportacao
from database.questoes_repository import obter_desempenho_questoes, obter_desempenho_questoes_por_area
from database.resultados_repository import obter_desempenho_por_area, obter_resumo_usuario
from services.metricas_estudo import (
    obter_evolucao_estudos, obter_tempo_total_estudado, resumir_desempenho_objetivo,
)
from services.provas_service import listar_provas


def obter_dados_relatorio(usuario_id):
    dados = preparar_exportacao(usuario_id)
    catalogo = {prova["id"]: prova for prova in listar_provas()}
    for chave in ("resultados_provas", "respostas_provas"):
        for registro in dados[chave]:
            prova_id = registro["prova_id"]
            prova = catalogo.get(prova_id)
            if prova:
                dia = {"Primeiro Dia": "Dia 1", "Segundo Dia": "Dia 2"}.get(prova["dia"], prova["dia"])
                registro["prova"] = f'{prova["nome"]} — {dia}' if dia else prova["nome"]
                registro["instituicao"] = prova["tipo"]
            else:
                registro["prova"] = f"Prova {prova_id}"
                registro["instituicao"] = None

    hoje = date.today()
    inicio = hoje.replace(day=1)
    fim = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])
    dados["estatisticas"] = {
        **resumir_desempenho_objetivo(obter_desempenho_por_area(usuario_id, por_prova=True)),
        "resumo": obter_resumo_usuario(usuario_id),
        "tempo_total_segundos": obter_tempo_total_estudado(usuario_id),
        "evolucao_mensal": obter_evolucao_estudos(usuario_id, inicio, fim),
        "questoes_praticadas_por_area": obter_desempenho_questoes_por_area(usuario_id),
        "analise_questoes_praticadas": {
            criterio: obter_desempenho_questoes(usuario_id, criterio)
            for criterio in ("dificuldade", "competencia", "habilidade", "lingua")
        },
    }
    return dados
