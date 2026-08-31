from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
import json
from controllers.web.configuracoes_controller import carregar_configuracoes, atualizar_conta, alterar_senha, \
    atualizar_metas_configuracoes
from database.conexao import conectar
from studyhub.controllers.estudo_controller import iniciar_estudo_controller, finalizar_estudo_controller, \
    obter_estudo_ativo_controller
from studyhub.controllers.web.tarefa_controller import  editar_tarefa_controller, excluir_tarefa_controller
from studyhub.database.usuario_repository import obter_usuario_por_id
from studyhub.database.tarefa_repository import listar_tarefas, buscar_tarefa
from studyhub.controllers.web.tarefa_controller import adicionar_tarefa_controller, concluir_tarefa_controller
from studyhub.services.dashboard_service import carregar_dashboard
from studyhub.controllers.web.cadastro_controller import realizar_cadastro
from studyhub.controllers.web.login_controller import realizar_login
from services.provas_service import obter_prova
from services.provas_service import listar_provas
from controllers.resultados_controller import obter_historico
from database.estudos_repository import obter_estudos_por_data, obter_total_segundos
from database.tarefa_repository import obter_tarefas_por_data
from studyhub.database.resultados_repository import obter_resultados_por_data, converter_tempo_para_segundos, \
    obter_provas_por_periodo, obter_segundos_provas
from studyhub.services.provas_service import obter_catalogo_por_id
from studyhub.database.anotacao_repository import (
    obter_anotacao_por_data,
    salvar_anotacao
)
from datetime import datetime
from database.questoes_repository import (
    obter_ultima_resposta_questao
)
from studyhub.controllers.dados_controller import (
    obter_dados_exportacao,
    limpar_historico
)
from database.estudos_repository import (
    obter_estudos_por_periodo
)
from datetime import date, timedelta
from database.resultados_repository import (
    obter_resumo_usuario,
    listar_resultados_usuario
)
from studyhub.database.estudos_repository import obter_estudos_por_mes
from studyhub.database.tarefa_repository import obter_tarefas_por_mes
from studyhub.database.resultados_repository import obter_resultados_por_mes
from studyhub.database.anotacao_repository import obter_anotacoes_por_mes
from database.resultados_repository import (
    salvar_resultado,
    salvar_respostas_prova,
    obter_desempenho_por_area
)
from studyhub.controllers.web.configuracoes_controller import (
    atualizar_tema,
excluir_conta as excluir_conta_controller
)
app = Flask(__name__)

app.secret_key = "studyhub-chave-desenvolvimento"

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

@app.route("/estudos/iniciar-ajax", methods=["POST"])
def iniciar_estudo_ajax():

    usuario_id = session.get("usuario_id")

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

        "inicio":
            estudo["inicio"]

    })

@app.route("/estudos/finalizar-ajax", methods=["POST"])
def finalizar_estudo_ajax():

    usuario_id = session.get("usuario_id")

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

@app.route("/estudos/finalizar-automatico", methods=["POST"])
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

@app.route("/provas")
def pagina_provas():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

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
        return redirect(url_for("pagina_login"))

    prova = obter_prova(id_prova)

    return render_template(

        "provas/prova.html",

        prova=prova,

        questao_atual=prova.questoes[0]

    )


