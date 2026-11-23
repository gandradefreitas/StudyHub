import os
from datetime import datetime, timezone
from secrets import token_urlsafe

from authlib.integrations.flask_client import OAuth
from flask import abort, flash, redirect, render_template, request, session, url_for

from controllers.web.configuracoes_controller import excluir_conta as excluir_conta_controller
from controllers.web.login_controller import realizar_login
from database.usuario_repository import (
    buscar_por_email, buscar_por_google_id, excluir_usuario, obter_usuario_por_id,
    salvar_usuario_google, vincular_google,
)
from security.limite_login import limpar_tentativas, reservar_tentativa
from services.autenticacao import autenticar

oauth = OAuth()


def logout():

    session.clear()

    flash(
        "Você saiu da sua conta.",
        "mensagem-erro"
    )

    return redirect(
        url_for("pagina_login")
    )


def login_google():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


def google_callback():

    token = google.authorize_access_token()

    userinfo = token.get("userinfo")

    if not userinfo:
        return "Não foi possível obter os dados da conta Google.", 400

    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    nome = userinfo.get("name")
    email_verificado = userinfo.get("email_verified")

    if not google_id or not email:
        return "O Google não forneceu os dados necessários.", 400

    if not email_verificado:
        return "O e-mail da conta Google não foi verificado.", 400

    exclusao = session.get("google_exclusao")
    if exclusao and exclusao["estado"] == request.args.get("state"):
        session.pop("google_exclusao", None)
        usuario_id = session.get("usuario_id")
        conta = obter_usuario_por_id(usuario_id) if usuario_id else None
        if (
            usuario_id != exclusao["usuario_id"]
            or datetime.now(timezone.utc).timestamp() > exclusao["expira_em"]
            or not conta
            or conta["google_id"] != google_id
            or conta["senha"] is not None
        ):
            flash("Confirme a exclusão com a conta Google vinculada ao StudyHub.", "mensagem-erro")
            return redirect(url_for("pagina_configuracoes"))
        if not excluir_usuario(usuario_id):
            flash("Não foi possível excluir a conta.", "mensagem-erro")
            return redirect(url_for("pagina_configuracoes"))
        return _sair_de_conta_excluida()

    # 1. Procurar uma conta já vinculada ao Google
    usuario = buscar_por_google_id(google_id)

    if usuario:

        session.clear()
        session["usuario_id"] = usuario["id"]
        session["nome"] = usuario["nome"]

        return redirect(
            url_for("dashboard")
        )

    # 2. Procurar uma conta existente pelo e-mail
    usuario = buscar_por_email(email)

    if usuario:
        session["google_vinculo_email"] = email
        session["google_vinculo_id"] = google_id

        return redirect(
            url_for("vincular_google_conta")
        )

    # 3. Criar uma nova conta Google
    usuario_id = salvar_usuario_google(
        nome,
        email,
        google_id
    )

    session.clear()
    session["usuario_id"] = usuario_id
    session["nome"] = nome

    return redirect(
        url_for("dashboard")
    )


def vincular_google_conta():

    if request.method == "POST":

        email = session.get("google_vinculo_email")
        google_id = session.get("google_vinculo_id")

        if not email or not google_id:

            return redirect(
                url_for("pagina_login")
            )

        senha = request.form.get("senha", "")
        chave = _chave_limite_login(email)
        if not reservar_tentativa(chave):
            flash("Muitas tentativas de login. Tente novamente mais tarde.", "mensagem-erro")
            return render_template("vincular_google.html"), 429

        usuario = autenticar(
            email,
            senha
        )

        if not usuario:

            flash(
                "Senha incorreta.",
                "mensagem-erro"
            )

            return render_template(
                "vincular_google.html"
            )

        vincular_google(
            usuario["id"],
            google_id
        )

        limpar_tentativas(chave)
        session.clear()
        session["usuario_id"] = usuario["id"]
        session["nome"] = usuario["nome"]

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "vincular_google.html"
    )


def _chave_limite_login(email):
    # Mantém chaves existentes para endereços válidos e limita chaves de dados malformados.
    identificacao = email.strip().lower()
    if len(identificacao) > 254 or "\x00" in identificacao:
        identificacao = "invalido"
    return f'{identificacao}|{request.remote_addr or "desconhecido"}'


def pagina_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        chave = _chave_limite_login(email)

        if not reservar_tentativa(chave):
            flash("Muitas tentativas de login. Tente novamente mais tarde.", "mensagem-erro")
            return render_template("pagina_login.html"), 429

        usuario, mensagem = realizar_login(
            email,
            senha
        )

        if usuario:

            limpar_tentativas(chave)
            session.clear()

            session["usuario_id"] = usuario["id"]

            session["nome"] = usuario["nome"]

            return redirect(
                url_for("dashboard")
            )

        flash(
            mensagem,
            "mensagem-erro"
        )

    return render_template(
        "pagina_login.html"
    )


def confirmar_exclusao_google():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("pagina_login"))
    conta = obter_usuario_por_id(usuario_id)
    if not conta or not conta["google_id"] or conta["senha"] is not None:
        abort(403)
    estado = token_urlsafe(32)
    session["google_exclusao"] = {
        "estado": estado,
        "usuario_id": usuario_id,
        "expira_em": datetime.now(timezone.utc).timestamp() + 300,
    }
    return google.authorize_redirect(
        url_for("google_callback", _external=True), state=estado, prompt="select_account",
    )


def excluir_conta_configuracoes():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    senha_atual = request.form.get(
        "senha_atual",
        ""
    )

    sucesso, mensagem = excluir_conta_controller(
        session["usuario_id"],
        senha_atual
    )

    if not sucesso:

        flash(
            mensagem,
            "erro"
        )

        return redirect(
            url_for("pagina_configuracoes")
        )

    return _sair_de_conta_excluida()


def _sair_de_conta_excluida():
    session.clear()

    flash(
        "Sua conta foi excluída com sucesso.",
        "sucesso"
    )

    return redirect(
        url_for("pagina_login")
    )


def registrar_autenticacao(app):
    global google
    oauth.init_app(app)

    google = oauth.register(
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )

    app.add_url_rule("/logout", view_func=logout, methods=["POST"])
    app.add_url_rule("/login/google", view_func=login_google)
    app.add_url_rule("/login/google/callback", view_func=google_callback)
    app.add_url_rule("/login/google/vincular", view_func=vincular_google_conta, methods=["GET", "POST"])
    app.add_url_rule("/login", view_func=pagina_login, methods=["GET", "POST"])
    app.add_url_rule("/configuracoes/excluir-conta/google", view_func=confirmar_exclusao_google, methods=["POST"])
    app.add_url_rule("/configuracoes/excluir-conta", view_func=excluir_conta_configuracoes, methods=["POST"])
