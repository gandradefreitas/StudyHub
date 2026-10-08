import json
from datetime import datetime
from database.conexao import conectar


def registrar_resposta_questao(
    usuario_id,
    questao_numero,
    resposta,
    correta,
    tentativa,
    intervalo_revisao,
    data_resposta,
    proxima_tentativa
):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO respostas_questoes (
            usuario_id,
            questao_numero,
            resposta,
            correta,
            tentativa,
            intervalo_revisao,
            data_resposta,
            proxima_tentativa
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        usuario_id,
        questao_numero,
        resposta,
        correta,
        tentativa,
        intervalo_revisao,
        data_resposta,
        proxima_tentativa
    ))

    conexao.commit()

    conexao.close()


def obter_ultima_resposta_questao(
    usuario_id,
    questao_numero
):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            resposta,
            correta,
            tentativa,
            intervalo_revisao,
            data_resposta,
            proxima_tentativa
        FROM respostas_questoes
        WHERE usuario_id = %s
        AND questao_numero = %s
        ORDER BY data_resposta DESC
        LIMIT 1
    """, (
        usuario_id,
        questao_numero
    ))

    resultado = cursor.fetchone()

    conexao.close()

    return resultado


# =====================================================
# ORDEM DAS QUESTÕES
# =====================================================

def obter_ordem_questoes(usuario_id, total_questoes=50):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (questao_numero)
            questao_numero,
            proxima_tentativa
        FROM respostas_questoes
        WHERE usuario_id = %s
        ORDER BY
            questao_numero,
            data_resposta DESC
    """, (
        usuario_id,
    ))

    respostas = cursor.fetchall()

    conexao.close()

    agora = datetime.now()

    questoes_disponiveis = []
    questoes_bloqueadas = []

    # =====================================================
    # MAPEAR A ÚLTIMA RESPOSTA DE CADA QUESTÃO
    # =====================================================

    respostas_por_questao = {}

    for resposta in respostas:

        numero = resposta["questao_numero"]

        respostas_por_questao[numero] = (
            resposta["proxima_tentativa"]
        )

    # =====================================================
    # CLASSIFICAR AS 50 QUESTÕES
    # =====================================================

    for numero in range(1, total_questoes + 1):

        proxima_tentativa = (
            respostas_por_questao.get(numero)
        )

        # -------------------------------------------------
        # NUNCA RESPONDIDA
        # -------------------------------------------------

        if proxima_tentativa is None:

            questoes_disponiveis.append(numero)

            continue

        # -------------------------------------------------
        # VERIFICAR SE O BLOQUEIO JÁ TERMINOU
        # -------------------------------------------------

        if isinstance(
            proxima_tentativa,
            str
        ):

            proxima_tentativa = (
                datetime.fromisoformat(
                    proxima_tentativa
                )
            )

        if proxima_tentativa.tzinfo is not None:

            agora_com_fuso = datetime.now(
                proxima_tentativa.tzinfo
            )

        else:

            agora_com_fuso = agora

        # -------------------------------------------------
        # DISPONÍVEL NOVAMENTE
        # -------------------------------------------------

        if agora_com_fuso >= proxima_tentativa:

            questoes_disponiveis.append(numero)

        # -------------------------------------------------
        # AINDA BLOQUEADA
        # -------------------------------------------------

        else:

            questoes_bloqueadas.append(numero)

    # =====================================================
    # DISPONÍVEIS PRIMEIRO
    # BLOQUEADAS NO FINAL
    # =====================================================

    return (
        questoes_disponiveis
        + questoes_bloqueadas
    )

def calcular_intervalo_revisao(
    correta,
    ultima_resposta
):

    # =============================================
    # ERRO
    # =============================================

    if not correta:

        return 1

    # =============================================
    # PRIMEIRO ACERTO
    # =============================================

    if not ultima_resposta:

        return 3

    ultimo_intervalo = (
        ultima_resposta["intervalo_revisao"]
    )

    # =============================================
    # PROGRESSÃO
    # =============================================

    if ultimo_intervalo < 3:

        return 3

    if ultimo_intervalo < 7:

        return 7

    if ultimo_intervalo < 14:

        return 14

    return 30

def obter_numero_tentativa(
    usuario_id,
    questao_numero
):

    conexao = conectar()

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            tentativa
        FROM respostas_questoes
        WHERE usuario_id = %s
        AND questao_numero = %s
        ORDER BY data_resposta DESC
        LIMIT 1
    """, (
        usuario_id,
        questao_numero
    ))

    resultado = cursor.fetchone()

    conexao.close()

    if not resultado:
        return 1

    return resultado["tentativa"] + 1

def obter_questoes_para_revisao(usuario_id):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT ON (questao_numero)
            questao_numero,
            proxima_tentativa,
            tentativa,
            intervalo_revisao,
            correta,
            data_resposta
        FROM respostas_questoes
        WHERE usuario_id = %s
        ORDER BY questao_numero, data_resposta DESC
    """, (usuario_id,))

    respostas = cursor.fetchall()
    conexao.close()

    agora = datetime.now()

    questoes_revisao = []

    for resposta in respostas:

        proxima_tentativa = resposta["proxima_tentativa"]

        if not proxima_tentativa:
            continue

        if isinstance(proxima_tentativa, str):
            proxima_tentativa = datetime.fromisoformat(
                proxima_tentativa
            )

        if proxima_tentativa.tzinfo is not None:
            agora_com_fuso = datetime.now(
                proxima_tentativa.tzinfo
            )
        else:
            agora_com_fuso = agora

        if agora_com_fuso >= proxima_tentativa:
            questoes_revisao.append(resposta)

    return questoes_revisao

def obter_questoes_filtradas(
    area=None,
    dificuldade=None,
    competencia=None,
    habilidade=None,
    lingua=None
):

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    if area:
        questoes = [
            questao
            for questao in questoes
            if questao.get("area") == area
        ]

    if dificuldade:
        questoes = [
            questao
            for questao in questoes
            if questao.get("dificuldade") == dificuldade
        ]

    if competencia:
        questoes = [
            questao
            for questao in questoes
            if questao.get("competencia") == competencia
        ]

    if habilidade:
        questoes = [
            questao
            for questao in questoes
            if questao.get("habilidade") == habilidade
        ]

    if lingua:
        questoes = [
            questao
            for questao in questoes
            if questao.get("lingua") == lingua
        ]

    return questoes

def obter_areas_questoes():
    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    areas = sorted({
        questao["area"]
        for questao in questoes
        if questao.get("area")
    })

    return areas

def obter_dificuldades_questoes():

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    dificuldades = sorted({
        questao["dificuldade"]
        for questao in questoes
        if questao.get("dificuldade")
    })

    return dificuldades

def obter_competencias_questoes():

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    competencias = sorted({
        questao["competencia"]
        for questao in questoes
        if questao.get("competencia")
    })

    return competencias

def obter_habilidades_questoes():

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    habilidades = sorted({
        questao["habilidade"]
        for questao in questoes
        if questao.get("habilidade")
    })

    return habilidades

def obter_linguas_questoes():

    with open(
        "dados/questoes/questoes.json",
        "r",
        encoding="utf-8"
    ) as arquivo:
        questoes = json.load(arquivo)

    linguas = sorted({
        questao["lingua"]
        for questao in questoes
        if questao.get("lingua")
    })

    return linguas