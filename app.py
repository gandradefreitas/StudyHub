from flask import Flask,render_template,request,redirect,url_for,session,flash
from studyhub.controllers.estudo_controller import iniciar_estudo_controller, finalizar_estudo_controller, \
    obter_estudo_ativo_controller, obter_horas_estudadas_controller
from studyhub.controllers.web.tarefa_controller import  editar_tarefa_controller, excluir_tarefa_controller
from studyhub.database.usuario_repository import obter_usuario_por_id
from studyhub.database.tarefa_repository import listar_tarefas, buscar_tarefa
from studyhub.controllers.web.tarefa_controller import adicionar_tarefa_controller, concluir_tarefa_controller
from studyhub.services.dashboard_service import carregar_dashboard
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

    dados = carregar_dashboard(
        session["usuario_id"]
    )

    horas_estudadas = obter_horas_estudadas_controller(
        session["usuario_id"]
    )

    return render_template(
        "dashboard.html",
        **dados,
        horas_estudadas=horas_estudadas,
        classe_body="sidebar-toggle",
        mostrar_pesquisa=True,
        mostrar_perfil=True
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

    return redirect(url_for("pagina_login"))

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


@app.route("/tarefas")
def pagina_tarefas():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    tarefas = listar_tarefas(
        session["usuario_id"]
    )

    return render_template(
        "tarefas.html",
        usuario=usuario,
        tarefas=tarefas,
        classe_body="sidebar-toggle"
    )

@app.route("/tarefas/nova", methods=["GET", "POST"])
def nova_tarefa():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    if request.method == "POST":

        descricao = request.form.get("descricao")

        resultado, mensagem = adicionar_tarefa_controller(
            session["usuario_id"],
            descricao
        )

        flash(
            mensagem,
            "mensagem-sucesso" if resultado else "mensagem-erro"
        )

        if resultado:
            return redirect(url_for("pagina_tarefas"))

    return render_template(
        "nova_tarefa.html",
        usuario=usuario,
        mostrar_pesquisa = False,
        mostrar_perfil = False,
        classe_body="sidebar-toggle"
    )

@app.route("/tarefas/<int:id_tarefa>/concluir", methods=["POST"])
def concluir_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    resultado, mensagem = concluir_tarefa_controller(
        session["usuario_id"],
        id_tarefa
    )

    flash(
        mensagem,
        "mensagem-sucesso" if resultado else "mensagem-erro"
    )

    return redirect(url_for("pagina_tarefas"))

@app.route("/tarefas/<int:id_tarefa>/editar", methods=["GET", "POST"])
def editar_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(session["usuario_id"])

    if request.method == "POST":

        nova_descricao = request.form.get("descricao")

        resultado, mensagem = editar_tarefa_controller(
            session["usuario_id"],
            id_tarefa,
            nova_descricao
        )

        flash(
            mensagem,
            "mensagem-sucesso" if resultado else "mensagem-erro"
        )

        return redirect(url_for("pagina_tarefas"))

    tarefa = buscar_tarefa(
        id_tarefa,
        session["usuario_id"]
    )

    return render_template(
        "editar_tarefa.html",
        usuario=usuario,
        tarefa=tarefa,
        classe_body="sidebar-toggle"
    )

@app.route("/tarefas/<int:id_tarefa>/excluir", methods=["GET", "POST"])
def excluir_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    resultado, mensagem = excluir_tarefa_controller(
        session["usuario_id"],
        id_tarefa
    )

    flash(
        mensagem,
        "mensagem-sucesso" if resultado else "mensagem-erro"
    )

    return redirect(url_for("pagina_tarefas"))

@app.route("/estudos")
def pagina_estudos():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    estudo_ativo = obter_estudo_ativo_controller(session["usuario_id"])

    return render_template(
        "estudos.html",
        estudo_ativo=estudo_ativo,
        classe_body="sidebar-toggle",
        usuario=usuario,

    )

@app.route("/estudos/iniciar", methods=["POST"])
def iniciar_estudo():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    sucesso, mensagem = iniciar_estudo_controller(
        session["usuario_id"]
    )

    flash(mensagem)

    return redirect(url_for("pagina_estudos"))

@app.route("/estudos/finalizar", methods=["POST"])
def finalizar_estudo():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    sucesso, mensagem = finalizar_estudo_controller(
        session["usuario_id"]
    )

    flash(mensagem)

    return redirect(url_for("pagina_estudos"))
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

            return redirect(url_for("pagina_cadastro"))


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

            return redirect(url_for("pagina_login"))

        flash(
            mensagem,
            "mensagem-erro"
        )


    return render_template(
        "pagina_cadastro.html"
    )



if __name__ == "__main__":

    app.run(debug=True)