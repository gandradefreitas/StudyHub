from calendar import monthrange
from datetime import date, timedelta

from flask import jsonify, redirect, render_template, request, session, url_for

from database.questoes_repository import obter_desempenho_questoes, obter_desempenho_questoes_por_area
from database.resultados_repository import (
    listar_resultados_usuario, obter_desempenho_por_area, obter_resumo_usuario,
)
from services.metricas_estudo import (
    obter_evolucao_estudos, obter_tempo_total_estudado, resumir_desempenho_objetivo,
)
from services.provas_service import obter_catalogo_por_id


def pagina_estatisticas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:
        return redirect(
            url_for("pagina_login")
        )

    return render_template("estatisticas/estatisticas.html", **_desempenho_objetivo(usuario_id))


def _desempenho_objetivo(usuario_id):
    return resumir_desempenho_objetivo(obter_desempenho_por_area(usuario_id, por_prova=True))


def estatisticas_resumo():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    resultado = obter_resumo_usuario(
        usuario_id
    )

    total_segundos = obter_tempo_total_estudado(usuario_id)

    provas = resultado["provas"]
    questoes = resultado["questoes"]
    acertos = resultado["acertos"]
    erros = resultado["erros"]
    nao_respondidas = resultado["nao_respondidas"]

    respondidas = (
        acertos + erros
    )

    if respondidas > 0:

        porcentagem = (
            acertos / respondidas
        ) * 100

    else:

        porcentagem = 0

    return jsonify({

        "horas_estudadas":
            total_segundos,

        "provas":
            provas,

        "questoes":
            questoes,

        "respondidas":
            respondidas,

        "acertos":
            acertos,

        "erros":
            erros,

        "nao_respondidas":
            nao_respondidas,

        "porcentagem":
            round(
                porcentagem,
                1
            )
    })


def estatisticas_evolucao():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    hoje = date.today()
    if "dias" in request.args:
        dias = request.args.get("dias", type=int)
        if dias is None or not 1 <= dias <= 366:
            return jsonify({"erro": "Período inválido."}), 400
        inicio = hoje - timedelta(days=dias - 1)
        fim = hoje
    else:
        ano = request.args.get("ano", default=hoje.year, type=int)
        mes = request.args.get("mes", default=hoje.month, type=int)
        if not 1 <= ano <= 9999 or not 1 <= mes <= 12:
            return jsonify({"erro": "Ano ou mês inválido."}), 400
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, monthrange(ano, mes)[1])

    return jsonify(obter_evolucao_estudos(usuario_id, inicio, fim))


def estatisticas_provas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    resultados = listar_resultados_usuario(
        usuario_id
    )

    provas = []

    for resultado in resultados:

        id_prova = int(
            resultado["prova_id"]
        )

        catalogo = obter_catalogo_por_id(
            id_prova
        )

        if catalogo is None:
            continue

        provas.append({

            "id":
                id_prova,

            "nome":
                catalogo["nome"],

            "dia":
                catalogo["dia"],

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
                resultado["porcentagem"],

            "data":
                resultado["data_realizacao"]
        })

    return jsonify(provas)


def estatisticas_areas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    desempenho = obter_desempenho_por_area(
        usuario_id
    )

    return jsonify(desempenho)


def estatisticas_questoes_areas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    desempenho = obter_desempenho_questoes_por_area(
        usuario_id
    )

    return jsonify(desempenho)


def estatisticas_questoes_detalhadas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    criterio = request.args.get("criterio", "dificuldade")

    criterios_permitidos = {
        "dificuldade",
        "competencia",
        "habilidade",
        "lingua"
    }

    if criterio not in criterios_permitidos:

        return jsonify({
            "erro": "Critério de análise inválido."
        }), 400

    desempenho = obter_desempenho_questoes(
        usuario_id,
        criterio
    )

    return jsonify(desempenho)


def registrar_estatisticas(app):
    app.add_url_rule("/estatisticas", view_func=pagina_estatisticas)
    app.add_url_rule("/estatisticas/resumo", view_func=estatisticas_resumo)
    app.add_url_rule("/estatisticas/evolucao", view_func=estatisticas_evolucao)
    app.add_url_rule("/estatisticas/provas", view_func=estatisticas_provas)
    app.add_url_rule("/estatisticas/areas", view_func=estatisticas_areas)
    app.add_url_rule("/estatisticas/questoes-areas", view_func=estatisticas_questoes_areas)
    app.add_url_rule("/estatisticas/questoes-detalhadas", view_func=estatisticas_questoes_detalhadas)
