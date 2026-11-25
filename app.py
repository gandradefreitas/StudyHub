from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, \
    send_from_directory, abort

import json


import os
from hashlib import blake2b
from uuid import UUID, uuid4

from flask_wtf.csrf import CSRFProtect


from psycopg import Error as ErroPostgres

from database.conexao import conectar
from database.criar_banco import verificar_esquema_web
from database.provas_objetivas_repository import (
    TentativaObjetivaEncerrada,
    obter_inicio_tentativa_objetiva,
    obter_ou_criar_tentativa_objetiva,
)
from security.respostas import configurar_protecao_http
from database.respostas_discursivas_repository import obter_respostas, obter_tentativa_discursiva_por_id, \
    listar_tentativas_discursivas_usuario, reagendar_correcao_discursiva, \
    obter_segundos_restantes_tentativa

from controllers.web.configuracoes_controller import (
    carregar_configuracoes,
    atualizar_conta,
    alterar_senha,
    atualizar_metas_configuracoes,
    atualizar_tema,
)

from controllers.prova_discursiva_controller import (
    carregar_prova_ita_segunda_fase,
    obter_campos_permitidos,
    preparar_tentativa_discursiva,
    salvar_respostas_tentativa,
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
from controllers.web.autenticacao_controller import registrar_autenticacao
from controllers.web.estatisticas_controller import registrar_estatisticas
from controllers.web.exportacoes_controller import registrar_exportacoes
from controllers.resultados_controller import obter_historico
from controllers.dados_controller import (
    limpar_historico
)

from database.usuario_repository import (
    obter_usuario_por_id,
)
from database.tarefa_repository import (
    listar_tarefas,
    buscar_tarefa,
    obter_tarefas_por_data,
    obter_tarefas_por_mes
)

from database.estudos_repository import (
    obter_estudos_por_data,
    obter_estudos_por_mes
)

from database.resultados_repository import (
    obter_resultados_por_data,
    obter_resumo_usuario,
    listar_resultados_usuario,
    obter_resultados_por_mes,
    converter_tempo_para_segundos, obter_respostas_por_resultado, obter_resultado_por_id, salvar_resultado_com_respostas
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
    obter_habilidades_questoes, obter_linguas_questoes
)

from controllers.idiomas_controller import idiomas
from controllers.redacoes_controller import listar_envios, redacoes
from database.idiomas_repository import obter_progresso
from services.configuracoes import definir_senha_usuario
from services.dashboard_service import carregar_dashboard
from services.notas_service import carregar_notas
from services.provas_service import (
    obter_prova,
    listar_provas,
    obter_catalogo_por_id
)

from datetime import datetime, date, timedelta, timezone

from utils.horario import horario_studyhub

app = Flask(__name__)
app.jinja_env.filters["horario_studyhub"] = horario_studyhub

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY não configurada.")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

csrf = CSRFProtect(app)
configurar_protecao_http(app)
app.register_blueprint(idiomas)
app.register_blueprint(redacoes)
registrar_autenticacao(app)
registrar_estatisticas(app)
registrar_exportacoes(app)


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

    _, leituras = obter_progresso(session["usuario_id"])
    envios = listar_envios(session["usuario_id"])
    return render_template(
        "dashboard.html",
        leituras_concluidas=len(leituras),
        palavras_lidas=sum(leitura["palavras"] for leitura in leituras.values()),
        redacoes_enviadas=len(envios),
        **dados,
        classe_body="sidebar-toggle",
        mostrar_pesquisa=True,
        mostrar_perfil=True
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


# ============================================================
# ITA 2025 — SEGUNDA FASE DISCURSIVA
# ============================================================

DISCIPLINAS_ITA_SEGUNDA_FASE = {
    "matematica": "Matemática",
    "fisica": "Física",
    "quimica": "Química",
}


def obter_disciplina_ita(slug):
    return DISCIPLINAS_ITA_SEGUNDA_FASE.get(slug)


def redirecionar_prova_ita(slug):
    return redirect(
        url_for(
            "visualizar_prova_ita_segunda_fase",
            disciplina=slug,
        )
    )


# ============================================================
# ITA 2025 — SELEÇÃO DA SEGUNDA FASE
# ============================================================

@app.route("/provas/ita/2025/segunda-fase")
def selecionar_provas_ita_segunda_fase():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    disciplinas = [
        {
            "nome": "Matemática",
            "slug": "matematica",
            "tipo": "Discursiva",
            "questoes": 10,
            "tempo": "4 horas",
            "descricao": (
                "Resolva os problemas apresentando "
                "seus cálculos e justificativas."
            ),
        },
        {
            "nome": "Física",
            "slug": "fisica",
            "tipo": "Discursiva",
            "questoes": 10,
            "tempo": "4 horas",
            "descricao": (
                "Desenvolva as resoluções e apresente "
                "o raciocínio utilizado."
            ),
        },
        {
            "nome": "Química",
            "slug": "quimica",
            "tipo": "Discursiva",
            "questoes": 10,
            "tempo": "4 horas",
            "descricao": (
                "Resolva os problemas com cálculos "
                "e justificativas quando necessários."
            ),
        },
        {
            "nome": "Português",
            "slug": "portugues",
            "tipo": "Objetiva",
            "questoes": 20,
            "tempo": "4 horas",
            "descricao": (
                "Responda às questões objetivas "
                "de Língua Portuguesa."
            ),
        },
    ]

    return render_template(
        "provas/ita_segunda_fase.html",
        disciplinas=disciplinas,
        titulo="ITA 2025 — Segunda Fase",
        classe_body="sidebar-toggle",
    )

@app.route(
    "/provas/ita/2025/segunda-fase/<disciplina>"
)
def visualizar_prova_ita_segunda_fase(disciplina):

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    nome_disciplina = obter_disciplina_ita(disciplina)

    if nome_disciplina is None:
        abort(404)

    usuario_id = session["usuario_id"]

    prova = carregar_prova_ita_segunda_fase(disciplina)

    tentativa_id, respostas, status = preparar_tentativa_discursiva(
        usuario_id=usuario_id,
        disciplina=nome_disciplina,
    )

    if tentativa_id is None and status == "limite_diario":
        flash(
            f"Você já iniciou a prova de {nome_disciplina} hoje. "
            "Você poderá iniciar outra amanhã.",
            "warning",
        )
        return redirect(url_for("selecionar_provas_ita_segunda_fase"))

    tempo_restante_segundos = 0
    if status == "em_andamento":
        partes_tempo = prova.tempo.strip().lower().split()
        if len(partes_tempo) == 2 and partes_tempo[0].isdigit():
            quantidade_tempo = int(partes_tempo[0])
            unidade_tempo = partes_tempo[1]
            multiplicadores_tempo = {
                "hora": 3600,
                "horas": 3600,
                "minuto": 60,
                "minutos": 60,
                "segundo": 1,
                "segundos": 1,
            }
            duracao_segundos = (
                quantidade_tempo * multiplicadores_tempo[unidade_tempo]
            )
        else:
            raise ValueError(
                f"Duração inválida para a prova discursiva: {prova.tempo!r}"
            )

        tempo_restante_segundos = obter_segundos_restantes_tentativa(
            tentativa_id,
            usuario_id,
            duracao_segundos,
        )

    return render_template(
        "provas/prova_discursiva.html",
        prova=prova,
        tentativa_id=tentativa_id,
        respostas=respostas,
        status=status,
        tempo_restante_segundos=tempo_restante_segundos,
        disciplina_slug=disciplina,
        titulo=f"ITA 2025 — Segunda Fase — {nome_disciplina}",
        classe_body="sidebar-toggle",
    )


@app.route(
    "/provas/ita/2025/segunda-fase/<disciplina>/salvar",
    methods=["POST"],
)
def salvar_prova_ita_segunda_fase(disciplina):

    ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        if ajax:
            return jsonify(status="erro", mensagem="Sua sessão expirou. Entre novamente para salvar as respostas."), 401
        return redirect(url_for("pagina_login"))

    nome_disciplina = obter_disciplina_ita(disciplina)

    if nome_disciplina is None:
        abort(404)

    tentativa_id = request.form.get("tentativa_id", type=int)

    if not tentativa_id:
        if ajax:
            return jsonify(status="erro", mensagem="Não foi possível identificar sua tentativa."), 400
        flash("Não foi possível identificar sua tentativa.", "error")
        return redirecionar_prova_ita(disciplina)

    prova = carregar_prova_ita_segunda_fase(disciplina)

    try:
        salvar_respostas_tentativa(
            tentativa_id, usuario_id, prova, request.form
        )
    except ValueError as erro:
        if ajax:
            return jsonify(status="erro", mensagem=str(erro)), 400
        flash(str(erro), "error")
        return redirecionar_prova_ita(disciplina)

    if ajax:
        return jsonify(status="ok")

    flash("Respostas salvas com sucesso!", "success")

    return redirecionar_prova_ita(disciplina)


@app.route(
    "/provas/ita/2025/segunda-fase/resultado/<int:tentativa_id>"
)
def visualizar_resultado_discursivo(tentativa_id):

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("pagina_login"))

    tentativa = obter_tentativa_discursiva_por_id(
        tentativa_id=tentativa_id,
        usuario_id=usuario_id,
    )

    if tentativa is None:
        abort(404)

    respostas = obter_respostas(tentativa_id)
    reivindicada_ate = tentativa.get("correcao_reivindicada_ate")
    agora_utc = datetime.now(timezone.utc)
    if reivindicada_ate is not None and reivindicada_ate.tzinfo is None:
        reivindicada_ate = reivindicada_ate.replace(tzinfo=timezone.utc)
    tentativa["correcao_em_andamento"] = bool(
        reivindicada_ate is not None and reivindicada_ate > agora_utc
    )
    tentativa["pode_tentar_correcao"] = bool(
        tentativa["status"] == "finalizada"
        and (tentativa.get("resultado_correcao") or {}).get("status") == "falha_definitiva"
    )

    respostas_esperadas = {}
    pacote = tentativa.get("resultado_correcao") or {}
    if pacote.get("modo_correcao") == "resposta_final" and pacote.get("correcao"):
        disciplina_slug = next(
            slug for slug, nome in DISCIPLINAS_ITA_SEGUNDA_FASE.items()
            if nome == tentativa["disciplina"]
        )
        prova = carregar_prova_ita_segunda_fase(disciplina_slug)
        respostas_esperadas = {
            f"Q{questao.numero}{str(item.letra or '').strip()}": item.resposta_esperada
            for questao in prova.questoes
            for item in questao.itens
        }

    return render_template(
        "provas/resultado.html",
        tentativa=tentativa,
        respostas=respostas,
        respostas_esperadas=respostas_esperadas,
        tipo_resultado="discursivo",
        titulo=f"Resultado — {tentativa['disciplina']}",
        classe_body="sidebar-toggle"
    )


@app.route(
    "/provas/ita/2025/segunda-fase/resultado/<int:tentativa_id>/tentar-correcao",
    methods=["POST"],
)
def tentar_correcao_discursiva(tentativa_id):
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("pagina_login"))

    tentativa = obter_tentativa_discursiva_por_id(tentativa_id, usuario_id)
    if tentativa is None:
        abort(404)
    if reagendar_correcao_discursiva(tentativa_id, usuario_id):
        flash("A prova foi reenviada para a fila de correção.", "info")
    return redirect(url_for("visualizar_resultado_discursivo", tentativa_id=tentativa_id))

