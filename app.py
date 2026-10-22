import re

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, \
    send_from_directory, abort

import io

import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)

import os

from flask_wtf.csrf import CSRFProtect

from authlib.integrations.flask_client import OAuth

from security.limite_login import (
    verificar_bloqueio,
    registrar_tentativa_falha,
    limpar_tentativas
)

from controllers.web.configuracoes_controller import (
    carregar_configuracoes,
    atualizar_conta,
    alterar_senha,
    atualizar_metas_configuracoes,
    atualizar_tema,
    excluir_conta as excluir_conta_controller
)

from controllers.estudo_controller import (
    iniciar_estudo_controller,
    finalizar_estudo_controller,
    obter_estudo_ativo_controller, finalizar_estudo_automatico_controller, registrar_atividade_estudo_controller,
    iniciar_estudo_automatico_controller
)

from controllers.web.tarefa_controller import (
    adicionar_tarefa_controller,
    concluir_tarefa_controller,
    editar_tarefa_controller,
    excluir_tarefa_controller
)

from controllers.web.cadastro_controller import realizar_cadastro
from controllers.web.login_controller import realizar_login
from controllers.resultados_controller import obter_historico
from controllers.dados_controller import (
    obter_dados_exportacao,
    limpar_historico
)

from database.usuario_repository import (
    obter_usuario_por_id,
    buscar_por_email,
    buscar_por_google_id,
    salvar_usuario_google,
    vincular_google
)
from database.tarefa_repository import (
    listar_tarefas,
    buscar_tarefa,
    obter_tarefas_por_data,
    obter_tarefas_por_mes
)

from database.estudos_repository import (
    obter_estudos_por_data,
    obter_total_segundos,
    obter_estudos_por_periodo,
    obter_estudos_por_mes
)

from database.resultados_repository import (
    obter_resultados_por_data,
    obter_provas_por_periodo,
    obter_segundos_provas,
    obter_resumo_usuario,
    listar_resultados_usuario,
    obter_resultados_por_mes,
    salvar_resultado,
    salvar_respostas_prova,
    obter_desempenho_por_area,
    converter_tempo_para_segundos, obter_respostas_por_resultado, obter_resultado_por_id
)

from database.anotacao_repository import (
    obter_anotacao_por_data,
    salvar_anotacao,
    obter_anotacoes_por_mes
)

from database.questoes_repository import (
    obter_ultima_resposta_questao,
    registrar_resposta_questao,
    obter_ordem_questoes, calcular_intervalo_revisao, obter_numero_tentativa, obter_questoes_para_revisao,
    obter_questoes_filtradas, obter_areas_questoes, obter_dificuldades_questoes, obter_competencias_questoes,
    obter_habilidades_questoes, obter_linguas_questoes, obter_desempenho_questoes_por_area, obter_desempenho_questoes
)

from database.criar_banco import criar_tabelas
from services.autenticacao import autenticar
from services.configuracoes import definir_senha_usuario
from services.dashboard_service import carregar_dashboard
from services.provas_service import (
    obter_prova,
    listar_provas,
    obter_catalogo_por_id
)

from datetime import datetime, date, timedelta, timezone

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY não configurada.")

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

csrf = CSRFProtect(app)

criar_tabelas()


@app.context_processor
def contexto_usuario():

    if "usuario_id" not in session:
        return {}

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    return {
        "usuario": usuario
    }

@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(
        app.static_folder,
        "robots.txt",
        mimetype="text/plain"
    )

@app.route("/sitemap.xml")
def sitemap_xml():
    paginas = [
        url_for("pagina_inicial", _external=True),
        url_for("pagina_login", _external=True),
        url_for("pagina_cadastro", _external=True)
    ]

    urls = "\n".join(
        f"    <url>\n"
        f"        <loc>{url}</loc>\n"
        f"    </url>"
        for url in paginas
    )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""

    return sitemap, 200, {"Content-Type": "application/xml"}
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
        return redirect(
            url_for("pagina_login")
        )

    dados = carregar_dashboard(
        session["usuario_id"]
    )

    return render_template(
        "dashboard.html",
        **dados,
        classe_body="sidebar-toggle",
        mostrar_pesquisa=True,
        mostrar_perfil=True
    )


# ==========================
# LOGOUT
# ==========================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash(
        "Você saiu da sua conta.",
        "mensagem-erro"
    )

    return redirect(
        url_for("pagina_login")
    )

# ==========================
# LOGIN
# ==========================

@app.route("/login/google")
def login_google():
    redirect_uri = url_for("google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/login/google/callback")
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

    # 1. Procurar uma conta já vinculada ao Google
    usuario = buscar_por_google_id(google_id)

    if usuario:

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

    session["usuario_id"] = usuario_id
    session["nome"] = nome

    return redirect(
        url_for("dashboard")
    )

@app.route("/login/google/vincular", methods=["GET", "POST"])
def vincular_google_conta():

    if request.method == "POST":

        email = session.get("google_vinculo_email")
        google_id = session.get("google_vinculo_id")

        if not email or not google_id:

            return redirect(
                url_for("pagina_login")
            )

        senha = request.form.get("senha")

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

        session.pop(
            "google_vinculo_email",
            None
        )

        session.pop(
            "google_vinculo_id",
            None
        )

        session["usuario_id"] = usuario["id"]
        session["nome"] = usuario["nome"]

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "vincular_google.html"
    )

@app.route("/login", methods=["GET", "POST"])
def pagina_login():

    if request.method == "POST":

        email = request.form.get("email")
        senha = request.form.get("senha")

        ip = request.remote_addr or "desconhecido"

        chave = f"{email.lower().strip()}|{ip}"

        if verificar_bloqueio(chave):

            flash(
                "Muitas tentativas de login. "
                "Tente novamente mais tarde.",
                "mensagem-erro"
            )

            return render_template(
                "pagina_login.html"
            )

        usuario, mensagem = realizar_login(
            email,
            senha
        )

        if usuario:

            limpar_tentativas(chave)

            session["usuario_id"] = usuario["id"]

            session["nome"] = usuario["nome"]

            return redirect(
                url_for("dashboard")
            )

        registrar_tentativa_falha(chave)

        flash(
            mensagem,
            "mensagem-erro"
        )

    return render_template(
        "pagina_login.html"
    )

# ==========================
# TAREFAS
# ==========================

@app.route("/tarefas")
def pagina_tarefas():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

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
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    if request.method == "POST":

        descricao = request.form.get(
            "descricao"
        )

        resultado, mensagem = adicionar_tarefa_controller(
            session["usuario_id"],
            descricao
        )

        if resultado:

            return redirect(
                url_for("pagina_tarefas")
            )

    return render_template(
        "nova_tarefa.html",
        usuario=usuario,
        mostrar_pesquisa=False,
        mostrar_perfil=False,
        classe_body="sidebar-toggle"
    )


@app.route(
    "/tarefas/<int:id_tarefa>/concluir",
    methods=["POST"]
)
def concluir_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    resultado, mensagem = concluir_tarefa_controller(
        session["usuario_id"],
        id_tarefa
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_tarefas")
    )


@app.route(
    "/tarefas/<int:id_tarefa>/editar",
    methods=["GET", "POST"]
)
def editar_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    if request.method == "POST":

        nova_descricao = request.form.get(
            "descricao"
        )

        resultado, mensagem = editar_tarefa_controller(
            session["usuario_id"],
            id_tarefa,
            nova_descricao
        )

        flash(
            mensagem,
            "mensagem-sucesso"
            if resultado
            else "mensagem-erro"
        )

        return redirect(
            url_for("pagina_tarefas")
        )

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


@app.route(
    "/tarefas/<int:id_tarefa>/excluir",
    methods=["POST"]
)
def excluir_tarefa(id_tarefa):

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    resultado, mensagem = excluir_tarefa_controller(
        session["usuario_id"],
        id_tarefa
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_tarefas")
    )


# ==========================
# ESTUDOS
# ==========================

@app.route("/estudos")
def pagina_estudos():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    estudo_ativo = obter_estudo_ativo_controller(
        session["usuario_id"]
    )

    return render_template(
        "estudos.html",
        estudo_ativo=estudo_ativo,
        classe_body="sidebar-toggle",
        usuario=usuario
    )


@app.route(
    "/estudos/iniciar-ajax",
    methods=["POST"]
)
def iniciar_estudo_ajax():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    sucesso, mensagem = iniciar_estudo_controller(
        usuario_id
    )

    if not sucesso:

        return jsonify({
            "sucesso": False,
            "erro": mensagem
        }), 400

    estudo = obter_estudo_ativo_controller(
        usuario_id
    )

    return jsonify({
        "sucesso": True,
        "inicio": estudo["inicio"]
    })


@app.route(
    "/estudos/finalizar-ajax",
    methods=["POST"]
)
def finalizar_estudo_ajax():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    sucesso, mensagem = finalizar_estudo_controller(
        usuario_id
    )

    if not sucesso:

        return jsonify({
            "sucesso": False,
            "erro": mensagem
        }), 400

    return jsonify({
        "sucesso": True,
        "mensagem": mensagem
    })


