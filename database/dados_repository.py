from database.conexao import conectar


def obter_dados_exportacao(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    usuario = cursor.fetchone()

    cursor.execute("""
        SELECT
            tema,
            meta_estudo,
            meta_questoes
        FROM configuracoes_usuario
        WHERE usuario_id = %s
    """, (usuario_id,))

    configuracoes = cursor.fetchone()

    cursor.execute("""
        SELECT
            inicio,
            fim,
            duracao,
            ativa
        FROM estudos
        WHERE usuario_id = %s
        ORDER BY inicio
    """, (usuario_id,))

    estudos = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            descricao,
            concluida,
            data_conclusao
        FROM tarefas
        WHERE usuario_id = %s
        ORDER BY id
    """, (usuario_id,))

    tarefas = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            data,
            texto
        FROM anotacoes
        WHERE usuario_id = %s
        ORDER BY data
    """, (usuario_id,))

    anotacoes = cursor.fetchall()

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
        ORDER BY data_realizacao
    """, (usuario_id,))

    resultados_provas = cursor.fetchall()

    cursor.execute("""
        SELECT
            prova_id,
            questao_numero,
            resposta,
            correta,
            data
        FROM respostas_provas
        WHERE usuario_id = %s
        ORDER BY data
    """, (usuario_id,))

    respostas_provas = cursor.fetchall()

    adicionais = {}
    consultas = {
        "respostas_questoes": """SELECT questao_numero, resposta, correta, tentativa,
            intervalo_revisao, data_resposta, proxima_tentativa FROM respostas_questoes
            WHERE usuario_id = %s ORDER BY id""",
        "resultados_questoes": """SELECT questao_numero, resposta_usuario, resposta_correta,
            correta, data_resposta, proxima_tentativa FROM resultados_questoes
            WHERE usuario_id = %s ORDER BY id""",
        "provas_discursivas": """SELECT id, instituicao, ano, fase, disciplina, status,
            nota_total, nota_maxima, data_inicio, data_finalizacao, resultado_correcao
            FROM tentativas_provas_discursivas WHERE usuario_id = %s ORDER BY id""",
        "respostas_discursivas": """SELECT r.tentativa_id, r.questao_numero, r.item_letra, r.resposta
            FROM respostas_discursivas r JOIN tentativas_provas_discursivas t ON t.id = r.tentativa_id
            WHERE t.usuario_id = %s ORDER BY r.id""",
        "experiencia": """SELECT origem, referencia, exp_decimos, registrado_em
            FROM experiencia_atividades WHERE usuario_id = %s ORDER BY registrado_em, origem, referencia""",
        "leituras_idiomas": """SELECT texto_id, palavras, concluido_em, acertos
            FROM leituras_idiomas WHERE usuario_id = %s ORDER BY concluido_em, texto_id""",
        "redacoes": """SELECT instituicao, ano, tema, titulo, texto, notas, nota, tempo_segundos, criado_em
            FROM redacoes WHERE usuario_id = %s ORDER BY id""",
        "rascunhos_redacoes_surpresa": """SELECT instituicao, rodada, segundos, texto, titulo
            FROM redacoes_surpresa WHERE usuario_id = %s AND chave IS NOT NULL ORDER BY instituicao""",
    }
    for nome, consulta in consultas.items():
        cursor.execute(consulta, (usuario_id,))
        adicionais[nome] = cursor.fetchall()

    conexao.close()

    return {
        "usuario": usuario,
        "configuracoes": configuracoes,
        "estudos": estudos,
        "tarefas": tarefas,
        "anotacoes": anotacoes,
        "resultados_provas": resultados_provas,
        "respostas_provas": respostas_provas,
        **adicionais,
    }


def limpar_historico(usuario_id):

    conexao = conectar()
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            DELETE FROM respostas_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM resultados_provas
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("DELETE FROM tentativas_provas_objetivas WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM respostas_questoes WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM resultados_questoes WHERE usuario_id = %s", (usuario_id,))
        cursor.execute("DELETE FROM leituras_idiomas WHERE usuario_id = %s", (usuario_id,))

        # As respostas discursivas são removidas pela chave estrangeira.
        cursor.execute("""
            DELETE FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM redacoes_surpresa
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM redacoes
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM estudos
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM anotacoes
            WHERE usuario_id = %s
        """, (usuario_id,))

        cursor.execute("""
            DELETE FROM tarefas
            WHERE usuario_id = %s
        """, (usuario_id,))

        # EXP, avisos de nível e molduras são conquistas da conta.
        conexao.commit()

        return True

    except Exception:

        conexao.rollback()

        return False

    finally:

        conexao.close()