@app.route(
    "/provas/ita/2025/segunda-fase/<disciplina>/finalizar",
    methods=["POST"],
)
def finalizar_prova_ita_segunda_fase(disciplina):

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("pagina_login"))

    nome_disciplina = obter_disciplina_ita(disciplina)

    if nome_disciplina is None:
        abort(404)

    tentativa_id = request.form.get("tentativa_id", type=int)

    if not tentativa_id:
        flash(
            "Não foi possível identificar sua tentativa.",
            "error",
        )
        return redirecionar_prova_ita(disciplina)

    prova = carregar_prova_ita_segunda_fase(disciplina)
    try:
        salvar_respostas_tentativa(
            tentativa_id, usuario_id, prova, request.form, finalizar=True
        )
    except ValueError as erro:
        flash(str(erro), "error")
        return redirecionar_prova_ita(disciplina)

    flash("Prova finalizada. A correção será processada pelo StudyHub.", "success")

    return redirect(
        url_for(
            "visualizar_resultado_discursivo",
            tentativa_id=tentativa_id,
        )
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


    tentativa = obter_ou_criar_tentativa_objetiva(session["usuario_id"], prova.id)
    duracao = converter_tempo_para_segundos(prova.tempo)
    agora = datetime.now(timezone.utc)
    return render_template(
        "provas/prova.html",
        prova=prova,
        questao_atual=prova.questoes[0],
        tentativa_id=str(tentativa["id"]),
        tempo_restante=max(0, duracao - (agora - tentativa["inicio"]).total_seconds()),
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

        if (
                not isinstance(questoes_recebidas, list)
                or not questoes_recebidas
        ):
            return jsonify({
                "erro": "Questões da prova não foram informadas."
            }), 400

        numeros_recebidos = []

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

            numeros_recebidos.append(numero)

        # Rejeita números duplicados.
        if len(numeros_recebidos) != len(set(numeros_recebidos)):
            return jsonify({
                "erro": "A lista contém questões duplicadas."
            }), 400

        numeros_questoes = set(numeros_recebidos)

        # ------------------------------------------------
        # IDENTIFICA AS QUESTÕES OFICIAIS ESPERADAS
        # ------------------------------------------------

        lingua_escolhida = dados.get("lingua")

        if prova.tipo == "ENEM" and prova.dia == "Primeiro Dia":
            if isinstance(lingua_escolhida, str):
                lingua_escolhida = lingua_escolhida.strip().lower().replace("ê", "e")

            # Verifica se o idioma informado é válido.
            if lingua_escolhida not in ("ingles", "espanhol"):
                return jsonify({
                    "erro": "Idioma da prova inválido."
                }), 400

            questoes_esperadas = [
                questao
                for questao in prova.questoes
                if (
                        not questao.lingua
                        or questao.lingua.lower().replace("ê", "e") == lingua_escolhida
                )
            ]

        else:

            questoes_esperadas = list(prova.questoes)

        numeros_esperados = {
            questao.numero
            for questao in questoes_esperadas
        }

        # ------------------------------------------------
        # CONFERE SE A LISTA RECEBIDA É EXATAMENTE A ESPERADA
        # ------------------------------------------------

        if numeros_questoes != numeros_esperados:
            return jsonify({
                "erro": (
                    "A lista de questões não corresponde "
                    "ao conjunto oficial da prova."
                )
            }), 400

        # Utiliza os objetos oficiais carregados no servidor.
        # Não confia nos enunciados ou dados enviados pelo cliente.
        questoes_realizadas = questoes_esperadas


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
                resposta_usuario = int(resposta_usuario)

            except (TypeError, ValueError):
                return jsonify({
                    "erro": "Uma ou mais respostas são inválidas."
                }), 400

            if not (
                0 <= resposta_usuario < len(questao.alternativas)
            ):
                return jsonify({
                    "erro": "Alternativa inválida."
                }), 400

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

        try:
            tentativa_id = UUID(dados.get("tentativa_id", ""))
        except (ValueError, TypeError, AttributeError):
            return jsonify(erro="Tentativa inválida. Reabra a prova para continuar."), 400

        inicio = obter_inicio_tentativa_objetiva(usuario_id, prova_id, tentativa_id)
        if inicio is None:
            return jsonify(erro="Esta tentativa não está mais aberta para esta conta."), 409

        duracao = datetime.now(timezone.utc) - inicio
        limite = converter_tempo_para_segundos(prova.tempo)
        segundos = min(limite, max(0, int(duracao.total_seconds())))

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
        # SALVA RESULTADO E RESPOSTAS EM UMA ÚNICA TRANSAÇÃO
        # ------------------------------------------------

        try:

            resultado_id = salvar_resultado_com_respostas(
                resultado=resultado,
                questoes=questoes_realizadas,
                respostas=respostas,
                tentativa_id=tentativa_id,
            )

        except TentativaObjetivaEncerrada as erro:
            return jsonify(erro=str(erro)), 409

        except Exception:

            app.logger.exception(
                "Erro ao salvar resultado e respostas da prova."
            )

            return jsonify({
                "erro": (
                    "Não foi possível salvar o resultado. "
                    "Tente novamente."
                )
            }), 500

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
            lingua_escolhida = (resultado.get("lingua") or "").lower().replace("ê", "e")

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
                                    or questao.lingua.lower().replace("ê", "e") == lingua_escolhida
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
        tipo_resultado="objetivo",
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


@app.route("/notas")
def pagina_notas():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("pagina_login"))

    return render_template(
        "provas/notas.html",
        usuario=obter_usuario_por_id(usuario_id),
        classe_body="sidebar-toggle",
        **carregar_notas(usuario_id),
    )


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
        redacoes=listar_envios(session["usuario_id"]),
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
        tipo_resultado="objetivo",
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
    "/configuracoes/dados/limpar",
    methods=["POST"]
)
def limpar_historico_rota():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    resultado, mensagem = limpar_historico(
        session["usuario_id"],
        incluir_leituras=request.form.get("incluir_leituras") == "1",
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


# ==========================
# QUESTÕES
# ==========================

def questoes_em_ordem_aleatoria(usuario_id):
    # Ordenar pela chave de cada questão mantém as demais no lugar após uma resposta.
    semente = session.get("ordem_pratica")
    if semente is None:
        semente = uuid4().hex
        session["ordem_pratica"] = semente
    return sorted(
        obter_ordem_questoes(usuario_id),
        key=lambda numero: blake2b(f"{semente}:{numero}".encode(), digest_size=8).digest(),
    )


@app.route("/questoes")
def questoes_inicio():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return redirect(
            url_for("pagina_login")
        )

    ordem_questoes = questoes_em_ordem_aleatoria(usuario_id)

    return redirect(
        url_for(
            "questoes",
            numero=ordem_questoes[0] if ordem_questoes else 1
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

    ordem_questoes = questoes_em_ordem_aleatoria(usuario_id)

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
            questoes_concluidas=bool(questoes),

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
    try:
        with conectar(connect_timeout=3) as conexao:
            conexao.execute("SET LOCAL statement_timeout = '1500ms'")
            if verificar_esquema_web(conexao):
                return "OK", 200
            app.logger.warning("Health check: há migrações pendentes.")
    except (ErroPostgres, KeyError) as erro:
        app.logger.warning(
            "Health check: %s (SQLSTATE %s).",
            type(erro).__name__, getattr(erro, "sqlstate", None),
        )
    return "Serviço indisponível", 503

if __name__ == "__main__":

    app.run(
        debug=False
    )