@app.route("/provas/resultado", methods=["GET", "POST"])
def resultado_prova():

    if request.method == "POST":

        dados = request.get_json()

        print("\n==============================")
        print("DADOS RECEBIDOS DA PROVA")
        print("==============================")
        print(dados)
        print("==============================\n")


        if not dados:

            return jsonify({
                "erro": "Nenhum dado foi recebido."
            }), 400


        porcentagem = round(
            (dados["acertos"] / dados["total"]) * 100,
            2
        )


        resultado = {

            "usuario_id":
                session["usuario_id"],

            "prova_id":
                dados["prova_id"],

            "acertos":
                dados["acertos"],

            "erros":
                dados["erros"],

            "nao_respondidas":
                dados["naoRespondidas"],

            "total":
                dados["total"],

            "tempo_gasto":
                dados["tempoGasto"],

            "porcentagem":
                porcentagem

        }


        print("\n==============================")
        print("RESULTADO CALCULADO")
        print("==============================")
        print(resultado)
        print("==============================\n")


        salvar_resultado(resultado)


        salvar_respostas_prova(

            usuario_id=session["usuario_id"],

            prova_id=dados["prova_id"],

            questoes=dados["questoes"],

            respostas=dados["respostas"]

        )


        session["resultado_prova"] = {

            "prova_id":
                dados["prova_id"],

            "acertos":
                dados["acertos"],

            "erros":
                dados["erros"],

            "nao_respondidas":
                dados["naoRespondidas"],

            "total":
                dados["total"],

            "porcentagem":
                porcentagem,

            "tempo_gasto":
                dados["tempoGasto"]

        }


        print("\n==============================")
        print("RESULTADO SALVO NA SESSÃO")
        print("==============================")
        print(session["resultado_prova"])
        print("==============================\n")


        return jsonify({
            "status": "ok"
        })


    # =====================================================
    # GET
    # =====================================================

    resultado = session.get(

        "resultado_prova",

        {

            "prova_id": None,

            "acertos": 0,

            "erros": 0,

            "questoes_erradas": [],

            "nao_respondidas": 0,

            "total": 90,

            "porcentagem": 0,

            "tempo_gasto": "0min"

        }

    )


    print("\n==============================")
    print("RESULTADO ENVIADO PARA HTML")
    print("==============================")
    print(resultado)
    print("==============================\n")


    return render_template(

        "provas/resultado.html",

        resultado=resultado,

        titulo="Resultado",

        classe_body="sidebar-toggle"

    )

@app.route("/provas/historico")
def historico_provas():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    usuario = obter_usuario_por_id(session["usuario_id"])

    historico = obter_historico(session["usuario_id"])

    return render_template(
        "provas/historico.html",
        historico=historico,
        usuario=usuario,
        titulo="Histórico de Provas",
        classe_body="sidebar-toggle"
    )

@app.route("/calendario")
def pagina_calendario():
    return render_template("/calendario.html")