@app.route(
    "/estudos/finalizar-automatico",
    methods=["POST"]
)
def finalizar_estudo_automatico():

    if "usuario_id" not in session:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    sucesso, mensagem = finalizar_estudo_controller(
        session["usuario_id"]
    )

    return jsonify({
        "sucesso": sucesso,
        "mensagem": mensagem
    })

# ==========================
# CRONÔMETRO AUTOMÁTICO
# ==========================

@app.route("/questoes/estudo/iniciar", methods=["POST"])
def iniciar_estudo_automatico():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    try:
        sucesso, mensagem, estudo = (
            iniciar_estudo_automatico_controller(usuario_id)
        )

        if not sucesso:
            return jsonify({
                "sucesso": False,
                "erro": mensagem
            }), 400

        # Reconcilia o estado da sessão com o limite de inatividade.
        estado = registrar_atividade_estudo_controller(
            usuario_id,
            "heartbeat"
        )

        if estado is None:
            return jsonify({
                "sucesso": False,
                "erro": "Não foi possível recuperar a sessão."
            }), 409

        return jsonify({
            "sucesso": True,
            "mensagem": mensagem,
            "duracao": estado["duracao"],
            "pausado": estado["pausado"]
        })

    except Exception:
        app.logger.exception(
            "Erro ao iniciar ou recuperar sessão automática de estudo."
        )

        return jsonify({
            "sucesso": False,
            "erro": "Não foi possível iniciar o cronômetro."
        }), 500


@app.route("/questoes/estudo/atividade", methods=["POST"])
def registrar_atividade_estudo():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    dados = request.get_json(silent=True) or {}
    tipo_evento = dados.get("tipo_evento")

    if tipo_evento not in ("atividade", "heartbeat"):
        return jsonify({
            "sucesso": False,
            "erro": "Tipo de evento inválido."
        }), 400

    try:
        estudo = registrar_atividade_estudo_controller(
            usuario_id,
            tipo_evento
        )

        if estudo is None:
            return jsonify({
                "sucesso": False,
                "erro": "Nenhuma sessão de estudo ativa encontrada."
            }), 404

        return jsonify({
            "sucesso": True,
            "duracao": estudo["duracao"],
            "pausado": estudo["pausado"]
        })

    except Exception:
        app.logger.exception(
            "Erro ao registrar atividade da sessão de estudo."
        )

        return jsonify({
            "sucesso": False,
            "erro": "Não foi possível atualizar o cronômetro."
        }), 500

@app.route("/questoes/estudo/finalizar", methods=["POST"])
def finalizar_sessao_questoes():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "erro": "Usuário não autenticado."
        }), 401

    try:
        sucesso, mensagem = (
            finalizar_estudo_automatico_controller(usuario_id)
        )

        if not sucesso:
            return jsonify({
                "sucesso": False,
                "erro": mensagem
            }), 400

        return jsonify({
            "sucesso": True,
            "mensagem": mensagem
        })

    except Exception:
        app.logger.exception(
            "Erro ao finalizar sessão automática de estudo."
        )

        return jsonify({
            "sucesso": False,
            "erro": "Não foi possível finalizar a sessão."
        }), 500

# ==========================
# PROVAS
# ==========================

@app.route("/provas")
def pagina_provas():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    provas = listar_provas()

    return render_template(
        "provas/provas.html",
        usuario=usuario,
        provas=provas,
        classe_body="sidebar-toggle"
    )


@app.route("/provas/<int:id_prova>")
def visualizar_prova(id_prova):

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    prova = obter_prova(id_prova)


    if prova is None:
        return redirect(
            url_for("pagina_provas")
        )


    # Registra o início da prova no servidor
    session["prova_inicio"] = {
        "prova_id": prova.id,
        "inicio": datetime.now(
            timezone.utc
        ).isoformat()
    }


    return render_template(
        "provas/prova.html",
        prova=prova,
        questao_atual=prova.questoes[0]
    )



@app.route(
    "/provas/resultado",
    methods=["GET", "POST"]
)
def resultado_prova():

    if request.method == "POST":

        # Usuário precisa estar autenticado
        usuario_id = session.get("usuario_id")

        if not usuario_id:

            return jsonify({
                "erro": "Usuário não autenticado."
            }), 401

        dados = request.get_json()

        if not isinstance(dados, dict):
            return jsonify({
                "erro": "Nenhum dado válido foi recebido."
            }), 400


        # ------------------------------------------------
        # VALIDAÇÃO DOS DADOS RECEBIDOS
        # ------------------------------------------------

        prova_id = dados.get("prova_id")
        respostas = dados.get("respostas")


        if prova_id is None:

            return jsonify({
                "erro": "Prova não informada."
            }), 400


        if not isinstance(respostas, dict):

            return jsonify({
                "erro": "Formato de respostas inválido."
            }), 400


        try:

            prova_id = int(prova_id)

        except (TypeError, ValueError):

            return jsonify({
                "erro": "Prova inválida."
            }), 400


        # ------------------------------------------------
        # CARREGA A PROVA OFICIAL
        # ------------------------------------------------

        prova = obter_prova(prova_id)

        if prova is None:
            return jsonify({
                "erro": "Prova não encontrada."
            }), 404

        # ------------------------------------------------
        # IDENTIFICA E VALIDA AS QUESTÕES REALIZADAS
        # ------------------------------------------------

        questoes_recebidas = dados.get("questoes")

        if not isinstance(questoes_recebidas, list) or not questoes_recebidas:
            return jsonify({
                "erro": "Questões da prova não foram informadas."
            }), 400

        numeros_questoes = set()

        for questao in questoes_recebidas:

            if not isinstance(questao, dict):
                return jsonify({
                    "erro": "Formato de questão inválido."
                }), 400

            try:
                numero = int(questao["numero"])

            except (KeyError, TypeError, ValueError):
                return jsonify({
                    "erro": "Número de questão inválido."
                }), 400

            numeros_questoes.add(numero)

        # ------------------------------------------------
        # FILTRA AS QUESTÕES OFICIAIS DA PROVA
        # ------------------------------------------------

        lingua_escolhida = dados.get("lingua")

        if prova.tipo == "ENEM" and prova.dia == "Primeiro Dia":

            # ENEM: considera o idioma escolhido pelo participante.
            questoes_realizadas = [
                questao
                for questao in prova.questoes
                if questao.numero in numeros_questoes
                   and (
                           not questao.lingua
                           or questao.lingua == lingua_escolhida
                   )
            ]

        else:

            # Outras provas, como o ITA:
            # considera todas as questões oficiais recebidas,
            # inclusive aquelas que possuem um campo "lingua".
            questoes_realizadas = [
                questao
                for questao in prova.questoes
                if questao.numero in numeros_questoes
            ]

        if len(questoes_realizadas) != len(numeros_questoes):
            return jsonify({
                "erro": "A lista de questões não corresponde à prova oficial."
            }), 400

        # ------------------------------------------------
        # CALCULA O RESULTADO
        # ------------------------------------------------

        acertos = 0
        erros = 0
        nao_respondidas = 0

        # Armazena somente as respostas das questões erradas.
        # O enunciado e o gabarito serão recuperados no GET.

        respostas_erradas = {}

        for questao in questoes_realizadas:

            resposta_usuario = respostas.get(
                str(questao.numero)
            )

            if resposta_usuario is None or resposta_usuario == "":
                nao_respondidas += 1
                continue

            # ------------------------------------------------
            # VALIDA A ALTERNATIVA
            # ------------------------------------------------

            try:

                resposta_usuario = int(
                    resposta_usuario
                )

            except (
                    TypeError,
                    ValueError
            ):

                erros += 1

                continue

            # Verifica se a alternativa existe na questão
            if not (
                    0 <= resposta_usuario < len(questao.alternativas)
            ):

                return jsonify({
                    "erro": "Alternativa inválida."
                }), 400

            # ------------------------------------------------
            # COMPARA COM O GABARITO OFICIAL
            # ------------------------------------------------

            if resposta_usuario == questao.resposta:

                acertos += 1

            else:

                erros += 1

                # Guarda somente os dados necessários
                # para reconstruir a revisão posteriormente.

                respostas_erradas[
                    str(questao.numero)
                ] = resposta_usuario


        # ------------------------------------------------
        # TOTAL DE QUESTÕES
        # ------------------------------------------------

        total = len(questoes_realizadas)


        # ------------------------------------------------
        # PORCENTAGEM
        # ------------------------------------------------

        porcentagem = round(
            (acertos / total) * 100,
            2
        ) if total > 0 else 0

        # ------------------------------------------------
        # CALCULA O TEMPO NO SERVIDOR
        # ------------------------------------------------

        prova_inicio = session.get(
            "prova_inicio"
        )


        if (
            not prova_inicio
            or prova_inicio.get("prova_id") != prova_id
        ):

            return jsonify({
                "erro": "Início da prova não encontrado."
            }), 400


        try:

            inicio = datetime.fromisoformat(
                prova_inicio["inicio"]
            )

        except (
            TypeError,
            ValueError
        ):

            session.pop(
                "prova_inicio",
                None
            )

            return jsonify({
                "erro": "Horário de início da prova inválido."
            }), 400


        fim = datetime.now(
            timezone.utc
        )


        duracao = fim - inicio


        segundos = max(
            0,
            int(duracao.total_seconds())
        )


        horas = segundos // 3600

        minutos = (
            segundos % 3600
        ) // 60

        segundos_restantes = (
            segundos % 60
        )


        tempo_gasto = (
            f"{horas:02d}:"
            f"{minutos:02d}:"
            f"{segundos_restantes:02d}"
        )



        # ------------------------------------------------
        # SALVA O RESULTADO
        # ------------------------------------------------

        resultado = {

            "usuario_id":
                usuario_id,

            "prova_id":
                prova_id,

            "acertos":
                acertos,

            "erros":
                erros,

            "nao_respondidas":
                nao_respondidas,

            "total":
                total,

            "tempo_gasto":
                tempo_gasto,

            "porcentagem":
                porcentagem
        }

        # ------------------------------------------------
        # SALVA O RESULTADO
        # ------------------------------------------------

        resultado_id = salvar_resultado(
            resultado
        )

        # ------------------------------------------------
        # SALVA AS RESPOSTAS DA TENTATIVA
        # ------------------------------------------------

        salvar_respostas_prova(

            usuario_id=usuario_id,

            prova_id=prova_id,

            resultado_id=resultado_id,

            questoes=questoes_realizadas,

            respostas=respostas

        )

        session.pop(
            "prova_inicio",
            None
        )

        # ------------------------------------------------
        # RESULTADO DA SESSÃO
        # ------------------------------------------------

        session["resultado_prova"] = {

            "numeros_questoes": [
                questao.numero
                for questao in questoes_realizadas
            ],

            "prova_id":
                prova_id,

            "lingua":
                lingua_escolhida,

            "acertos":
                acertos,

            "erros":
                erros,

            "nao_respondidas":
                nao_respondidas,

            "total":
                total,

            "porcentagem":
                porcentagem,

            "tempo_gasto":
                tempo_gasto,

            "respostas_erradas":
                respostas_erradas

        }


        return jsonify({
            "status": "ok"
        })

    # ----------------------------------------------------
    # PÁGINA DE RESULTADO
    # ----------------------------------------------------

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    # ----------------------------------------------------
    # RECUPERA O RESULTADO DA PROVA
    # ----------------------------------------------------

    resultado = session.get(
        "resultado_prova"
    )

    if resultado is None:
        resultado = {

            "prova_id": None,

            "acertos": 0,

            "erros": 0,

            "questoes_erradas": [],

            "nao_respondidas": 0,

            "total": 0,

            "porcentagem": 0,

            "tempo_gasto": "00:00:00"

        }

    # ----------------------------------------------------
    # RECONSTRÓI AS QUESTÕES ERRADAS
    # ----------------------------------------------------

    questoes_erradas = []

    if resultado["prova_id"] is not None:

        # Recupera a prova oficial
        prova = obter_prova(
            resultado["prova_id"]
        )

        if prova is not None:

            # Recupera o idioma utilizado na prova
            lingua_escolhida = resultado.get(
                "lingua"
            )

            # Recupera as respostas erradas
            respostas_erradas = resultado.get(
                "respostas_erradas",
                {}
            )

            numeros_questoes = set(
                resultado.get("numeros_questoes", [])
            )


            # Reconstrói as questões realizadas conforme o tipo de prova.
            if prova.tipo == "ENEM" and prova.dia == "Primeiro Dia":

                questoes_realizadas = [
                    questao
                    for questao in prova.questoes
                    if (
                            questao.numero in numeros_questoes
                            and (
                                    not questao.lingua
                                    or questao.lingua == lingua_escolhida
                            )
                    )
                ]

            else:

                questoes_realizadas = [
                    questao
                    for questao in prova.questoes
                    if questao.numero in numeros_questoes
                ]

            # Monta a revisão
            for questao in questoes_realizadas:

                numero = str(
                    questao.numero
                )

                # Ignora questões que não foram erradas
                if numero not in respostas_erradas:
                    continue

                questoes_erradas.append({

                    "numero": questao.numero,

                    "enunciado": questao.enunciado,

                    "imagem": questao.imagem,

                    "pergunta": questao.pergunta,

                    "alternativas": [
                        preparar_alternativa_revisao(alternativa)
                        for alternativa in questao.alternativas
                    ],

                    "respostaUsuario": respostas_erradas[numero],

                    "respostaCorreta": questao.resposta,

                    "comentario": questao.comentario

                })

    # ----------------------------------------------------
    # ADICIONA AS QUESTÕES ERRADAS AO RESULTADO
    # ----------------------------------------------------

    resultado["questoes_erradas"] = questoes_erradas

    # ----------------------------------------------------
    # RENDERIZA A PÁGINA
    # ----------------------------------------------------

    return render_template(
        "provas/resultado.html",
        resultado=resultado,
        prova=prova if resultado["prova_id"] is not None else None,
        titulo="Resultado",
        classe_body="sidebar-toggle"
    )

