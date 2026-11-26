from flask import Blueprint, Response, abort, flash, redirect, request, session, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from database.usuario_repository import obter_foto_perfil
from services.configuracoes import atualizar_dados_conta
from services.foto_perfil_service import LIMITE_FOTO, preparar_foto

perfil = Blueprint("perfil", __name__, url_prefix="/perfil")


@perfil.post("")
def atualizar():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("pagina_login"))

    try:
        arquivo = request.files.get("foto")
        foto = preparar_foto(arquivo) if arquivo and arquivo.filename else None
    except RequestEntityTooLarge:
        session["erro_perfil"] = "Escolha uma foto de até 2 MB."
    except ValueError as erro:
        session["erro_perfil"] = str(erro)
    else:
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        sucesso, mensagem = atualizar_dados_conta(usuario_id, nome, email, foto=foto)
        if sucesso:
            session.pop("erro_perfil", None)
            session["nome"] = nome
            flash("Perfil atualizado com sucesso.", "mensagem-sucesso")
        else:
            session["erro_perfil"] = mensagem

    return redirect(url_for("dashboard"), code=303)


def limitar_upload_perfil():
    if request.endpoint == "perfil.atualizar":
        request.max_content_length = LIMITE_FOTO + 64 * 1024


@perfil.errorhandler(RequestEntityTooLarge)
def foto_grande(_erro):
    if not session.get("usuario_id"):
        return redirect(url_for("pagina_login"))
    session["erro_perfil"] = "Escolha uma foto de até 2 MB."
    return redirect(url_for("dashboard"), code=303)


@perfil.get("/foto")
def foto():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        abort(404)
    imagem = obter_foto_perfil(usuario_id)
    if imagem is None:
        abort(404)
    return Response(imagem, mimetype="image/jpeg")
