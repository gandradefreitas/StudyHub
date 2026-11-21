from time import time

from database.conexao import conectar

# Limite de tempo creditado se a aba fechar sem conseguir enviar a pausa.
JANELA_ATIVA = 10


def obter_tentativa(conexao, usuario_id, instituicao):
    return conexao.execute("""
        SELECT * FROM redacoes_surpresa
        WHERE usuario_id = %s AND instituicao = %s
        FOR UPDATE
    """, (usuario_id, instituicao)).fetchone()


def estado_atual(tentativa, limite, acao, texto, titulo):
    agora = time()
    segundos = tentativa["segundos"]
    inicio = tentativa["ativo_desde"]
    if inicio is not None:
        segundos = min(limite, segundos + min(JANELA_ATIVA, max(0, agora - inicio)))

    if tentativa["segundos"] >= limite:
        texto, titulo = tentativa["texto"], tentativa["titulo"]
    return {
        "segundos": segundos,
        "ativo_desde": agora if acao == "ativo" and segundos < limite else None,
        "texto": texto,
        "titulo": titulo,
    }


def gravar_estado(conexao, usuario_id, instituicao, estado):
    conexao.execute("""
        UPDATE redacoes_surpresa
        SET segundos = %(segundos)s, ativo_desde = %(ativo_desde)s,
            texto = %(texto)s, titulo = %(titulo)s
        WHERE usuario_id = %(usuario_id)s AND instituicao = %(instituicao)s
    """, dict(estado, usuario_id=usuario_id, instituicao=instituicao))


def avancar_surpresa(conexao, usuario_id, instituicao):
    conexao.execute("""
        UPDATE redacoes_surpresa
        SET rodada = rodada + 1, segundos = 0, ativo_desde = NULL,
            texto = '', titulo = '', chave = NULL, revisao = 0
        WHERE usuario_id = %s AND instituicao = %s
    """, (usuario_id, instituicao))


def preparar_tentativa(usuario_id, instituicao, limite, chave):
    with conectar() as conexao:
        conexao.execute("""
            INSERT INTO redacoes_surpresa (usuario_id, instituicao)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (usuario_id, instituicao))
        tentativa = obter_tentativa(conexao, usuario_id, instituicao)
        estado = estado_atual(tentativa, limite, "pausar", tentativa["texto"], tentativa["titulo"])
        gravar_estado(conexao, usuario_id, instituicao, estado)
        conexao.execute("""
            UPDATE redacoes_surpresa SET chave = %s
            WHERE usuario_id = %s AND instituicao = %s
        """, (chave, usuario_id, instituicao))
    return dict(tentativa, **estado, chave=chave)