def preparar_alternativa_revisao(alternativa):
    """
    Prepara uma alternativa para exibição na revisão da prova.
    Reconhece URLs diretas e links Markdown que representam imagens.
    """

    alternativa = str(alternativa).strip()

    # Remove aspas externas, se existirem.
    alternativa = alternativa.strip('"').strip("'").strip()

    # Caso seja um link Markdown: [texto](URL)
    if alternativa.startswith("[") and "](" in alternativa:

        inicio_url = alternativa.rfind("](")

        url = alternativa[inicio_url + 2:]

        # Remove o parêntese final do Markdown.
        if url.endswith(")"):
            url = url[:-1]

        url = url.strip()

        if url.startswith(("https://", "http://")):
            return {
                "tipo": "imagem",
                "conteudo": url
            }

    # Caso seja uma URL direta.
    if alternativa.startswith(("https://", "http://")):
        return {
            "tipo": "imagem",
            "conteudo": alternativa
        }

    # Caso seja texto comum.
    return {
        "tipo": "texto",
        "conteudo": alternativa
    }


@app.route("/provas/historico")
def historico_provas():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        session["usuario_id"]
    )

    historico = obter_historico(
        session["usuario_id"]
    )

    return render_template(
        "provas/historico.html",
        historico=historico,
        usuario=usuario,
        titulo="Histórico de Provas",
        classe_body="sidebar-toggle"
    )

@app.route(
    "/provas/historico/<int:resultado_id>"
)
def visualizar_resultado_historico(resultado_id):

    # ------------------------------------------------
    # AUTENTICAÇÃO
    # ------------------------------------------------

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return redirect(
            url_for("pagina_login")
        )

    # ------------------------------------------------
    # RECUPERA O RESULTADO
    # ------------------------------------------------

    resultado_db = obter_resultado_por_id(
        resultado_id,
        usuario_id
    )

    if resultado_db is None:

        abort(404)

    # ------------------------------------------------
    # RECUPERA AS RESPOSTAS DA TENTATIVA
    # ------------------------------------------------

    respostas_db = obter_respostas_por_resultado(
        resultado_id,
        usuario_id
    )

    respostas_usuario = {
        str(resposta["questao_numero"]): resposta["resposta"]
        for resposta in respostas_db
    }

    # ------------------------------------------------
    # RECUPERA A PROVA OFICIAL
    # ------------------------------------------------

    prova = obter_prova(
        resultado_db["prova_id"]
    )

    if prova is None:

        abort(404)

    # ------------------------------------------------
    # RECONSTRÓI AS QUESTÕES ERRADAS
    # ------------------------------------------------

    questoes_erradas = []

    for questao in prova.questoes:

        numero = str(questao.numero)

        # Ignora questões que não foram respondidas.
        if numero not in respostas_usuario:
            continue

        resposta_usuario = respostas_usuario[numero]

        # Ignora questões respondidas corretamente.
        if resposta_usuario == questao.resposta:
            continue

        questoes_erradas.append({
            "numero": questao.numero,

            "enunciado": questao.enunciado,

            "imagem": questao.imagem,

            "pergunta": questao.pergunta,

            "alternativas": [
                preparar_alternativa_revisao(alternativa)
                for alternativa in questao.alternativas
            ],

            "respostaUsuario": resposta_usuario,

            "respostaCorreta": questao.resposta,

            "comentario": questao.comentario
        })

    # ------------------------------------------------
    # MONTA O RESULTADO PARA O TEMPLATE
    # ------------------------------------------------

    resultado = {

        "prova_id":
            resultado_db["prova_id"],

        "acertos":
            resultado_db["acertos"],

        "erros":
            resultado_db["erros"],

        "nao_respondidas":
            resultado_db["nao_respondidas"],

        "total":
            resultado_db["total"],

        "tempo_gasto":
            resultado_db["tempo_gasto"],

        "porcentagem":
            resultado_db["porcentagem"],

        "questoes_erradas":
            questoes_erradas

    }

    # ------------------------------------------------
    # RENDERIZA O RESULTADO
    # ------------------------------------------------

    return render_template(
        "provas/resultado.html",
        resultado=resultado,
        prova=prova,
        titulo="Resultado da Prova",
        classe_body="sidebar-toggle"
    )


