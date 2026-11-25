from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from database.idiomas_repository import obter_progresso, registrar_leitura
from services.idiomas_service import IDIOMAS, TEXTOS, montar_estatisticas

idiomas = Blueprint("idiomas", __name__, url_prefix="/idiomas")


@idiomas.before_request
def exigir_login():
    if not session.get("usuario_id"):
        return redirect(url_for("pagina_login"))


@idiomas.get("")
def listar():
    hoje, progresso = obter_progresso(session["usuario_id"])
    return render_template(
        "idiomas/lista.html",
        idiomas=IDIOMAS,
        textos=TEXTOS.values(),
        progresso=progresso,
        estatisticas=montar_estatisticas(progresso.values(), hoje, request.args.get("mes")),
        idioma_aberto=request.args.get("idioma"),
        classe_body="sidebar-toggle",
    )


@idiomas.route("/<texto_id>", methods=["GET", "POST"])
def leitura(texto_id):
    texto = TEXTOS.get(texto_id)
    if texto is None:
        abort(404)

    usuario_id = session["usuario_id"]
    questoes = texto["questoes"]
    respostas = {}
    erro = False
    if request.method == "POST":
        for numero, questao in enumerate(questoes, 1):
            opcoes = {str(i) for i in range(len(questao["opcoes"]))}
            selecao = request.form.getlist(f"questao-{numero}")
            if len(selecao) == 1 and selecao[0] in opcoes:
                respostas[numero] = int(selecao[0])
        if len(respostas) == len(questoes):
            acertos = sum(respostas[n] == q["correta"] for n, q in enumerate(questoes, 1))
            if registrar_leitura(usuario_id, texto_id, texto["palavras"], acertos):
                return redirect(url_for("idiomas.leitura", texto_id=texto_id, _anchor="resultado"), code=303)
        erro = True

    _, progresso = obter_progresso(usuario_id)
    resultado = progresso.get(texto_id)
    espera = resultado["espera_segundos"] if resultado else 0
    bloqueado = bool(espera and request.method == "POST")
    return render_template(
        "idiomas/leitura.html",
        texto=texto,
        idioma=IDIOMAS[texto["idioma"]],
        respostas=respostas,
        erro=erro and not espera,
        resultado=resultado,
        espera_minutos=(espera + 59) // 60,
        classe_body="sidebar-toggle",
    ), (429 if bloqueado else 422 if erro else 200), (
        {"Retry-After": str(espera)} if bloqueado else {}
    )
