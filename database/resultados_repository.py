from utils.horario import horario_studyhub

from database.conexao import conectar
from database.experiencia_repository import registrar_experiencia
from services.experiencia_service import exp_resposta_prova
from database.provas_objetivas_repository import TentativaObjetivaEncerrada
from database.tempo_provas_escritas import obter_duracao_provas_escritas_por_dia
from services.provas_service import obter_prova, listar_provas


def salvar_resultado(resultado):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""

            INSERT INTO resultados_provas
            (
                usuario_id,
                prova_id,
                acertos,
                erros,
                nao_respondidas,
                total,
                tempo_gasto,
                porcentagem
            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

            RETURNING id

        """, (
            resultado["usuario_id"],
            resultado["prova_id"],
            resultado["acertos"],
            resultado["erros"],
            resultado["nao_respondidas"],
            resultado["total"],
            resultado["tempo_gasto"],
            resultado["porcentagem"]
        ))

        resultado_id = cursor.fetchone()["id"]

        conexao.commit()

        return resultado_id

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()


def formatar_data_realizacao(data):
    return horario_studyhub(data).strftime("%d/%m/%Y às %H:%M")


def listar_resultados_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""

        SELECT
            id,
            prova_id,
            acertos,
            erros,
            nao_respondidas,
            total,
            tempo_gasto,
            porcentagem,
            data_realizacao
        
        FROM resultados_provas
        
        WHERE usuario_id = %s
        
        ORDER BY data_realizacao DESC

    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    provas = listar_provas()

    historico = []

    for resultado in resultados:

        prova = next(
            (
                prova
                for prova in provas
                if prova["id"] == resultado["prova_id"]
            ),
            None
        )

        historico.append({

            "id": resultado["id"],

            "prova_id":
                resultado["prova_id"],

            "data_realizacao":
                formatar_data_realizacao(
                    resultado["data_realizacao"]
                ),

            "_data_ordem": resultado["data_realizacao"],

            "prova":
                (
                    f'{prova["nome"]} — {prova["dia"]}'
                    if prova
                    else "Prova não encontrada"
                ),

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
                resultado["porcentagem"]
        })

    return historico


def obter_resultados_por_data(usuario_id, data):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            acertos,
            erros,
            nao_respondidas,
            total,
            tempo_gasto,
            porcentagem,
            data_realizacao

        FROM resultados_provas

        WHERE usuario_id = %s

        AND data_realizacao::date = %s

        ORDER BY data_realizacao
    """, (
        usuario_id,
        data
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados


def obter_resultados_por_mes(usuario_id, ano, mes):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            data_realizacao::date AS data
        FROM resultados_provas
        WHERE usuario_id = %s
        AND EXTRACT(YEAR FROM data_realizacao) = %s
        AND EXTRACT(MONTH FROM data_realizacao) = %s
        GROUP BY data_realizacao::date
        ORDER BY data_realizacao::date
    """, (
        usuario_id,
        ano,
        mes
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados


def salvar_respostas_prova(
    usuario_id,
    prova_id,
    resultado_id,
    questoes,
    respostas
):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        for questao in questoes:

            chave_questao = str(
                questao.numero
            )

            # Não salva questões que ficaram em branco.
            if chave_questao not in respostas:
                continue

            resposta_usuario = respostas[
                chave_questao
            ]

            # Normaliza a resposta para inteiro.
            resposta_usuario = int(
                resposta_usuario
            )

            correta = (
                1
                if resposta_usuario == questao.resposta
                else 0
            )

            cursor.execute("""

                INSERT INTO respostas_provas
                (
                    usuario_id,
                    prova_id,
                    resultado_id,
                    questao_numero,
                    resposta,
                    correta
                )

                VALUES (%s, %s, %s, %s, %s, %s)

            """, (
                usuario_id,
                prova_id,
                resultado_id,
                questao.numero,
                resposta_usuario,
                correta
            ))

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()

def obter_respostas_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            resposta,
            correta
        FROM respostas_provas
        WHERE usuario_id = %s
        ORDER BY data
    """, (usuario_id,))

    respostas = cursor.fetchall()

    conexao.close()

    return respostas


def obter_resumo_usuario(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    # =====================================================
    # RESUMO DAS PROVAS
    # =====================================================

    cursor.execute("""
        SELECT
            COUNT(*) AS provas,

            COALESCE(SUM(acertos), 0) AS acertos_provas,

            COALESCE(SUM(erros), 0) AS erros_provas,

            COALESCE(SUM(nao_respondidas), 0) AS nao_respondidas

        FROM resultados_provas

        WHERE usuario_id = %s
    """, (usuario_id,))

    resultado_provas = cursor.fetchone()

    # =====================================================
    # QUESTÕES DO MÓDULO DE ESTUDOS
    # =====================================================

    cursor.execute("""
        SELECT
            COUNT(*) AS questoes_estudos,

            COALESCE(SUM(correta), 0) AS acertos_estudos

        FROM respostas_questoes

        WHERE usuario_id = %s
    """, (usuario_id,))

    resultado_estudos = cursor.fetchone()

    # =====================================================
    # SOMAR ACERTOS E ERROS
    # =====================================================

    acertos = (
        resultado_provas["acertos_provas"]
        + resultado_estudos["acertos_estudos"]
    )

    erros_provas = (
        resultado_provas["erros_provas"]
    )

    questoes_estudos = (
        resultado_estudos["questoes_estudos"]
    )

    # Nas questões de estudos:
    # cada resposta registrada é uma questão resolvida.
    # Portanto, as que não foram acertadas são erros.

    erros_estudos = (
        questoes_estudos
        - resultado_estudos["acertos_estudos"]
    )

    erros = (
        erros_provas
        + erros_estudos
    )

    # =====================================================
    # QUESTÕES REALMENTE RESOLVIDAS
    # =====================================================

    questoes = (
        acertos
        + erros
    )

    # =====================================================
    # QUESTÕES EM BRANCO
    # =====================================================

    nao_respondidas = (
        resultado_provas["nao_respondidas"]
    )

    conexao.close()

    return {

        "provas":
            resultado_provas["provas"],

        "questoes":
            questoes,

        "acertos":
            acertos,

        "erros":
            erros,

        "nao_respondidas":
            nao_respondidas
    }


def obter_desempenho_por_area(usuario_id, *, por_prova=False):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            correta
        FROM respostas_provas
        WHERE usuario_id = %s
    """, (usuario_id,))

    respostas = cursor.fetchall()

    conexao.close()

    desempenho = {}
    provas_indexadas = {}
    for resposta in respostas:
        prova_id = resposta["prova_id"]
        if prova_id not in provas_indexadas:
            prova = obter_prova(prova_id)
            provas_indexadas[prova_id] = (
                (prova.tipo, {questao.numero: questao for questao in prova.questoes})
                if prova else (None, {})
            )
        tipo, questoes = provas_indexadas[prova_id]
        questao = questoes.get(resposta["questao_numero"])
        correta = resposta["correta"]

        if questao is None:
            continue

        area = questao.area
        if por_prova:
            area = (tipo, "Matemática" if area == "Matematica" else area)

        if area not in desempenho:

            desempenho[area] = {

                "questoes": 0,

                "acertos": 0,

                "erros": 0
            }

        desempenho[area]["questoes"] += 1

        if correta:

            desempenho[area]["acertos"] += 1

        else:

            desempenho[area]["erros"] += 1

    for area in desempenho:

        total = desempenho[area]["questoes"]

        desempenho[area]["porcentagem"] = round(
            (
                desempenho[area]["acertos"]
                / total
            ) * 100,
            1
        )

    return desempenho


def obter_provas_realizadas(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT DISTINCT prova_id
        FROM resultados_provas
        WHERE usuario_id = %s
    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados


def obter_segundos_provas(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = %s
    """, (usuario_id,))

    resultados = cursor.fetchall()

    conexao.close()

    total_segundos = 0

    for resultado in resultados:

        tempo = resultado["tempo_gasto"]

        if not tempo:
            continue

        horas, minutos, segundos = map(
            int,
            tempo.split(":")
        )

        total_segundos += (
            horas * 3600
            + minutos * 60
            + segundos
        )

    return total_segundos + sum(
        dia["duracao"] for dia in obter_duracao_provas_escritas_por_dia(usuario_id)
    )


def obter_provas_por_periodo(
    usuario_id,
    data_inicio,
    data_fim
):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            data_realizacao::date AS data,
            tempo_gasto
        FROM resultados_provas
        WHERE usuario_id = %s
        AND data_realizacao::date BETWEEN %s AND %s
        ORDER BY data_realizacao
    """, (
        usuario_id,
        data_inicio,
        data_fim
    ))

    resultados = cursor.fetchall()

    conexao.close()

    return resultados


def converter_tempo_para_segundos(tempo):

    if not tempo:
        return 0

    horas, minutos, segundos = map(
        int,
        tempo.split(":")
    )

    return (
        horas * 3600
        + minutos * 60
        + segundos
    )

def obter_resultado_por_id(resultado_id, usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                usuario_id,
                prova_id,
                acertos,
                erros,
                nao_respondidas,
                total,
                tempo_gasto,
                porcentagem,
                data_realizacao

            FROM resultados_provas

            WHERE id = %s
              AND usuario_id = %s

        """, (
            resultado_id,
            usuario_id
        ))

        return cursor.fetchone()

    finally:

        cursor.close()
        conexao.close()

