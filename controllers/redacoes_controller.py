from datetime import datetime, timezone
from uuid import UUID, uuid4

from flask import Blueprint, abort, current_app, redirect, render_template, request, session, url_for
from flask_wtf.csrf import generate_csrf

from database.conexao import conectar
from database.redacoes_surpresa_repository import (
    avancar_surpresa, estado_atual, gravar_estado, obter_tentativa, preparar_tentativa,
)
from database.fila_redacoes_repository import (
    obter_envio_repetido, reagendar_redacao, registrar_envio,
)
from services.redacoes_surpresa_service import LIMITES, obter_tema_surpresa
from services.redacoes_service import (
    COMPETENCIAS, CRITERIOS_ITA, TEMAS,
)

redacoes = Blueprint("redacoes", __name__, url_prefix="/redacoes")


def listar_envios(usuario_id):
    with conectar() as conexao:
        return conexao.execute("""
            SELECT id, tema, ano, criado_em, nota, instituicao, tempo_segundos, correcao_falhou FROM redacoes
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
    chave_envio = uuid4()
    if request.method == "POST":
        try:
            chave_envio = UUID(request.form.get("chave_envio", ""))
        except ValueError:
            abort(400)
        texto = request.form.get("texto", "").strip()
        titulo = request.form.get("titulo", "").strip() if ita else ""
        if texto and len(texto) <= 6000 and (not ita or 0 < len(titulo) <= 200):
            with conectar() as conexao:
                envio_id = registrar_envio(
                    conexao, session["usuario_id"], tema["titulo"], tema["ano"],
                    texto, instituicao, titulo, chave_envio=chave_envio,
                )
            return redirect(url_for("redacoes.resultado", envio_id=envio_id), code=303)
    return render_template("redacoes/escrever.html", tema=tema, texto=texto, titulo=titulo,
                           instituicao=instituicao, ita=ita, chave_envio=chave_envio,
                           invalido=request.method == "POST"), 422 if request.method == "POST" else 200


def obter_envio(envio_id):
    with conectar() as conexao:
        envio = conexao.execute("""
            SELECT tema, ano, texto, notas, nota, criado_em, instituicao, titulo, tempo_segundos,
                   correcao_falhou, correcao_tentar_apos, correcao_reivindicada_ate
            FROM redacoes
            WHERE id = %s AND usuario_id = %s
        """, (envio_id, session["usuario_id"])).fetchone()
    if envio is None:
        abort(404)
    return envio


@redacoes.post("/resultado/<int:envio_id>/corrigir")
def corrigir(envio_id):
    obter_envio(envio_id)
    reagendar_redacao(envio_id, session["usuario_id"])
    return redirect(url_for("redacoes.resultado", envio_id=envio_id), code=303)


@redacoes.get("/resultado/<int:envio_id>")
def resultado(envio_id):
    envio = obter_envio(envio_id)
    ita = envio["instituicao"] == "ITA"
    nomes = [nome for nome, _ in CRITERIOS_ITA] if ita else COMPETENCIAS
    divisor = 10 if ita else 1
    competencias = [(nome, nota / divisor) for nome, nota in zip(nomes, envio["notas"] or [])]
    agora = datetime.now(timezone.utc)
    reserva = envio["correcao_reivindicada_ate"]
    estado = "pendente"
    if envio["correcao_falhou"]:
        estado = "falhou"
    elif reserva and reserva > agora:
        estado = "processando"
    elif envio["correcao_tentar_apos"] and envio["correcao_tentar_apos"] > agora:
        estado = "reagendada"
    return render_template("redacoes/resultado.html", envio=envio,
                           envio_id=envio_id, competencias=competencias, estado=estado,
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
        try:
            chave_envio = UUID(request.form.get("chave", ""))
        except ValueError:
            abort(400)
        with conectar() as conexao:
            tentativa = obter_tentativa(conexao, usuario_id, instituicao)
            repetido = obter_envio_repetido(conexao, usuario_id, chave_envio)
            if repetido:
                return redirect(url_for("redacoes.resultado", envio_id=repetido["id"]), code=303)
            if not tentativa or tentativa["chave"] != chave_envio.hex:
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
            envio_id = registrar_envio(
                conexao, usuario_id, tema["titulo"], 0, estado["texto"], instituicao,
                estado["titulo"] if instituicao == "ITA" else "", chave_envio=chave_envio,
                tempo_segundos=int(estado["segundos"]),
            )
            avancar_surpresa(conexao, usuario_id, instituicao)
        return redirect(url_for("redacoes.resultado", envio_id=envio_id), code=303)
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


@redacoes.route("/surpresa/<instituicao>/tempo", methods=["GET", "POST"])
def salvar_tempo_surpresa(instituicao):
    limite = LIMITES.get(instituicao)
    if limite is None:
        abort(404)
    if request.method == "GET":
        return {"csrf_token": generate_csrf()}, 200, {"Cache-Control": "no-store"}
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
            "texto": estado["texto"], "titulo": estado["titulo"],
            "csrf_token": generate_csrf()}
