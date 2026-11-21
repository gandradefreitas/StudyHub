from uuid import uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, session, url_for
from psycopg.types.json import Jsonb

from database.conexao import conectar
from database.redacoes_surpresa_repository import (
    avancar_surpresa, estado_atual, gravar_estado, obter_tentativa, preparar_tentativa,
)
from gemini_client import enviar_mensagem
from services.redacoes_surpresa_service import LIMITES, obter_tema_surpresa
from services.redacoes_service import (
    COMPETENCIAS, CRITERIOS_ITA, TEMAS, estimar_notas, estimar_notas_ita,
)

redacoes = Blueprint("redacoes", __name__, url_prefix="/redacoes")


def listar_envios(usuario_id):
    with conectar() as conexao:
        return conexao.execute("""
            SELECT id, tema, ano, criado_em, nota, instituicao, tempo_segundos FROM redacoes
            WHERE usuario_id = %s ORDER BY criado_em DESC, id DESC
        """, (usuario_id,)).fetchall()


@redacoes.before_request
def exigir_login():
    if not session.get("usuario_id"):
        return redirect(url_for("pagina_login"))


@redacoes.get("")
def listar():
    envios = listar_envios(session["usuario_id"])
    grupos = {}
    for instituicao, divisor in (("ENEM", 1), ("ITA", 10)):
        notas = [envio["nota"] for envio in envios
                 if envio["instituicao"] == instituicao and envio["nota"] is not None]
        grupos[instituicao] = {
            "media": sum(notas) / (len(notas) * divisor) if notas else None,
            "maximo": 1000 if instituicao == "ENEM" else 10,
            "temas": {chave: tema for chave, tema in TEMAS.items()
                      if tema.get("instituicao", "ENEM") == instituicao},
        }
    with conectar() as conexao:
        iniciadas = conexao.execute("""
            SELECT instituicao FROM redacoes_surpresa WHERE usuario_id = %s AND chave IS NOT NULL
        """, (session["usuario_id"],)).fetchall()
    return render_template("redacoes/lista.html", grupos=grupos, limites=LIMITES,
                           iniciadas={linha["instituicao"] for linha in iniciadas})


