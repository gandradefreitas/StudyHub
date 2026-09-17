from datetime import datetime
from database.conexao import conectar


def registrar_resposta_questao(
    usuario_id,
    questao_numero,
    resposta,
    correta,
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
            data_resposta,
            proxima_tentativa
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        usuario_id,
        questao_numero,
        resposta,
        correta,
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