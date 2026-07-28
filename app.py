from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def pagina_inicial():
    return render_template("pagina_inicial.html")


@app.route("/login", methods=["GET", "POST"])
def pagina_login():

    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        print(email)
        print(senha)

    return render_template("pagina_login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def pagina_cadastro():

    if request.method == "POST":

        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        print(nome)
        print(email)
        print(senha)
        print(confirmar_senha)

    return render_template("pagina_cadastro.html")


if __name__ == "__main__":
    app.run(debug=True)