def listar_acertos_por_tentativa(usuario_id):
    with conectar() as conexao:
        return conexao.execute(
            """
            SELECT resultado_id, questao_numero
            FROM respostas_provas
            WHERE usuario_id = %s AND resultado_id IS NOT NULL AND correta = 1
            """,
            (usuario_id,),
        ).fetchall()


def obter_respostas_por_resultado(resultado_id, usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            SELECT
                questao_numero,
                resposta,
                correta

            FROM respostas_provas

            WHERE resultado_id = %s
              AND usuario_id = %s

            ORDER BY questao_numero

        """, (
            resultado_id,
            usuario_id
        ))

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()


def salvar_resultado_com_respostas(
    resultado,
    questoes,
    respostas,
    *,
    tentativa_id=None,
):
    """
    Salva o resultado de uma prova objetiva e suas respostas
    em uma única transação.

    Se ocorrer qualquer erro, todas as alterações são revertidas.
    """

    conexao = conectar()
    cursor = None

    try:
        cursor = conexao.cursor()
        if tentativa_id is not None:
            cursor.execute("""
                SELECT id FROM tentativas_provas_objetivas
                WHERE usuario_id = %s AND prova_id = %s AND id = %s AND resultado_id IS NULL
                FOR UPDATE
            """, (resultado["usuario_id"], resultado["prova_id"], tentativa_id))
            if cursor.fetchone() is None:
                raise TentativaObjetivaEncerrada("Esta tentativa não está mais aberta para esta conta.")

        # ------------------------------------------------
        # 1. VALIDA OS DADOS BÁSICOS
        # ------------------------------------------------

        if not isinstance(respostas, dict):
            raise ValueError("Formato de respostas inválido.")

        if not questoes:
            raise ValueError("A prova não possui questões.")

        numeros = [
            questao.numero
            for questao in questoes
        ]

        if len(numeros) != len(set(numeros)):
            raise ValueError("Existem questões duplicadas.")

        total = len(questoes)

        if resultado["total"] != total:
            raise ValueError(
                "O total informado não corresponde às questões."
            )

        # ------------------------------------------------
        # 2. VALIDA E PROCESSA AS RESPOSTAS
        # ------------------------------------------------

        acertos = 0
        erros = 0
        nao_respondidas = 0
        respostas_processadas = []

        for questao in questoes:

            resposta_usuario = respostas.get(
                str(questao.numero)
            )

            if resposta_usuario is None or resposta_usuario == "":
                nao_respondidas += 1
                continue

            # Não aceita booleanos como alternativas numéricas.
            if isinstance(resposta_usuario, bool):
                raise ValueError("Alternativa inválida.")

            try:
                resposta_usuario = int(resposta_usuario)

            except (TypeError, ValueError):
                raise ValueError("Alternativa inválida.")

            if not (
                0 <= resposta_usuario < len(questao.alternativas)
            ):
                raise ValueError("Alternativa fora dos limites.")

            correta = int(
                resposta_usuario == questao.resposta
            )

            if correta:
                acertos += 1
            else:
                erros += 1

            respostas_processadas.append(
                (
                    resultado["usuario_id"],
                    resultado["prova_id"],
                    questao.numero,
                    resposta_usuario,
                    correta,
                )
            )

        # ------------------------------------------------
        # 3. CONFERE A CONSISTÊNCIA DO RESULTADO
        # ------------------------------------------------

        if (
            resultado["acertos"] != acertos
            or resultado["erros"] != erros
            or resultado["nao_respondidas"] != nao_respondidas
        ):
            raise ValueError(
                "Os totais do resultado não correspondem às respostas."
            )

        # ------------------------------------------------
        # 4. INSERE O RESULTADO
        # ------------------------------------------------

        cursor.execute(
            """
            INSERT INTO resultados_provas (
                usuario_id,
                prova_id,
                acertos,
                erros,
                nao_respondidas,
                total,
                tempo_gasto,
                porcentagem
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                resultado["usuario_id"],
                resultado["prova_id"],
                acertos,
                erros,
                nao_respondidas,
                total,
                resultado["tempo_gasto"],
                resultado["porcentagem"],
            ),
        )

        resultado_salvo = cursor.fetchone()

        if resultado_salvo is None:
            raise RuntimeError(
                "O banco não retornou o ID do resultado."
            )

        resultado_id = (
            resultado_salvo["id"]
            if isinstance(resultado_salvo, dict)
            else resultado_salvo[0]
        )

        # ------------------------------------------------
        # 5. INSERE AS RESPOSTAS
        # ------------------------------------------------

        for resposta in respostas_processadas:

            usuario_id, prova_id, numero, alternativa, correta = resposta

            cursor.execute(
                """
                INSERT INTO respostas_provas (
                    usuario_id,
                    prova_id,
                    resultado_id,
                    questao_numero,
                    resposta,
                    correta
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    usuario_id,
                    prova_id,
                    resultado_id,
                    numero,
                    alternativa,
                    correta,
                ),
            )

        # ------------------------------------------------
        # 6. CONFIRMA A TRANSAÇÃO
        # ------------------------------------------------

        if tentativa_id is not None:
            cursor.execute("""
                UPDATE tentativas_provas_objetivas SET resultado_id = %s WHERE id = %s
            """, (resultado_id, tentativa_id))
        for usuario_id, prova_id, numero, _, correta in sorted(respostas_processadas):
            registrar_experiencia(
                conexao, usuario_id, "prova_objetiva", f"{prova_id}:{numero}", exp_resposta_prova(correta),
            )

        conexao.commit()

        return resultado_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()