# ==========================
# CALENDÁRIO
# ==========================

@app.route("/calendario")
def pagina_calendario():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    return render_template(
        "/calendario.html"
    )

@app.route("/calendario/estudos")
def calendario_estudos():

    usuario_id = session.get(
        "usuario_id"
    )

    data = request.args.get(
        "data"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400

    if not isinstance(data, str):
        return jsonify({
            "erro": "Data inválida."
        }), 400

    try:
        date.fromisoformat(data)
    except ValueError:
        return jsonify({
            "erro": "Data inválida."
        }), 400

    estudos = obter_estudos_por_data(
        usuario_id,
        data
    )

    resultado = []

    for estudo in estudos:

        resultado.append({
            "inicio": estudo["inicio"],
            "fim": estudo["fim"],
            "duracao": estudo["duracao"]
        })

    return jsonify(resultado)


@app.route("/calendario/tarefas")
def calendario_tarefas():

    usuario_id = session.get(
        "usuario_id"
    )

    data = request.args.get(
        "data"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400

    if not isinstance(data, str):
        return jsonify({
            "erro": "Data inválida."
        }), 400

    try:
        date.fromisoformat(data)
    except ValueError:
        return jsonify({
            "erro": "Data inválida."
        }), 400

    tarefas = obter_tarefas_por_data(
        usuario_id,
        data
    )

    resultado = []

    for tarefa in tarefas:

        resultado.append({
            "id": tarefa["id"],
            "descricao": tarefa["descricao"],
            "data_conclusao": tarefa["data_conclusao"]
        })

    return jsonify(resultado)


@app.route("/calendario/provas")
def calendario_provas():

    usuario_id = session.get(
        "usuario_id"
    )

    data = request.args.get(
        "data"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400

    if not isinstance(data, str):
        return jsonify({
            "erro": "Data inválida."
        }), 400

    try:
        date.fromisoformat(data)
    except ValueError:
        return jsonify({
            "erro": "Data inválida."
        }), 400

    resultados = obter_resultados_por_data(
        usuario_id,
        data
    )

    resultado = []

    for resultado_prova in resultados:

        id_prova = int(
            resultado_prova["prova_id"]
        )

        catalogo = obter_catalogo_por_id(
            id_prova
        )

        if catalogo is None:
            continue

        resultado.append({

            "id":
                id_prova,

            "nome":
                catalogo["nome"],

            "dia":
                catalogo["dia"],

            "acertos":
                resultado_prova["acertos"],

            "erros":
                resultado_prova["erros"],

            "nao_respondidas":
                resultado_prova["nao_respondidas"],

            "total":
                resultado_prova["total"],

            "tempo_gasto":
                resultado_prova["tempo_gasto"],

            "porcentagem":
                resultado_prova["porcentagem"],

            "data":
                resultado_prova["data_realizacao"]
        })

    return jsonify(resultado)


@app.route("/calendario/anotacao")
def calendario_anotacao():

    usuario_id = session.get(
        "usuario_id"
    )

    data = request.args.get(
        "data"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400

    if not isinstance(data, str):
        return jsonify({
            "erro": "Data inválida."
        }), 400

    try:
        date.fromisoformat(data)
    except ValueError:
        return jsonify({
            "erro": "Data inválida."
        }), 400

    anotacao = obter_anotacao_por_data(
        usuario_id,
        data
    )

    if anotacao is None:

        return jsonify({
            "existe": False,
            "texto": ""
        })

    return jsonify({

        "existe": True,

        "id":
            anotacao["id"],

        "data":
            anotacao["data"],

        "texto":
            anotacao["texto"]
    })


@app.route(
    "/calendario/anotacao",
    methods=["POST"]
)
def salvar_calendario_anotacao():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    dados = request.get_json()

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    data = dados.get(
        "data"
    )

    texto = dados.get(
        "texto",
        ""
    )

    if not isinstance(texto, str):
        return jsonify({
            "erro": "Texto da anotação inválido."
        }), 400

    texto = texto.strip()

    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400

    if not isinstance(data, str):
        return jsonify({
            "erro": "Data inválida."
        }), 400

    try:

        date.fromisoformat(data)

    except ValueError:

        return jsonify({
            "erro": "Data inválida."
        }), 400



    if not texto:

        return jsonify({
            "erro": "A anotação não pode estar vazia."
        }), 400

    if len(texto) > 5000:
        return jsonify({
            "erro": "A anotação é muito longa."
        }), 400

    salvar_anotacao(
        usuario_id,
        data,
        texto
    )

    return jsonify({
        "sucesso": True,
        "mensagem": "Anotação salva com sucesso."
    })



@app.route("/calendario/indicadores")
def indicadores_calendario():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    mes = request.args.get(
        "mes",
        type=int
    )

    ano = request.args.get(
        "ano",
        type=int
    )

    if mes is None or ano is None:
        return jsonify({
            "erro": "Mês e ano são obrigatórios."
        }), 400

    if mes < 1 or mes > 12:
        return jsonify({
            "erro": "Mês inválido."
        }), 400

    if ano < 2000 or ano > 2100:
        return jsonify({
            "erro": "Ano inválido."
        }), 400

    indicadores = {}

    estudos = obter_estudos_por_mes(
        usuario_id,
        ano,
        mes
    )

    for estudo in estudos:

        data = estudo["data"]

        if hasattr(data, "isoformat"):
            data = data.isoformat()

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["estudo"] = True

    tarefas = obter_tarefas_por_mes(
        usuario_id,
        ano,
        mes
    )

    for tarefa in tarefas:

        data = tarefa["data"]

        if hasattr(data, "isoformat"):
            data = data.isoformat()

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["tarefa"] = True

    provas = obter_resultados_por_mes(
        usuario_id,
        ano,
        mes
    )

    for prova in provas:

        data = prova["data"]

        if hasattr(data, "isoformat"):
            data = data.isoformat()

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["prova"] = True

    anotacoes = obter_anotacoes_por_mes(
        usuario_id,
        ano,
        mes
    )

    for anotacao in anotacoes:

        data = anotacao["data"]

        if hasattr(data, "isoformat"):
            data = data.isoformat()

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["anotacao"] = True

    return jsonify(indicadores)


# ==========================
# ESTATÍSTICAS
# ==========================

@app.route("/estatisticas")
def pagina_estatisticas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:
        return redirect(
            url_for("pagina_login")
        )

    return render_template(
        "estatisticas/estatisticas.html"
    )


@app.route("/estatisticas/resumo")
def estatisticas_resumo():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    resultado = obter_resumo_usuario(
        usuario_id
    )

    segundos_estudo = obter_total_segundos(
        usuario_id
    )

    segundos_provas = obter_segundos_provas(
        usuario_id
    )

    total_segundos = (
        segundos_estudo
        + segundos_provas
    )

    provas = resultado["provas"]
    questoes = resultado["questoes"]
    acertos = resultado["acertos"]
    erros = resultado["erros"]
    nao_respondidas = resultado["nao_respondidas"]

    respondidas = (
        acertos + erros
    )

    if respondidas > 0:

        porcentagem = (
            acertos / respondidas
        ) * 100

    else:

        porcentagem = 0

    return jsonify({

        "horas_estudadas":
            total_segundos,

        "provas":
            provas,

        "questoes":
            questoes,

        "respondidas":
            respondidas,

        "acertos":
            acertos,

        "erros":
            erros,

        "nao_respondidas":
            nao_respondidas,

        "porcentagem":
            round(
                porcentagem,
                1
            )
    })


@app.route("/estatisticas/evolucao")
def estatisticas_evolucao():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    hoje = date.today()

    ano = request.args.get(
        "ano",
        default=hoje.year,
        type=int
    )

    mes = request.args.get(
        "mes",
        default=hoje.month,
        type=int
    )

    if mes < 1 or mes > 12:

        return jsonify({
            "erro": "Mês inválido."
        }), 400

    inicio = date(
        ano,
        mes,
        1
    )

    if mes == 12:

        proximo_mes = date(
            ano + 1,
            1,
            1
        )

    else:

        proximo_mes = date(
            ano,
            mes + 1,
            1
        )

    fim = (
        proximo_mes
        - timedelta(days=1)
    )

    estudos = obter_estudos_por_periodo(
        usuario_id,
        inicio.isoformat(),
        fim.isoformat()
    )

    estudos_por_data = {}

    for estudo in estudos:

        data = estudo["data"]

        if isinstance(data, date):

            data = data.isoformat()

        estudos_por_data[data] = (
            estudo["duracao"]
        )

    provas = obter_provas_por_periodo(
        usuario_id,
        inicio.isoformat(),
        fim.isoformat()
    )

    provas_por_data = {}

    for prova in provas:

        data = prova["data"]

        if isinstance(data, date):

            data = data.isoformat()

        segundos = converter_tempo_para_segundos(
            prova["tempo_gasto"]
        )

        provas_por_data[data] = (
            provas_por_data.get(data, 0)
            + segundos
        )

    resultado = []

    data_atual = inicio

    while data_atual <= fim:

        data_formatada = (
            data_atual.isoformat()
        )

        duracao_estudos = (
            estudos_por_data.get(
                data_formatada,
                0
            )
        )

        duracao_provas = (
            provas_por_data.get(
                data_formatada,
                0
            )
        )

        duracao_total = (
            duracao_estudos
            + duracao_provas
        )

        resultado.append({

            "data":
                data_formatada,

            "duracao":
                duracao_total
        })

        data_atual += timedelta(
            days=1
        )

    return jsonify(resultado)


@app.route("/estatisticas/provas")
def estatisticas_provas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    resultados = listar_resultados_usuario(
        usuario_id
    )

    provas = []

    for resultado in resultados:

        id_prova = int(
            resultado["prova_id"]
        )

        catalogo = obter_catalogo_por_id(
            id_prova
        )

        if catalogo is None:
            continue

        provas.append({

            "id":
                id_prova,

            "nome":
                catalogo["nome"],

            "dia":
                catalogo["dia"],

            "acertos":
                resultado["acertos"],

            "erros":
                resultado["erros"],

            "nao_respondidas":
                resultado["nao_respondidas"],

            "total":
                resultado["total"],

            "tempo_gasto":
                resultado["tempo_gasto"],

            "porcentagem":
                resultado["porcentagem"],

            "data":
                resultado["data_realizacao"]
        })

    return jsonify(provas)


@app.route("/estatisticas/areas")
def estatisticas_areas():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    desempenho = obter_desempenho_por_area(
        usuario_id
    )

    return jsonify(desempenho)


@app.route("/estatisticas/questoes-areas")
def estatisticas_questoes_areas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    desempenho = obter_desempenho_questoes_por_area(
        usuario_id
    )

    return jsonify(desempenho)


@app.route("/estatisticas/questoes-detalhadas")
def estatisticas_questoes_detalhadas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    criterio = request.args.get("criterio", "dificuldade")

    criterios_permitidos = {
        "dificuldade",
        "competencia",
        "habilidade",
        "lingua"
    }

    if criterio not in criterios_permitidos:

        return jsonify({
            "erro": "Critério de análise inválido."
        }), 400

    desempenho = obter_desempenho_questoes(
        usuario_id,
        criterio
    )

    return jsonify(desempenho)




# ==========================
# CONFIGURAÇÕES
# ==========================

@app.route("/configuracoes")
def pagina_configuracoes():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    dados = carregar_configuracoes(
        session["usuario_id"]
    )

    return render_template(
        "configuracoes/configuracoes.html",
        **dados,
        classe_body="sidebar-toggle",
        mostrar_pesquisa=False,
        mostrar_perfil=False
    )


@app.route(
    "/configuracoes/conta",
    methods=["POST"]
)
def atualizar_conta_configuracoes():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    nome = request.form.get(
        "nome"
    )

    email = request.form.get(
        "email"
    )

    resultado, mensagem = atualizar_conta(
        session["usuario_id"],
        nome,
        email
    )

    if resultado:

        session["nome"] = nome

        flash(
            mensagem,
            "mensagem-sucesso"
        )

    else:

        flash(
            mensagem,
            "mensagem-erro"
        )

    return redirect(
        url_for("pagina_configuracoes")
    )


@app.route(
    "/configuracoes/senha",
    methods=["POST"]
)
def alterar_senha_configuracoes():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    senha_atual = request.form.get(
        "senha_atual"
    )

    nova_senha = request.form.get(
        "nova_senha"
    )

    confirmar_senha = request.form.get(
        "confirmar_senha"
    )

    resultado, mensagem = alterar_senha(
        session["usuario_id"],
        senha_atual,
        nova_senha,
        confirmar_senha
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_configuracoes")
    )

@app.route(
    "/configuracoes/definir-senha",
    methods=["POST"]
)
def definir_senha_configuracoes():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    nova_senha = request.form.get("nova_senha")
    confirmar_senha = request.form.get("confirmar_senha")

    sucesso, mensagem = definir_senha_usuario(
        session["usuario_id"],
        nova_senha,
        confirmar_senha
    )

    if sucesso:
        flash(
            mensagem,
            "mensagem-sucesso"
        )
    else:
        flash(
            mensagem,
            "mensagem-erro"
        )

    return redirect(
        url_for("pagina_configuracoes")
    )

@app.route(
    "/configuracoes/aparencia",
    methods=["POST"]
)
def atualizar_aparencia_configuracoes():

    if "usuario_id" not in session:

        return redirect(
            url_for("pagina_login")
        )

    tema = request.form.get(
        "tema"
    )

    resultado, mensagem = atualizar_tema(
        session["usuario_id"],
        tema
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_configuracoes")
    )


@app.route(
    "/configuracoes/metas",
    methods=["POST"]
)
def atualizar_metas_configuracoes_rota():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    meta_estudo_horas = request.form.get(
        "meta_estudo_horas"
    )

    meta_estudo_minutos = request.form.get(
        "meta_estudo_minutos"
    )

    meta_questoes = request.form.get(
        "meta_questoes"
    )

    try:

        horas = int(
            meta_estudo_horas or 0
        )

        minutos = int(
            meta_estudo_minutos or 0
        )

    except ValueError:

        flash(
            "Informe valores válidos para a meta de estudo.",
            "mensagem-erro"
        )

        return redirect(
            url_for("pagina_configuracoes")
        )

    if horas < 0:
        flash(
            "As horas não podem ser negativas.",
            "mensagem-erro"
        )

        return redirect(
            url_for("pagina_configuracoes")
        )

    if minutos < 0 or minutos > 59:

        flash(
            "Os minutos devem estar entre 0 e 59.",
            "mensagem-erro"
        )

        return redirect(
            url_for("pagina_configuracoes")
        )

    meta_estudo = (
        horas * 60
    ) + minutos

    resultado, mensagem = atualizar_metas_configuracoes(
        session["usuario_id"],
        meta_estudo,
        meta_questoes
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_configuracoes")
    )


@app.route(
    "/configuracoes/dados/exportar",
    methods=["GET"]
)
def exportar_dados():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    dados = obter_dados_exportacao(
        session["usuario_id"]
    )

    arquivo = json.dumps(
        dados,
        ensure_ascii=False,
        indent=4,
        default=str
    )

    return Response(
        arquivo,
        mimetype="application/json",
        headers={
            "Content-Disposition":
                "attachment; filename=studyhub_dados.json"
        }
    )

@app.route(
    "/configuracoes/dados/exportar/pdf",
    methods=["GET"]
)
def exportar_dados_pdf():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    dados = obter_dados_exportacao(
        session["usuario_id"]
    )

    if not isinstance(dados, dict):
        return "Não foi possível gerar o relatório.", 500

    memoria = io.BytesIO()

    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.7 * cm,
        bottomMargin=2 * cm,
        title="Relatório de dados - StudyHub",
        author="StudyHub"
    )

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloStudyHub",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=5
        )
    )

    estilos.add(
        ParagraphStyle(
            name="SubtituloStudyHub",
            parent=estilos["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=18
        )
    )

    estilos.add(
        ParagraphStyle(
            name="SecaoStudyHub",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TextoStudyHub",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155"),
            wordWrap="LTR"
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TextoPequenoStudyHub",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#334155"),
            wordWrap="LTR"
        )
    )

    estilos.add(
        ParagraphStyle(
            name="CabecalhoTabelaStudyHub",
            parent=estilos["TextoPequenoStudyHub"],
            fontName="Helvetica-Bold",
            textColor=colors.white
        )
    )

    estilos.add(
        ParagraphStyle(
            name="IndicadorValorStudyHub",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=4
        )
    )

    estilos.add(
        ParagraphStyle(
            name="IndicadorRotuloStudyHub",
            parent=estilos["Normal"],
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B")
        )
    )

    elementos = []

    # --------------------------------------------------
    # FUNÇÕES AUXILIARES
    # --------------------------------------------------

    def formatar_texto(valor):

        if valor is None or valor == "":
            return "—"

        if isinstance(valor, bool):
            return "Sim" if valor else "Não"

        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M")

        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor)

        # Evita que caracteres especiais sejam interpretados
        # como tags HTML pelo ReportLab.
        from xml.sax.saxutils import escape

        return escape(texto)

    def formatar_data(valor, incluir_hora=False):

        if valor is None:
            return "—"

        if isinstance(valor, datetime):
            formato = (
                "%d/%m/%Y %H:%M"
                if incluir_hora
                else "%d/%m/%Y"
            )

            return valor.strftime(formato)

        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor)

        try:
            data = datetime.fromisoformat(texto)

            formato = (
                "%d/%m/%Y %H:%M"
                if incluir_hora
                else "%d/%m/%Y"
            )

            return data.strftime(formato)

        except (ValueError, TypeError):
            return texto

    def formatar_duracao(valor):

        if valor is None:
            return "—"

        if isinstance(valor, str):

            partes = valor.split(":")

            try:
                if len(partes) == 3:
                    horas, minutos, segundos = map(int, partes)

                    total_segundos = (
                        horas * 3600
                        + minutos * 60
                        + segundos
                    )

                elif len(partes) == 2:
                    minutos, segundos = map(int, partes)

                    total_segundos = (
                        minutos * 60
                        + segundos
                    )

                else:
                    total_segundos = int(valor)

            except ValueError:
                return valor

        else:
            try:
                total_segundos = int(valor)
            except (ValueError, TypeError):
                return str(valor)

        horas, resto = divmod(total_segundos, 3600)
        minutos, segundos = divmod(resto, 60)

        partes_formatadas = []

        if horas:
            partes_formatadas.append(f"{horas}h")

        if minutos:
            partes_formatadas.append(f"{minutos}min")

        if segundos and not horas:
            partes_formatadas.append(f"{segundos}s")

        return " ".join(partes_formatadas) or "0min"

    def adicionar_secao(titulo):

        elementos.append(
            Paragraph(
                titulo,
                estilos["SecaoStudyHub"]
            )
        )

    def adicionar_tabela(cabecalho, linhas, larguras):

        if not linhas:
            return

        dados_tabela = [
            [
                Paragraph(
                    formatar_texto(coluna),
                    estilos["CabecalhoTabelaStudyHub"]
                )
                for coluna in cabecalho
            ]
        ]

        for linha in linhas:

            dados_tabela.append([
                Paragraph(
                    formatar_texto(valor),
                    estilos["TextoPequenoStudyHub"]
                )
                for valor in linha
            ])

        tabela = Table(
            dados_tabela,
            colWidths=larguras,
            repeatRows=1,
            hAlign="LEFT"
        )

        tabela.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1E40AF")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC")
                    ]
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        elementos.append(tabela)
        elementos.append(Spacer(1, 0.25 * cm))

    def adicionar_indicadores(indicadores):

        celulas = []

        for valor, rotulo in indicadores:
            valor_formatado = Paragraph(
                formatar_texto(valor),
                estilos["IndicadorValorStudyHub"]
            )

            rotulo_formatado = Paragraph(
                formatar_texto(rotulo),
                estilos["IndicadorRotuloStudyHub"]
            )

            celulas.append([
                valor_formatado,
                rotulo_formatado
            ])

        if not celulas:
            return

        largura_disponivel = A4[0] - 3.4 * cm
        largura_celula = largura_disponivel / len(celulas)

        tabela = Table(
            [celulas],
            colWidths=[largura_celula] * len(celulas),
            hAlign="LEFT"
        )

        tabela.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F1F5F9")
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                )
            ])
        )

        elementos.append(tabela)
        elementos.append(Spacer(1, 0.35 * cm))

    # --------------------------------------------------
    # DADOS DO USUÁRIO
    # --------------------------------------------------

    usuario = dados.get("usuario")
    configuracoes = dados.get("configuracoes")

    if usuario:
        nome = usuario["nome"]
        email = usuario["email"]
    else:
        nome = "Usuário"
        email = None

    if configuracoes:
        tema = configuracoes["tema"]
        meta_estudo = configuracoes["meta_estudo"]
        meta_questoes = configuracoes["meta_questoes"]
    else:
        tema = "sistema"
        meta_estudo = 60
        meta_questoes = 20

    estudos = dados.get("estudos") or []
    tarefas = dados.get("tarefas") or []
    anotacoes = dados.get("anotacoes") or []
    resultados_provas = dados.get("resultados_provas") or []

    # --------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------

    elementos.append(
        Paragraph(
            "StudyHub",
            estilos["TituloStudyHub"]
        )
    )

    elementos.append(
        Paragraph(
            "Relatório de desempenho acadêmico",
            estilos["SubtituloStudyHub"]
        )
    )

    elementos.append(
        Paragraph(
            f"Exportado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            estilos["TextoStudyHub"]
        )
    )

    elementos.append(Spacer(1, 0.3 * cm))

    adicionar_secao("Identificação")

    adicionar_tabela(
        ["Informação", "Valor"],
        [
            ["Nome", nome],
            ["E-mail", email],
            [
                "Meta diária de estudo",
                f"{meta_estudo} minutos"
            ],
            [
                "Meta diária de questões",
                f"{meta_questoes} questões"
            ]
        ],
        [5 * cm, 10 * cm]
    )

    # --------------------------------------------------
    # RESUMO DO DESEMPENHO
    # --------------------------------------------------

    adicionar_secao("Resumo do desempenho")

    usuario_id = session["usuario_id"]

    resumo = obter_resumo_usuario(usuario_id)

    segundos_estudo = obter_total_segundos(usuario_id)
    segundos_provas = obter_segundos_provas(usuario_id)

    tempo_total = segundos_estudo + segundos_provas

    total_questoes = (
            resumo["acertos"]
            + resumo["erros"]
    )

    total_provas = resumo["provas"]

    if total_questoes > 0:
        taxa_acerto = (
                              resumo["acertos"] / total_questoes
                      ) * 100
    else:
        taxa_acerto = 0

    adicionar_indicadores([
        (
            total_questoes,
            "Questões resolvidas"
        ),
        (
            total_provas,
            "Provas realizadas"
        ),
        (
            f"{taxa_acerto:.1f}%".replace(".", ","),
            "Taxa de acerto"
        ),
        (
            formatar_duracao(tempo_total),
            "Tempo total"
        )
    ])

    # --------------------------------------------------
    # DESEMPENHO EM QUESTÕES
    # --------------------------------------------------

    adicionar_secao("Desempenho em questões")

    acertos = resumo["acertos"]
    erros = resumo["erros"]
    questoes_respondidas = acertos + erros

    if questoes_respondidas > 0:
        aproveitamento = (
                                 acertos / questoes_respondidas
                         ) * 100
    else:
        aproveitamento = 0

    adicionar_indicadores([
        (
            questoes_respondidas,
            "Questões resolvidas"
        ),
        (
            acertos,
            "Acertos"
        ),
        (
            erros,
            "Erros"
        ),
        (
            f"{aproveitamento:.1f}%".replace(".", ","),
            "Aproveitamento"
        )
    ])

    # --------------------------------------------------
    # DESEMPENHO POR ÁREA — PROVAS
    # --------------------------------------------------

    adicionar_secao("Desempenho por área")

    desempenho_areas = obter_desempenho_por_area(usuario_id)

    if desempenho_areas:

        linhas = []

        for area, resultado in sorted(
                desempenho_areas.items(),
                key=lambda item: item[1]["porcentagem"],
                reverse=True
        ):
            linhas.append([
                area,
                resultado["questoes"],
                resultado["acertos"],
                resultado["erros"],
                f'{resultado["porcentagem"]:.1f}%'.replace(".", ",")
            ])

        adicionar_tabela(
            [
                "Área do conhecimento",
                "Questões",
                "Acertos",
                "Erros",
                "Aproveitamento"
            ],
            linhas,
            [
                5.0 * cm,
                2.0 * cm,
                2.0 * cm,
                2.0 * cm,
                3.0 * cm
            ]
        )

    else:

        elementos.append(
            Paragraph(
                "Ainda não há respostas de provas suficientes "
                "para apresentar o desempenho por área.",
                estilos["TextoStudyHub"]
            )
        )

        elementos.append(Spacer(1, 0.25 * cm))

    # --------------------------------------------------
    # DESEMPENHO NAS QUESTÕES PRATICADAS
    # --------------------------------------------------

    adicionar_secao("Desempenho nas questões")

    desempenho_questoes = obter_desempenho_questoes_por_area(
        usuario_id
    )

    if desempenho_questoes:

        linhas = []

        for area, resultado in sorted(
                desempenho_questoes.items(),
                key=lambda item: item[1]["porcentagem"],
                reverse=True
        ):
            linhas.append([
                area,
                resultado["questoes"],
                resultado["acertos"],
                resultado["erros"],
                f'{resultado["porcentagem"]:.1f}%'.replace(".", ",")
            ])

        adicionar_tabela(
            [
                "Área do conhecimento",
                "Questões",
                "Acertos",
                "Erros",
                "Aproveitamento"
            ],
            linhas,
            [
                5.0 * cm,
                2.0 * cm,
                2.0 * cm,
                2.0 * cm,
                3.0 * cm
            ]
        )

    else:

        elementos.append(
            Paragraph(
                "Ainda não há questões praticadas suficientes "
                "para apresentar esta análise.",
                estilos["TextoStudyHub"]
            )
        )

        elementos.append(Spacer(1, 0.25 * cm))

    # --------------------------------------------------
    # ANÁLISE DETALHADA DAS QUESTÕES
    # --------------------------------------------------

    adicionar_secao("Análise detalhada das questões")

    criterios = [
        ("dificuldade", "Desempenho por dificuldade"),
        ("competencia", "Desempenho por competência"),
        ("habilidade", "Desempenho por habilidade"),
        ("lingua", "Desempenho por idioma")
    ]

    for criterio, titulo in criterios:

        desempenho = obter_desempenho_questoes(
            usuario_id,
            criterio
        )

        if not desempenho:
            continue

        adicionar_secao(titulo)

        linhas = []

        for categoria, resultado in sorted(
                desempenho.items(),
                key=lambda item: item[1]["porcentagem"],
                reverse=True
        ):
            linhas.append([
                categoria,
                resultado["questoes"],
                resultado["acertos"],
                resultado["erros"],
                f'{resultado["porcentagem"]:.1f}%'.replace(".", ",")
            ])

        adicionar_tabela(
            [
                "Categoria",
                "Questões",
                "Acertos",
                "Erros",
                "Aproveitamento"
            ],
            linhas,
            [
                5.0 * cm,
                2.0 * cm,
                2.0 * cm,
                2.0 * cm,
                3.0 * cm
            ]
        )

    # --------------------------------------------------
    # ANÁLISE DO DESEMPENHO
    # --------------------------------------------------

    adicionar_secao("Análise do desempenho")

    if desempenho_areas:

        areas_ordenadas = sorted(
            desempenho_areas.items(),
            key=lambda item: item[1]["porcentagem"],
            reverse=True
        )

        melhor_area, melhor_resultado = areas_ordenadas[0]
        pior_area, pior_resultado = areas_ordenadas[-1]

        adicionar_tabela(
            ["Indicador", "Resultado"],
            [
                [
                    "Maior aproveitamento em provas",
                    (
                        f'{melhor_area} — '
                        f'{melhor_resultado["porcentagem"]:.1f}%'
                    ).replace(".", ",")
                ],
                [
                    "Menor aproveitamento em provas",
                    (
                        f'{pior_area} — '
                        f'{pior_resultado["porcentagem"]:.1f}%'
                    ).replace(".", ",")
                ]
            ],
            [
                7.5 * cm,
                7.5 * cm
            ]
        )

    else:

        elementos.append(
            Paragraph(
                "Ainda não existem dados suficientes para "
                "identificar os pontos fortes e os pontos "
                "que precisam de atenção nas provas.",
                estilos["TextoStudyHub"]
            )
        )

        elementos.append(Spacer(1, 0.25 * cm))

    # --------------------------------------------------
    # RESULTADOS DAS PROVAS
    # --------------------------------------------------

    if resultados_provas:

        adicionar_secao("Resultados das provas")

        linhas = []

        nomes_provas = {
            1: "ENEM 2025 — Dia 1",
            2: "ENEM 2025 — Dia 2"
        }

        for resultado in resultados_provas:
            prova_id = resultado["prova_id"]
            acertos = resultado["acertos"]
            erros = resultado["erros"]
            nao_respondidas = resultado["nao_respondidas"]
            total = resultado["total"]
            tempo_gasto = resultado["tempo_gasto"]
            porcentagem = resultado["porcentagem"]
            data_realizacao = resultado["data_realizacao"]

            nome_prova = nomes_provas.get(
                prova_id,
                f"Prova {prova_id}"
            )

            linhas.append([
                nome_prova,
                f"{acertos}/{total}",
                erros,
                nao_respondidas,
                f"{float(porcentagem):.2f}%".replace(".", ","),
                formatar_duracao(tempo_gasto),
                formatar_data(
                    data_realizacao,
                    incluir_hora=True
                )
            ])

        adicionar_tabela(
            [
                "Prova",
                "Acertos",
                "Erros",
                "Em branco",
                "Aproveitamento",
                "Duração",
                "Realização"
            ],
            linhas,
            [
                3.0 * cm,
                1.5 * cm,
                1.2 * cm,
                1.5 * cm,
                2.0 * cm,
                1.5 * cm,
                3.3 * cm
            ]
        )

    # --------------------------------------------------
    # RODAPÉ
    # --------------------------------------------------

    def adicionar_rodape(canvas, doc):

        canvas.saveState()

        largura, altura = A4

        canvas.setStrokeColor(
            colors.HexColor("#CBD5E1")
        )

        canvas.line(
            1.7 * cm,
            1.5 * cm,
            largura - 1.7 * cm,
            1.5 * cm
        )

        canvas.setFont("Helvetica", 8)

        canvas.setFillColor(
            colors.HexColor("#64748B")
        )

        canvas.drawString(
            1.7 * cm,
            1 * cm,
            "StudyHub | Relatório pessoal"
        )

        canvas.drawRightString(
            largura - 1.7 * cm,
            1 * cm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    documento.build(
        elementos,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )

    memoria.seek(0)

    return Response(
        memoria.getvalue(),
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                'attachment; filename="studyhub_relatorio.pdf"',
            "Cache-Control": "no-store"
        }
    )


