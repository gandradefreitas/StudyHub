from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def pagina_inicial():
    return render_template("pagina_inicial.html")


@app.route("/login")
def pagina_login():
    return render_template("pagina_login.html")


@app.route("/cadastro")
def pagina_cadastro():
    return render_template("pagina_cadastro.html")


if __name__ == "__main__":
    app.run(debug=True)