@app.route("/calendario/estudos")
def calendario_estudos():

    usuario_id = session.get("usuario_id")

    data = request.args.get("data")


    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    if not data:

        return jsonify({
            "erro": "Data não informada."
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

    usuario_id = session.get("usuario_id")

    data = request.args.get("data")


    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    if not data:

        return jsonify({
            "erro": "Data não informada."
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

    usuario_id = session.get("usuario_id")

    data = request.args.get("data")


    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    if not data:

        return jsonify({
            "erro": "Data não informada."
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

            "id": id_prova,

            "nome": catalogo["nome"],

            "dia": catalogo["dia"],

            "acertos": resultado_prova["acertos"],

            "erros": resultado_prova["erros"],

            "nao_respondidas":
                resultado_prova["nao_respondidas"],

            "total": resultado_prova["total"],

            "tempo_gasto":
                resultado_prova["tempo_gasto"],

            "porcentagem":
                resultado_prova["porcentagem"],

            "data":
                resultado_prova["data"]

        })


    return jsonify(resultado)

@app.route("/calendario/anotacao")
def calendario_anotacao():

    usuario_id = session.get("usuario_id")

    data = request.args.get("data")


    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    if not data:

        return jsonify({
            "erro": "Data não informada."
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

        "id": anotacao["id"],

        "data": anotacao["data"],

        "texto": anotacao["texto"]

    })

@app.route("/calendario/anotacao", methods=["POST"])
def salvar_calendario_anotacao():

    usuario_id = session.get("usuario_id")


    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    dados = request.get_json()


    data = dados.get("data")
    texto = dados.get("texto", "").strip()


    if not data:

        return jsonify({
            "erro": "Data não informada."
        }), 400


    if not texto:

        return jsonify({
            "erro": "A anotação não pode estar vazia."
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

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)


    if not mes or not ano:
        return jsonify({
            "erro": "Mês e ano são obrigatórios."
        }), 400


    indicadores = {}


    # Estudos
    estudos = obter_estudos_por_mes(
        usuario_id,
        ano,
        mes
    )


    for estudo in estudos:

        data = estudo["data"]

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["estudo"] = True


    # Tarefas
    tarefas = obter_tarefas_por_mes(
        usuario_id,
        ano,
        mes
    )


    for tarefa in tarefas:

        data = tarefa["data"]

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["tarefa"] = True


    # Provas
    provas = obter_resultados_por_mes(
        usuario_id,
        ano,
        mes
    )


    for prova in provas:

        data = prova["data"]

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["prova"] = True


    # Anotações
    anotacoes = obter_anotacoes_por_mes(
        usuario_id,
        ano,
        mes
    )


    for anotacao in anotacoes:

        data = anotacao["data"]

        if data not in indicadores:
            indicadores[data] = {}

        indicadores[data]["anotacao"] = True


    return jsonify(indicadores)

@app.route("/estatisticas")
def pagina_estatisticas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("login"))

    return render_template("estatisticas/estatisticas.html")

@app.route("/estatisticas/resumo")
def estatisticas_resumo():

    usuario_id = session.get("usuario_id")

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
        segundos_estudo +
        segundos_provas
    )


    provas = resultado["provas"]
    questoes = resultado["questoes"]
    acertos = resultado["acertos"]
    erros = resultado["erros"]
    nao_respondidas = resultado["nao_respondidas"]


    respondidas = acertos + erros


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
            round(porcentagem, 1)

    })

@app.route("/estatisticas/evolucao")
def estatisticas_evolucao():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    # =========================================
    # DATA SELECIONADA
    # =========================================

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


    # =========================================
    # VALIDAR MÊS
    # =========================================

    if mes < 1 or mes > 12:

        return jsonify({
            "erro": "Mês inválido."
        }), 400


    # =========================================
    # PRIMEIRO E ÚLTIMO DIA DO MÊS
    # =========================================

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


    # =========================================
    # ESTUDOS
    # =========================================

    estudos = obter_estudos_por_periodo(
        usuario_id,
        inicio.isoformat(),
        fim.isoformat()
    )


    estudos_por_data = {}


    for estudo in estudos:

        estudos_por_data[
            estudo["data"]
        ] = estudo["duracao"]


    # =========================================
    # PROVAS
    # =========================================

    provas = obter_provas_por_periodo(
        usuario_id,
        inicio.isoformat(),
        fim.isoformat()
    )


    provas_por_data = {}


    for prova in provas:

        data = prova["data"]


        segundos = converter_tempo_para_segundos(
            prova["tempo_gasto"]
        )


        provas_por_data[data] = (
            provas_por_data.get(data, 0)
            + segundos
        )


    # =========================================
    # RESULTADO
    # =========================================

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

            "data": data_formatada,

            "duracao": duracao_total

        })


        data_atual += timedelta(days=1)


    return jsonify(resultado)

@app.route("/estatisticas/provas")
def estatisticas_provas():

    usuario_id = session.get("usuario_id")

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

            "id": id_prova,

            "nome": catalogo["nome"],

            "dia": catalogo["dia"],

            "acertos": resultado["acertos"],

            "erros": resultado["erros"],

            "nao_respondidas":
                resultado["nao_respondidas"],

            "total": resultado["total"],

            "tempo_gasto":
                resultado["tempo_gasto"],

            "porcentagem":
                resultado["porcentagem"],

            "data":
                resultado["data"]

        })


    return jsonify(provas)