@app.route(
    "/configuracoes/dados/limpar",
    methods=["POST"]
)
def limpar_historico_rota():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    resultado, mensagem = limpar_historico(
        session["usuario_id"]
    )

    flash(
        mensagem,
        "mensagem-sucesso"
        if resultado
        else "mensagem-erro"
    )

    return redirect(
        url_for("pagina_configuracoes")
    )


@app.route(
    "/configuracoes/excluir-conta",
    methods=["POST"]
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

    session.clear()

    flash(
        "Sua conta foi excluída com sucesso.",
        "sucesso"
    )

    return redirect(
        url_for("pagina_login")
    )


# ==========================
# QUESTÕES
# ==========================

@app.route("/questoes")
def questoes_inicio():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return redirect(
            url_for("pagina_login")
        )

    ordem_questoes = obter_ordem_questoes(
        usuario_id
    )

    if not ordem_questoes:

        flash(
            "Nenhuma questão está disponível no momento.",
            "info"
        )

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for(
            "questoes",
            numero=ordem_questoes[0]
        )
    )

@app.route("/questoes/<int:numero>")
def questoes(numero):

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        usuario_id
    )

    estudo_ativo = obter_estudo_ativo_controller(
        usuario_id
    )

    modo_revisao = request.args.get(
        "revisao"
    ) == "1"

    area = request.args.get("area")

    dificuldade = request.args.get("dificuldade")

    competencia = request.args.get("competencia")

    habilidade = request.args.get("habilidade")

    lingua = request.args.get("lingua")

    questoes = obter_questoes_filtradas(
        area=area,
        dificuldade=dificuldade,
        competencia=competencia,
        habilidade=habilidade,
        lingua=lingua
    )

    areas_questoes = obter_areas_questoes()

    dificuldades_questoes = obter_dificuldades_questoes()

    competencias_questoes = obter_competencias_questoes()

    habilidades_questoes = obter_habilidades_questoes()

    linguas_questoes = obter_linguas_questoes()

    # =====================================================
    # OBTER ORDEM DAS QUESTÕES
    # =====================================================

    ordem_questoes = obter_ordem_questoes(
        usuario_id
    )

    if modo_revisao:

        questoes_revisao = obter_questoes_para_revisao(
            usuario_id
        )

        if area or dificuldade or competencia or habilidade or lingua:
            questoes_filtradas = obter_questoes_filtradas(
                area=area,
                dificuldade=dificuldade,
                competencia=competencia,
                habilidade=habilidade,
                lingua=lingua
            )

            numeros_filtrados = {
                questao["numero"]
                for questao in questoes_filtradas
            }

            questoes_revisao = [
                resposta
                for resposta in questoes_revisao
                if resposta["questao_numero"] in numeros_filtrados
            ]

        ordem_questoes = [
            resposta["questao_numero"]
            for resposta in questoes_revisao
        ]
    elif area or dificuldade or competencia or habilidade or lingua:

        numeros_filtrados = {
            questao["numero"]
            for questao in questoes
        }

        ordem_questoes = [
            numero
            for numero in ordem_questoes
            if numero in numeros_filtrados
        ]

    # =====================================================
    # VERIFICAR SE EXISTEM QUESTÕES DISPONÍVEIS
    # =====================================================

    if not ordem_questoes:

        return render_template(
            "questoes.html",

            usuario=usuario,

            questao=None,

            tem_anterior=False,

            tem_proxima=False,

            numero_anterior=None,

            numero_proxima=None,

            questao_bloqueada=False,

            ultima_resposta=None,

            proxima_tentativa=None,

            estudo_ativo=estudo_ativo,

            modo_revisao=modo_revisao,

            ultima_questao_revisao=False,

            posicao_revisao=None,

            total_revisao=0 if modo_revisao else None,

            areas_questoes=areas_questoes,

            dificuldades_questoes=dificuldades_questoes,

            competencias_questoes=competencias_questoes,

            habilidades_questoes=habilidades_questoes,

            linguas_questoes=linguas_questoes,

            area=area,

            dificuldade=dificuldade,

            competencia=competencia,

            habilidade=habilidade,

            lingua=lingua
        )

    # =====================================================
    # VERIFICAR SE A QUESTÃO EXISTE NA ORDEM
    # =====================================================

    if numero not in ordem_questoes:

        return redirect(
            url_for(
                "questoes",
                numero=ordem_questoes[0],
                area=area,
                dificuldade=dificuldade,
                competencia=competencia,
                habilidade=habilidade,
                lingua=lingua,
                revisao=1 if modo_revisao else None
            )
        )

    # =====================================================
    # CARREGAR QUESTÕES
    # =====================================================



    questao = None

    for item in questoes:

        if item["numero"] == numero:

            questao = item

            break

    if questao is None:
        return redirect(
            url_for(
                "questoes",
                numero=ordem_questoes[0],
                area=area if not modo_revisao else None,
                dificuldade=dificuldade if not modo_revisao else None,
                competencia=competencia if not modo_revisao else None,
                habilidade=habilidade if not modo_revisao else None,
                lingua=lingua if not modo_revisao else None,
                revisao=1 if modo_revisao else None
            )
        )

    # =====================================================
    # LOCALIZAR QUESTÃO NA NOVA ORDEM
    # =====================================================

    indice_ordem = ordem_questoes.index(
        numero
    )

    posicao_revisao = None
    total_revisao = None

    if modo_revisao:
        posicao_revisao = indice_ordem + 1
        total_revisao = len(ordem_questoes)

    # =====================================================
    # QUESTÃO ANTERIOR
    # =====================================================

    if indice_ordem > 0:

        numero_anterior = (
            ordem_questoes[
                indice_ordem - 1
            ]
        )

        tem_anterior = True

    else:

        numero_anterior = None

        tem_anterior = False

    # =====================================================
    # PRÓXIMA QUESTÃO
    # =====================================================

    if indice_ordem < len(ordem_questoes) - 1:

        numero_proxima = (
            ordem_questoes[
                indice_ordem + 1
            ]
        )

        tem_proxima = True

    else:

        numero_proxima = None

        tem_proxima = False

    ultima_questao_revisao = (
            modo_revisao
            and not tem_proxima
    )

    # =====================================================
    # ÚLTIMA RESPOSTA
    # =====================================================

    ultima_resposta = obter_ultima_resposta_questao(
        usuario_id,
        numero
    )

    questao_bloqueada = False
    proxima_tentativa = None

    if ultima_resposta:

        proxima_tentativa = (
            ultima_resposta[
                "proxima_tentativa"
            ]
        )

        if proxima_tentativa:

            if isinstance(
                proxima_tentativa,
                str
            ):

                data_proxima = datetime.fromisoformat(
                    proxima_tentativa
                )

            else:

                data_proxima = proxima_tentativa

            # PostgreSQL pode retornar datetime
            # sem timezone. Mantemos a comparação
            # com datetime.now() nesse caso.

            if data_proxima.tzinfo is not None:

                agora = datetime.now(
                    data_proxima.tzinfo
                )

            else:

                agora = datetime.now()

            if agora < data_proxima:

                questao_bloqueada = True

    # =====================================================
    # RENDERIZAR
    # =====================================================

    return render_template(
        "questoes.html",

        usuario=usuario,

        questao=questao,

        tem_anterior=tem_anterior,

        tem_proxima=tem_proxima,

        numero_anterior=numero_anterior,

        numero_proxima=numero_proxima,

        questao_bloqueada=questao_bloqueada,

        ultima_resposta=ultima_resposta,

        proxima_tentativa=proxima_tentativa,

        estudo_ativo=estudo_ativo,

        modo_revisao=modo_revisao,

        ultima_questao_revisao=ultima_questao_revisao,

        posicao_revisao=posicao_revisao,

        total_revisao=total_revisao,

        areas_questoes=areas_questoes,

        dificuldades_questoes=dificuldades_questoes,

        area=area,

        dificuldade=dificuldade,

        competencias_questoes=competencias_questoes,

        competencia=competencia,

        habilidades_questoes=habilidades_questoes,

        habilidade=habilidade,

        linguas_questoes=linguas_questoes,

        lingua=lingua
    )


