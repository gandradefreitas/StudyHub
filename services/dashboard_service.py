from studyhub.database.estudos_repository import obter_segundos_estudados_hoje, obter_questoes_respondidas_hoje, \
    obter_total_segundos, obter_segundos_provas_hoje
from studyhub.database.resultados_repository import obter_resumo_usuario, obter_provas_realizadas, obter_segundos_provas
from studyhub.database.usuario_repository import obter_usuario_por_id, obter_configuracoes
from studyhub.services.estudo_service import obter_horas_estudadas, formatar_duracao
from studyhub.services.provas_service import listar_provas
from studyhub.database.tarefa_repository import (contar_tarefas_usuario,obter_proximas_tarefas)

def obter_proxima_prova(usuario_id):

    provas = listar_provas()

    realizadas = obter_provas_realizadas(usuario_id)

    ids_realizadas = {
        int(resultado[0])
        for resultado in realizadas
    }

    for prova in provas:

        if prova["id"] not in ids_realizadas:
            return prova

    return None

def carregar_dashboard(usuario_id):

    usuario = obter_usuario_por_id(usuario_id)

    estatisticas = contar_tarefas_usuario(usuario_id)

    estatisticas["horas_estudadas"] = (
        obter_horas_estudadas(
            usuario_id
        )
    )

    tarefas = obter_proximas_tarefas(usuario_id)

    resumo = obter_resumo_usuario(usuario_id)

    respondidas = (resumo["acertos"] + resumo["erros"])

    segundos_estudo_hoje = (obter_segundos_estudados_hoje(usuario_id))

    segundos_provas_hoje = (obter_segundos_provas_hoje(usuario_id))

    segundos_hoje = (segundos_estudo_hoje + segundos_provas_hoje)

    questoes_hoje = (obter_questoes_respondidas_hoje(usuario_id))

    configuracoes = obter_configuracoes(usuario_id)

    meta_estudo = configuracoes["meta_estudo"]

    meta_questoes = configuracoes["meta_questoes"]

    meta_estudo_segundos = (meta_estudo * 60)

    estudo_atual_formatado = formatar_duracao(segundos_hoje)

    estudo_meta_formatado = formatar_duracao(meta_estudo_segundos)

    proxima_prova = obter_proxima_prova(usuario_id)

    segundos_estudo = obter_total_segundos(usuario_id)

    segundos_provas = obter_segundos_provas(usuario_id)

    segundos_totais = (segundos_estudo + segundos_provas)

    tempo_estudado_total = formatar_duracao(segundos_totais)

    if respondidas > 0:

        porcentagem = (resumo["acertos"] / respondidas) * 100

    else:

        porcentagem = 0


    if meta_estudo_segundos > 0:

        porcentagem_estudo = (segundos_hoje / meta_estudo_segundos) * 100

    else:

        porcentagem_estudo = 0


    if meta_questoes > 0:

        porcentagem_questoes = (questoes_hoje / meta_questoes) * 100

    else:

        porcentagem_questoes = 0

    porcentagem_estudo = min(porcentagem_estudo,100)

    porcentagem_questoes = min(porcentagem_questoes,100)

    return {

        "usuario": usuario,

        "estatisticas": estatisticas,

        "tarefas": tarefas,

        "resumo": resumo,

        "desempenho": round(
            porcentagem,
            1
        ),

        "horas_estudadas": tempo_estudado_total,

        "proxima_prova": proxima_prova,

        "metas": {

            "estudo_atual": segundos_hoje,

            "estudo_meta": meta_estudo,

            "estudo_atual_formatado": estudo_atual_formatado,

            "estudo_meta_formatado": estudo_meta_formatado,

            "estudo_porcentagem": round(
                porcentagem_estudo,
                1
            ),

            "questoes_atual": questoes_hoje,

            "questoes_meta": meta_questoes,

            "questoes_porcentagem": round(
                porcentagem_questoes,
                1
            )

        }

    }