@app.route("/estatisticas/areas")
def estatisticas_areas():

    usuario_id = session.get("usuario_id")

    if not usuario_id:

        return jsonify({
            "erro": "Usuário não autenticado."
        }), 401


    desempenho = obter_desempenho_por_area(
        usuario_id
    )


    return jsonify(desempenho)

@app.route("/configuracoes")
def pagina_configuracoes():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

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

@app.route("/configuracoes/conta", methods=["POST"])
def atualizar_conta_configuracoes():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    nome = request.form.get("nome")
    email = request.form.get("email")

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


    if resultado:

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


    if resultado:

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


    if resultado:

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
        indent=4
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


    if resultado:

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
    "/configuracoes/excluir-conta",
    methods=["POST"]
)
def excluir_conta_configuracoes():

    if "usuario_id" not in session:

        return redirect(
            url_for("login")
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

@app.route("/questoes")
def questoes_inicio():

    return redirect(
        url_for(
            "questoes",
            numero=1
        )
    )

@app.route("/questoes/<int:numero>")
def questoes(numero):

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("login"))

    usuario = obter_usuario_por_id(
        usuario_id
    )

    estudo_ativo = obter_estudo_ativo_controller(usuario_id)


    # =====================================================
    # CARREGAR QUESTÕES
    # =====================================================

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:

        questoes = json.load(arquivo)


    # =====================================================
    # ENCONTRAR QUESTÃO
    # =====================================================

    questao = None
    indice_questao = None

    for indice, item in enumerate(questoes):

        if item["numero"] == numero:

            questao = item
            indice_questao = indice

            break


    # =====================================================
    # QUESTÃO NÃO ENCONTRADA
    # =====================================================

    if questao is None:

        return redirect(
            url_for(
                "questoes",
                numero=1
            )
        )


    # =====================================================
    # NAVEGAÇÃO
    # =====================================================

    tem_anterior = (
        indice_questao > 0
    )

    tem_proxima = (
        indice_questao < len(questoes) - 1
    )

    # =====================================================
    # VERIFICAR BLOQUEIO
    # =====================================================

    ultima_resposta = obter_ultima_resposta_questao(
        usuario_id,
        numero
    )

    questao_bloqueada = False
    proxima_tentativa = None

    if ultima_resposta:

        proxima_tentativa = (
            ultima_resposta["proxima_tentativa"]
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

            if datetime.now() < data_proxima:
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

        questao_bloqueada=questao_bloqueada,

        ultima_resposta=ultima_resposta,

        proxima_tentativa=proxima_tentativa,

        estudo_ativo=estudo_ativo
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

        if (
            item["numero"]
            == int(numero_questao)
        ):

            questao = item

            break


    if questao is None:

        return jsonify({
            "erro": "Questão não encontrada."
        }), 404


    # =====================================================
    # OBTER RESPOSTA CORRETA
    # =====================================================

    resposta_correta = questao["resposta"]


    # =====================================================
    # VERIFICAR RESPOSTA
    # =====================================================

    correta = (
        resposta == resposta_correta
    )


    # =====================================================
    # CALCULAR PRÓXIMA TENTATIVA
    # =====================================================

    from datetime import datetime, timedelta

    data_resposta = datetime.now()

    proxima_tentativa = (
        data_resposta
        + timedelta(days=3)
    )


    # =====================================================
    # SALVAR RESULTADO
    # =====================================================

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO respostas_questoes (

            usuario_id,
            questao_numero,
            resposta,
            correta,
            data_resposta,
            proxima_tentativa

        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            usuario_id,
            int(numero_questao),
            resposta,
            1 if correta else 0,
            data_resposta,
            proxima_tentativa
        )
    )


    conexao.commit()

    conexao.close()


    # =====================================================
    # RETORNAR RESULTADO
    # =====================================================

    return jsonify({

        "sucesso": True,

        "correta": correta,

        "resposta_usuario": resposta,

        "resposta_correta": resposta_correta,

        "proxima_tentativa":
            proxima_tentativa.isoformat()

    })
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