@app.route(
    "/questoes/responder",
    methods=["POST"]
)
def responder_questao():

    usuario_id = session.get(
        "usuario_id"
    )

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401

    dados = request.get_json()

    if not dados:

        return jsonify({
            "erro": "Dados não enviados."
        }), 400

    numero_questao = dados.get(
        "questao_numero"
    )

    resposta = dados.get(
        "resposta"
    )

    if (
        numero_questao is None
        or resposta is None
    ):

        return jsonify({
            "erro": "Questão ou resposta não informada."
        }), 400

    try:

        numero_questao = int(
            numero_questao
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "erro": "Questão inválida."
        }), 400

    if not isinstance(
        resposta,
        str
    ):

        return jsonify({
            "erro": "Resposta inválida."
        }), 400

    resposta = resposta.strip().upper()

    if resposta not in {
        "A",
        "B",
        "C",
        "D",
        "E"
    }:

        return jsonify({
            "erro": "Resposta inválida."
        }), 400

    # =====================================================
    # CARREGAR QUESTÕES
    # =====================================================

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:

        questoes = json.load(
            arquivo
        )

    questao = None

    for item in questoes:

        if item["numero"] == numero_questao:

            questao = item

            break

    if questao is None:

        return jsonify({
            "erro": "Questão não encontrada."
        }), 404

    # =====================================================
    # VERIFICAR ÚLTIMA RESPOSTA
    # =====================================================

    ultima_resposta = (
        obter_ultima_resposta_questao(
            usuario_id,
            numero_questao
        )
    )

    # =====================================================
    # IMPEDIR RESPOSTA DURANTE O BLOQUEIO
    # =====================================================

    if ultima_resposta:

        proxima_tentativa_atual = (
            ultima_resposta[
                "proxima_tentativa"
            ]
        )

        if proxima_tentativa_atual:

            if isinstance(
                proxima_tentativa_atual,
                str
            ):

                data_proxima = (
                    datetime.fromisoformat(
                        proxima_tentativa_atual
                    )
                )

            else:

                data_proxima = (
                    proxima_tentativa_atual
                )

            if data_proxima.tzinfo is not None:

                agora = datetime.now(
                    data_proxima.tzinfo
                )

            else:

                agora = datetime.now()

            if agora < data_proxima:

                return jsonify({

                    "erro":
                        "Esta questão ainda está bloqueada.",

                    "proxima_tentativa":
                        data_proxima.isoformat()

                }), 409

    # =====================================================
    # VERIFICAR RESPOSTA
    # =====================================================

    resposta_correta = (
        questao["resposta"]
    )

    correta = (
        resposta == resposta_correta
    )

    # =====================================================
    # DATA DA RESPOSTA
    # =====================================================

    data_resposta = datetime.now()

    # =====================================================
    # TENTATIVA
    # =====================================================

    tentativa = obter_numero_tentativa(
        usuario_id,
        numero_questao
    )

    # =====================================================
    # INTERVALO DE REVISÃO
    # =====================================================

    intervalo_revisao = (
        calcular_intervalo_revisao(
            correta,
            ultima_resposta
        )
    )

    # =====================================================
    # PRÓXIMA TENTATIVA
    # =====================================================

    proxima_tentativa = (
        data_resposta
        + timedelta(
            days=intervalo_revisao
        )
    )

    # =====================================================
    # REGISTRAR RESPOSTA
    # =====================================================

    registrar_resposta_questao(

        usuario_id=usuario_id,

        questao_numero=numero_questao,

        resposta=resposta,

        correta=1 if correta else 0,

        tentativa=tentativa,

        intervalo_revisao=intervalo_revisao,

        data_resposta=data_resposta,

        proxima_tentativa=proxima_tentativa

    )

    # =====================================================
    # RESPOSTA
    # =====================================================

    return jsonify({

        "sucesso": True,

        "correta": correta,

        "resposta_usuario":
            resposta,

        "resposta_correta":
            resposta_correta,

        "tentativa":
            tentativa,

        "intervalo_revisao":
            intervalo_revisao,

        "proxima_tentativa":
            proxima_tentativa.isoformat()

    })