@redacoes.route("/tema/<tema_id>", methods=["GET", "POST"])
def escrever(tema_id):
    tema = TEMAS.get(tema_id)
    if tema is None:
        abort(404)
    instituicao = tema.get("instituicao", "ENEM")
    ita = instituicao == "ITA"
    texto = titulo = ""
    if request.method == "POST":
        texto = request.form.get("texto", "").strip()
        titulo = request.form.get("titulo", "").strip() if ita else ""
        if texto and len(texto) <= 6000 and (not ita or 0 < len(titulo) <= 200):
            with conectar() as conexao:
                envio = conexao.execute("""
                    INSERT INTO redacoes (usuario_id, tema, ano, texto, instituicao, titulo)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (session["usuario_id"], tema["titulo"], tema["ano"], texto, instituicao, titulo)).fetchone()
            return corrigir(envio["id"])
    return render_template("redacoes/escrever.html", tema=tema, texto=texto, titulo=titulo,
                           instituicao=instituicao, ita=ita,
                           invalido=request.method == "POST"), 422 if request.method == "POST" else 200


def obter_envio(envio_id):
    with conectar() as conexao:
        envio = conexao.execute("""
            SELECT tema, ano, texto, notas, nota, criado_em, instituicao, titulo, tempo_segundos FROM redacoes
            WHERE id = %s AND usuario_id = %s
        """, (envio_id, session["usuario_id"])).fetchone()
    if envio is None:
        abort(404)
    return envio


@redacoes.post("/resultado/<int:envio_id>/corrigir")
def corrigir(envio_id):
    envio = obter_envio(envio_id)
    if envio["nota"] is None:
        try:
            if envio["instituicao"] == "ITA":
                notas = estimar_notas_ita(enviar_mensagem, envio["tema"], envio["titulo"], envio["texto"])
            else:
                notas = estimar_notas(enviar_mensagem, envio["tema"], envio["texto"])
        except (RuntimeError, ValueError):
            current_app.logger.warning("Estimativa da redação %s indisponível.", envio_id)
        else:
            with conectar() as conexao:
                conexao.execute("""
                    UPDATE redacoes SET notas = %s, nota = %s
                    WHERE id = %s AND usuario_id = %s AND nota IS NULL
                """, (Jsonb(notas), sum(notas), envio_id, session["usuario_id"]))
    return redirect(url_for("redacoes.resultado", envio_id=envio_id), code=303)


@redacoes.get("/resultado/<int:envio_id>")
def resultado(envio_id):
    envio = obter_envio(envio_id)
    ita = envio["instituicao"] == "ITA"
    nomes = [nome for nome, _ in CRITERIOS_ITA] if ita else COMPETENCIAS
    divisor = 10 if ita else 1
    competencias = [(nome, nota / divisor) for nome, nota in zip(nomes, envio["notas"] or [])]
    return render_template("redacoes/resultado.html", envio=envio,
                           envio_id=envio_id, competencias=competencias,
                           maximo=10 if ita else 1000, nota_maxima=2 if ita else 200, divisor=divisor)


@redacoes.route("/surpresa/<instituicao>", methods=["GET", "POST"])
def surpresa(instituicao):
    limite = LIMITES.get(instituicao)
    if limite is None:
        abort(404)
    usuario_id = session["usuario_id"]
    if request.method == "GET":
        tentativa = preparar_tentativa(usuario_id, instituicao, limite, uuid4().hex)
    else:
        with conectar() as conexao:
            tentativa = obter_tentativa(conexao, usuario_id, instituicao)
            if not tentativa or tentativa["chave"] != request.form.get("chave"):
                return redirect(url_for("redacoes.surpresa", instituicao=instituicao), code=303)
            estado = estado_atual(tentativa, limite, "pausar",
                                  request.form.get("texto", "")[:6000].strip(),
                                  request.form.get("titulo", "")[:200].strip())
            estado["texto"] = estado["texto"].strip()
            estado["titulo"] = estado["titulo"].strip()
            tema = obter_tema_surpresa(instituicao, tentativa["rodada"])
            if not estado["texto"] or (instituicao == "ITA" and not estado["titulo"]):
                gravar_estado(conexao, usuario_id, instituicao, estado)
                tentativa.update(estado)
                return renderizar_surpresa(instituicao, tentativa, invalido=True), 422
            envio = conexao.execute("""
                INSERT INTO redacoes (usuario_id, tema, ano, texto, instituicao, titulo, tempo_segundos)
                VALUES (%s, %s, 0, %s, %s, %s, %s) RETURNING id
            """, (usuario_id, tema["titulo"], estado["texto"], instituicao,
                  estado["titulo"] if instituicao == "ITA" else "", int(estado["segundos"]))).fetchone()
            avancar_surpresa(conexao, usuario_id, instituicao)
        return corrigir(envio["id"])
    return renderizar_surpresa(instituicao, tentativa)


def renderizar_surpresa(instituicao, tentativa, invalido=False):
    tema = obter_tema_surpresa(instituicao, tentativa["rodada"])
    resposta = current_app.make_response(render_template(
        "redacoes/escrever.html", tema=tema, instituicao=instituicao,
        ita=instituicao == "ITA", texto=tentativa["texto"], titulo=tentativa["titulo"],
        invalido=invalido, surpresa=tentativa, limite=LIMITES[instituicao],
    ))
    resposta.cache_control.no_store = True
    return resposta


@redacoes.post("/surpresa/<instituicao>/nova")
def encerrar_surpresa(instituicao):
    limite = LIMITES.get(instituicao)
    if limite is None:
        abort(404)
    usuario_id = session["usuario_id"]
    with conectar() as conexao:
        tentativa = obter_tentativa(conexao, usuario_id, instituicao)
        if not tentativa or tentativa["chave"] != request.form.get("chave"):
            abort(409)
        if tentativa["segundos"] < limite:
            abort(409)
        avancar_surpresa(conexao, usuario_id, instituicao)
    return redirect(url_for("redacoes.surpresa", instituicao=instituicao), code=303)


@redacoes.post("/surpresa/<instituicao>/tempo")
def salvar_tempo_surpresa(instituicao):
    limite = LIMITES.get(instituicao)
    if limite is None:
        abort(404)
    usuario_id = session["usuario_id"]
    acao = request.form.get("acao")
    revisao = request.form.get("revisao", type=int)
    if acao not in {"ativo", "pausar"} or revisao is None or not 0 < revisao < 2**31:
        abort(400)
    with conectar() as conexao:
        tentativa = obter_tentativa(conexao, usuario_id, instituicao)
        if not tentativa or tentativa["chave"] != request.form.get("chave"):
            abort(409)
        if revisao <= tentativa["revisao"]:
            abort(409)
        estado = estado_atual(tentativa, limite, acao,
                              request.form.get("texto", "")[:6000],
                              request.form.get("titulo", "")[:200])
        gravar_estado(conexao, usuario_id, instituicao, estado)
        conexao.execute("""
            UPDATE redacoes_surpresa SET revisao = %s
            WHERE usuario_id = %s AND instituicao = %s
        """, (revisao, usuario_id, instituicao))
    return {"restante": limite - estado["segundos"],
            "texto": estado["texto"], "titulo": estado["titulo"]}
