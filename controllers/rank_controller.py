from flask import Blueprint, Response, abort, current_app, redirect, render_template, request, session, url_for
from itsdangerous import BadData, URLSafeTimedSerializer

from database.rank_repository import ranking_nivel, ranking_questoes, ranking_tempo
from database.usuario_repository import obter_foto_perfil
from services.experiencia_service import calcular_progresso

rank = Blueprint("rank", __name__, url_prefix="/rank")


def assinatura_foto():
    return URLSafeTimedSerializer(current_app.secret_key, salt="rank-foto")


def formatar_tempo(segundos):
    horas, restante = divmod(segundos, 3600)
    minutos, segundos = divmod(restante, 60)
    return " ".join(f"{valor}{unidade}" for valor, unidade in (
        (horas, "h"), (minutos, "min"), (segundos, "s"),
    ) if valor)


@rank.get("")
def listar():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("pagina_login"))
    criterio = request.args.get("criterio", "questoes")
    consultas = {"questoes": ranking_questoes, "tempo": ranking_tempo, "nivel": ranking_nivel}
    consultar = consultas.get(criterio)
    if consultar is None:
        return redirect(url_for("rank.listar"))

    colocados = consultar()
    assinatura = assinatura_foto()
    for posicao, pessoa in enumerate(colocados, 1):
        pessoa["posicao"] = posicao
        pessoa["foto"] = (
            url_for("rank.foto", token=assinatura.dumps([usuario_id, pessoa["id"]]))
            if pessoa["tem_foto"] else None
        )
        if criterio == "tempo":
            pessoa["tempo"] = formatar_tempo(pessoa["segundos"])
        elif criterio == "nivel":
            pessoa["nivel"] = calcular_progresso(pessoa["exp_decimos"])["nivel"]
            inteiro, decimo = divmod(pessoa["exp_decimos"], 10)
            pessoa["exp"] = f"{inteiro:,}".replace(",", ".")
            if decimo:
                pessoa["exp"] += f",{decimo}"
        else:
            pessoa["taxa"] = f'{pessoa["aproveitamento"]:.1f}'.replace(".", ",")

    return render_template(
        "rank.html", criterio=criterio, colocados=colocados,
        classe_body="sidebar-toggle",
    )


@rank.get("/foto/<token>")
def foto(token):
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        abort(404)
    try:
        leitor, titular = assinatura_foto().loads(token, max_age=3600)
    except (BadData, ValueError, TypeError):
        abort(404)
    if leitor != usuario_id:
        abort(404)
    imagem = obter_foto_perfil(titular)
    if imagem is None:
        abort(404)
    return Response(imagem, mimetype="image/jpeg")