@app.route("/questoes/revisar")
def revisar_questoes():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(
            url_for("pagina_login")
        )

    usuario = obter_usuario_por_id(
        usuario_id
    )

    area = request.args.get("area")

    dificuldade = request.args.get("dificuldade")

    competencia = request.args.get("competencia")

    habilidade = request.args.get("habilidade")

    lingua = request.args.get("lingua")

    questoes_revisao = obter_questoes_para_revisao(
        usuario_id
    )

    if area or dificuldade or competencia or habilidade or lingua:
        questoes_filtradas = obter_questoes_filtradas(
            area=area,
            dificuldade=dificuldade,
            competencia=competencia,
            habilidade=habilidade,
            lingua=lingua
        )

        numeros_filtrados = {
            questao["numero"]
            for questao in questoes_filtradas
        }

        questoes_revisao = [
            resposta
            for resposta in questoes_revisao
            if resposta["questao_numero"] in numeros_filtrados
        ]

    return render_template(
        "revisar_questoes.html",
        usuario=usuario,
        questoes_revisao=questoes_revisao,
        area=area,
        dificuldade=dificuldade,
        competencia=competencia,
        habilidade=habilidade,
        lingua=lingua
    )

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404

# ==========================
# CADASTRO
# ==========================

@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def pagina_cadastro():

    if request.method == "POST":

        nome = request.form.get(
            "nome"
        )

        email = request.form.get(
            "email"
        )

        senha = request.form.get(
            "senha"
        )

        confirmar_senha = request.form.get(
            "confirmar_senha"
        )

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

            flash(
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

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":

    app.run(
        debug=False
    )
