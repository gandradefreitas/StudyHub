from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from studyhub.database.usuario_repository import obter_usuario_por_id
from studyhub.controllers.web.cadastro_controller import realizar_cadastro
from studyhub.controllers.web.login_controller import realizar_login


app = Flask(__name__)

app.secret_key = "studyhub-chave-desenvolvimento"


# ==========================
# PÁGINA INICIAL
# ==========================

@app.route("/")
def pagina_inicial():

    return render_template(
        "pagina_inicial.html"
    )



# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(session["usuario_id"])

    return render_template(
        "dashboard.html",
        usuario=usuario
    )


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Você saiu da sua conta.",
        "mensagem-sucesso"
    )

    return redirect(
        url_for("pagina_login")
    )


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def pagina_login():

    if request.method == "POST":

        email = request.form.get("email")

        senha = request.form.get("senha")


        usuario, mensagem = realizar_login(
            email,
            senha
        )


        if usuario:

            session["usuario_id"] = usuario[0]

            session["nome"] = usuario[1]

            flash(
                f"Bem-vindo, {usuario[1]}!",
                "mensagem-sucesso"
            )

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



# ==========================
# CADASTRO
# ==========================

@app.route("/cadastro", methods=["GET", "POST"])
def pagina_cadastro():

    if request.method == "POST":

        nome = request.form.get("nome")

        email = request.form.get("email")

        senha = request.form.get("senha")

        confirmar_senha = request.form.get("confirmar_senha")


        if senha != confirmar_senha:

            flash(
                "As senhas não coincidem.",
                "mensagem-erro"
            )

            return redirect(
                url_for("pagina_cadastro")
            )


        resultado, mensagem = realizar_cadastro(
            nome,
            email,
            senha
        )


        if resultado:

            flash (
                "Conta criada com sucesso! Faça login.",
                "mensagem-sucesso"
            )

            return redirect(
                url_for("pagina_login")
            )

        flash(
            mensagem,
            "mensagem-erro"
        )


    return render_template(
        "pagina_cadastro.html"
    )



if __name__ == "__main__":

    app.run(debug=True)