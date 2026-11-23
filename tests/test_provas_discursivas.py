import pytest

from tests.app_de_teste import app
from controllers.prova_discursiva_controller import (
    carregar_prova_ita_segunda_fase,
    obter_campos_permitidos,
)


@pytest.fixture
def cliente():
    configuracao_original = {
        "TESTING": app.config["TESTING"],
        "WTF_CSRF_ENABLED": app.config.get(
            "WTF_CSRF_ENABLED", True
        ),
    }

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    try:
        with app.test_client() as cliente:
            yield cliente
    finally:
        app.config.update(configuracao_original)


def test_aplicacao_flask_pode_ser_importada():
    assert app is not None


def test_acesso_a_prova_sem_login_redireciona(cliente):
    resposta = cliente.get(
        "/provas/ita/2025/segunda-fase",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_salvar_respostas_sem_login_redireciona(cliente):
    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_finalizar_prova_sem_login_redireciona(cliente):
    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={},
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_csrf_esta_habilitado_na_aplicacao():
    from flask_wtf.csrf import CSRFProtect

    assert any(
        isinstance(extensao, CSRFProtect)
        for extensao in app.extensions.values()
    )


def test_usuario_nao_pode_salvar_na_tentativa_de_outro(
    cliente,
    dados_discursivos,
):
    usuario_a, _ = dados_discursivos["usuarios"]
    _, tentativa_b = dados_discursivos["tentativas"]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_a
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_b),
            "resposta_1_1": "Resposta nÃ£o autorizada",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    from database.conexao import conectar

    conexao = conectar()

    try:
        resultado = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_b,),
        ).fetchone()

        assert resultado["total"] == 0
    finally:
        conexao.close()


def test_usuario_pode_salvar_na_propria_tentativa(
    cliente,
    dados_discursivos,
):
    usuario_a = dados_discursivos["usuarios"][0]
    tentativa_a = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_a
        sessao["nome"] = "Usuario Teste 1"

    prova = carregar_prova_ita_segunda_fase()
    campos = obter_campos_permitidos(prova)

    assert campos, (
        "A prova nÃ£o possui campos de resposta configurados."
    )

    campo_valido = sorted(campos)[0]

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_a),
            campo_valido: "Resposta automatizada de teste",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    from database.conexao import conectar

    conexao = conectar()

    try:
        resultado = conexao.execute(
            """
            SELECT resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_a,),
        ).fetchone()

        assert resultado is not None
        assert resultado["resposta"] == (
            "Resposta automatizada de teste"
        )
    finally:
        conexao.close()


def test_tentativa_finalizada_nao_aceita_respostas(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    # Finaliza a tentativa diretamente no banco de testes.
    conexao = conectar()

    try:
        conexao.execute(
            """
            UPDATE tentativas_provas_discursivas
            SET status = 'finalizada'
            WHERE id = %s
            """,
            (tentativa_id,),
        )
        conexao.commit()
    finally:
        conexao.close()

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_id),
            "resposta_1_1": "Tentativa de alteraÃ§Ã£o",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT status
            FROM tentativas_provas_discursivas
            WHERE id = %s
            """,
            (tentativa_id,),
        ).fetchone()

        assert registro["status"] == "finalizada"

        total = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_id,),
        ).fetchone()

        assert total["total"] == 0
    finally:
        conexao.close()


def test_campo_de_resposta_invalido_e_rejeitado(
    cliente,
    dados_discursivos,
):
    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_id),
            "resposta_999_999": "Campo que nÃ£o existe na prova",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    from database.conexao import conectar

    conexao = conectar()

    try:
        total = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_id,),
        ).fetchone()

        assert total["total"] == 0
    finally:
        conexao.close()


def test_resposta_acima_do_limite_e_rejeitada(
    cliente,
    dados_discursivos,
):
    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_id),
            "resposta_1_1": "A" * 20001,
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    from database.conexao import conectar

    conexao = conectar()

    try:
        total = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_id,),
        ).fetchone()

        assert total["total"] == 0
    finally:
        conexao.close()


def test_salvar_respostas_sem_token_csrf_e_rejeitado(
    cliente,
    dados_discursivos,
):
    from flask_wtf.csrf import generate_csrf

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    # Reativa a proteÃ§Ã£o CSRF para esta requisiÃ§Ã£o.
    csrf_original = cliente.application.config.get(
        "WTF_CSRF_ENABLED",
        True,
    )

    cliente.application.config["WTF_CSRF_ENABLED"] = True

    try:
        resposta = cliente.post(
            "/provas/ita/2025/segunda-fase/matematica/salvar",
            data={
                "tentativa_id": str(tentativa_id),
                "resposta_1_1": "Resposta sem token CSRF",
            },
            follow_redirects=False,
        )

        assert resposta.status_code == 400

    finally:
        cliente.application.config["WTF_CSRF_ENABLED"] = csrf_original


def test_finalizar_prova_sem_token_csrf_e_rejeitado(
    cliente,
    dados_discursivos,
):
    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    csrf_original = cliente.application.config.get(
        "WTF_CSRF_ENABLED",
        True,
    )

    cliente.application.config["WTF_CSRF_ENABLED"] = True

    try:
        resposta = cliente.post(
            "/provas/ita/2025/segunda-fase/matematica/finalizar",
            data={
                "tentativa_id": str(tentativa_id),
            },
            follow_redirects=False,
        )

        assert resposta.status_code == 400

    finally:
        cliente.application.config["WTF_CSRF_ENABLED"] = csrf_original


def test_usuario_pode_finalizar_a_propria_tentativa(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={
            "tentativa_id": str(tentativa_id),
        },
        follow_redirects=False,
    )

    # Confirma o redirecionamento HTTP.
    assert resposta.status_code == 302

    # Confirma que o destino é o resultado da tentativa finalizada.
    destino_esperado = (
        f"/provas/ita/2025/segunda-fase/resultado/{tentativa_id}"
    )

    assert resposta.headers["Location"].endswith(destino_esperado)

    # Confirma que a tentativa foi finalizada no banco de dados.
    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT status, data_finalizacao
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
            """,
            (tentativa_id, usuario_id),
        ).fetchone()

        assert registro is not None
        assert registro["status"] == "finalizada"
        assert registro["data_finalizacao"] is not None

    finally:
        conexao.close()


def test_usuario_nao_pode_finalizar_tentativa_de_outro(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_a, usuario_b = dados_discursivos["usuarios"]
    tentativa_a, tentativa_b = dados_discursivos["tentativas"]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_a
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={"tentativa_id": str(tentativa_b)},
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT usuario_id, status
            FROM tentativas_provas_discursivas
            WHERE id = %s
            """,
            (tentativa_b,),
        ).fetchone()

        assert registro is not None
        assert registro["usuario_id"] == usuario_b
        assert registro["status"] == "em_andamento"

    finally:
        conexao.close()


def test_tentativa_finalizada_nao_pode_ser_finalizada_novamente(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    conexao = conectar()

    try:
        conexao.execute(
            """
            UPDATE tentativas_provas_discursivas
            SET status = 'finalizada',
                data_finalizacao = CURRENT_TIMESTAMP
            WHERE id = %s
              AND usuario_id = %s
            """,
            (tentativa_id, usuario_id),
        )
        conexao.commit()

    finally:
        conexao.close()

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={"tentativa_id": str(tentativa_id)},
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT status
            FROM tentativas_provas_discursivas
            WHERE id = %s
            """,
            (tentativa_id,),
        ).fetchone()

        assert registro["status"] == "finalizada"

    finally:
        conexao.close()


def test_salvar_resposta_novamente_atualiza_registro(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar
    from app import carregar_prova_ita_segunda_fase, obter_campos_permitidos

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    prova = carregar_prova_ita_segunda_fase()
    campos = obter_campos_permitidos(prova)
    campo = sorted(campos)[0]

    for texto in ("Primeira versÃ£o", "Segunda versÃ£o"):
        resposta = cliente.post(
            "/provas/ita/2025/segunda-fase/matematica/salvar",
            data={
                "tentativa_id": str(tentativa_id),
                campo: texto,
            },
            follow_redirects=False,
        )
        assert resposta.status_code == 302

    conexao = conectar()

    try:
        registros = conexao.execute(
            """
            SELECT resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_id,),
        ).fetchall()

        assert len(registros) == 1
        assert registros[0]["resposta"] == "Segunda versÃ£o"

    finally:
        conexao.close()



def test_salvar_item_nao_apaga_resposta_de_outro_item(
    cliente,
    dados_discursivos,
):
    from controllers.prova_discursiva_controller import salvar_respostas_tentativa
    from models.questao_discursiva import (
        ProvaDiscursiva,
        QuestaoDiscursiva,
        ItemDiscursivo,
    )
    from database.conexao import conectar

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    itens = [
        ItemDiscursivo(
            letra="a",
            enunciado="Primeiro item de teste",
            valor=5,
            resposta_esperada="Resposta A",
            resolucao_referencia="ResoluÃ§Ã£o A",
            criterios_correcao=[],
        ),
        ItemDiscursivo(
            letra="b",
            enunciado="Segundo item de teste",
            valor=5,
            resposta_esperada="Resposta B",
            resolucao_referencia="ResoluÃ§Ã£o B",
            criterios_correcao=[],
        ),
    ]

    prova = ProvaDiscursiva(
        instituicao="ITA",
        ano=2025,
        fase="Segunda Fase",
        tipo="discursiva",
        tempo="A definir",
        convencoes=[],
        questoes=[
            QuestaoDiscursiva(
                numero=1,
                area="MatemÃ¡tica",
                enunciado="QuestÃ£o fictÃ­cia para teste",
                imagem=None,
                itens=itens,
            )
        ],
    )

    # Salva as duas respostas.
    salvar_respostas_tentativa(
        tentativa_id,
        usuario_id,
        prova,
        {
            "resposta_1_1": "Resposta original A",
            "resposta_1_2": "Resposta original B",
        },
    )

    # Atualiza apenas a primeira resposta.
    salvar_respostas_tentativa(
        tentativa_id,
        usuario_id,
        prova,
        {
            "resposta_1_1": "Resposta atualizada A",
        },
    )

    conexao = conectar()

    try:
        registros = conexao.execute(
            """
            SELECT questao_numero, item_letra, resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            ORDER BY item_letra
            """,
            (tentativa_id,),
        ).fetchall()

        assert len(registros) == 2

        respostas = {
            registro["item_letra"]: registro["resposta"]
            for registro in registros
        }

        assert respostas["a"] == "Resposta atualizada A"
        assert respostas["b"] == "Resposta original B"

    finally:
        conexao.close()




def test_campo_invalido_impede_salvamento_parcial(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar
    from app import carregar_prova_ita_segunda_fase, obter_campos_permitidos

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    prova = carregar_prova_ita_segunda_fase()
    campo_valido = sorted(obter_campos_permitidos(prova))[0]

    resposta = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_id),
            campo_valido: "Esta resposta nÃ£o deve ser salva",
            "resposta_999_999": "Campo invÃ¡lido",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    conexao = conectar()

    try:
        registros = conexao.execute(
            """
            SELECT resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_id,),
        ).fetchall()

        assert registros == []

    finally:
        conexao.close()


def test_respostas_continuam_disponiveis_apos_finalizar(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar
    from database.respostas_discursivas_repository import obter_respostas
    from app import carregar_prova_ita_segunda_fase, obter_campos_permitidos

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    prova = carregar_prova_ita_segunda_fase()
    campo = sorted(obter_campos_permitidos(prova))[0]
    texto_resposta = "Resposta preservada apÃ³s a finalizaÃ§Ã£o"

    # Salva a resposta.
    resposta_salvamento = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_id),
            campo: texto_resposta,
        },
        follow_redirects=False,
    )

    assert resposta_salvamento.status_code == 302

    # Finaliza a tentativa.
    resposta_finalizacao = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={"tentativa_id": str(tentativa_id)},
        follow_redirects=False,
    )

    assert resposta_finalizacao.status_code == 302

    # Confirma que a resposta continua armazenada.
    respostas = obter_respostas(tentativa_id)

    assert len(respostas) == 1
    assert texto_resposta == next(iter(respostas.values()))

    # Confirma que a tentativa realmente foi finalizada.
    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT status
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
            """,
            (tentativa_id, usuario_id),
        ).fetchone()

        assert registro is not None
        assert registro["status"] == "finalizada"

    finally:
        conexao.close()


def test_nova_tentativa_apos_finalizar_preserva_resposta_anterior(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_antiga_id = dados_discursivos["tentativas"][0]
    texto_resposta = "Minha resolução preservada para consulta."

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    # Salva uma resposta na tentativa antiga.
    salvamento = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_antiga_id),
            "resposta_1_1": texto_resposta,
        },
    )

    assert salvamento.status_code == 302

    # Finaliza a tentativa antiga.
    finalizacao = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/finalizar",
        data={
            "tentativa_id": str(tentativa_antiga_id),
        },
    )

    assert finalizacao.status_code == 302

    # O limite diário permanece ativo até o dia seguinte.
    assert cliente.get("/provas/ita/2025/segunda-fase/matematica").status_code == 302
    with conectar() as conexao:
        conexao.execute(
            """
            UPDATE tentativas_provas_discursivas
            SET data_inicio = data_inicio - INTERVAL '1 day',
                data_finalizacao = data_finalizacao - INTERVAL '1 day'
            WHERE id = %s
            """,
            (tentativa_antiga_id,),
        )

    pagina = cliente.get(
        "/provas/ita/2025/segunda-fase/matematica"
    )

    assert pagina.status_code == 200

    # A nova tentativa deve permitir responder novamente.
    assert b'name="resposta_1_1"' in pagina.data
    assert b"Finalizar prova" in pagina.data

    # A resposta antiga não deve aparecer na nova tentativa.
    assert texto_resposta.encode() not in pagina.data

    conexao = conectar()

    try:
        # Confirma que a tentativa antiga continua finalizada
        # e que a resposta original não foi alterada.
        registro_antigo = conexao.execute(
            """
            SELECT
                t.status,
                r.resposta
            FROM tentativas_provas_discursivas AS t
            JOIN respostas_discursivas AS r
                ON r.tentativa_id = t.id
            WHERE t.id = %s
              AND t.usuario_id = %s
              AND r.questao_numero = 1
              AND r.item_letra IS NULL
            """,
            (tentativa_antiga_id, usuario_id),
        ).fetchone()

        assert registro_antigo is not None
        assert registro_antigo["status"] == "finalizada"
        assert registro_antigo["resposta"] == texto_resposta

        # Identifica a tentativa em andamento da mesma disciplina.
        tentativa_nova = conexao.execute(
            """
            SELECT id, status
            FROM tentativas_provas_discursivas
            WHERE usuario_id = %s
              AND instituicao = %s
              AND ano = %s
              AND fase = %s
              AND disciplina = %s
              AND status = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                usuario_id,
                "ITA",
                2025,
                "Segunda Fase",
                "Matemática",
                "em_andamento",
            ),
        ).fetchone()

        assert tentativa_nova is not None
        assert tentativa_nova["id"] != tentativa_antiga_id

        # A nova tentativa deve começar sem respostas.
        respostas_novas = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM respostas_discursivas
            WHERE tentativa_id = %s
            """,
            (tentativa_nova["id"],),
        ).fetchone()

        assert respostas_novas["total"] == 0

    finally:
        conexao.close()

    # Uma requisição manual não pode alterar a tentativa finalizada.
    tentativa_alteracao = cliente.post(
        "/provas/ita/2025/segunda-fase/matematica/salvar",
        data={
            "tentativa_id": str(tentativa_antiga_id),
            "resposta_1_1": "Tentativa de alteração indevida.",
        },
    )

    assert tentativa_alteracao.status_code == 302

    # Verifica novamente a integridade da resposta antiga.
    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
              AND questao_numero = 1
              AND item_letra IS NULL
            """,
            (tentativa_antiga_id,),
        ).fetchone()

        assert registro is not None
        assert registro["resposta"] == texto_resposta

    finally:
        conexao.close()


def test_pagina_sem_login_nao_exibe_prova_discursiva(cliente):
    resposta = cliente.get(
        "/provas/ita/2025/segunda-fase",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_usuario_nao_visualiza_respostas_de_outro_usuario(
    cliente,
    dados_discursivos,
):
    from database.conexao import conectar

    usuario_a, usuario_b = dados_discursivos["usuarios"]
    tentativa_a, tentativa_b = dados_discursivos["tentativas"]

    resposta_privada = "RESPOSTA_PRIVADA_USUARIO_A_92741"

    # Insere uma resposta exclusivamente na tentativa do usuÃ¡rio A.
    conexao = conectar()

    try:
        conexao.execute(
            """
            INSERT INTO respostas_discursivas (
                tentativa_id,
                questao_numero,
                item_letra,
                resposta
            )
            VALUES (%s, %s, %s, %s)
            """,
            (tentativa_a, 1, None, resposta_privada),
        )
        conexao.commit()

    finally:
        conexao.close()

    # Autentica como usuÃ¡rio B.
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_b
        sessao["nome"] = "Usuario Teste 2"

    pagina = cliente.get("/provas/ita/2025/segunda-fase")

    assert pagina.status_code == 200
    assert resposta_privada.encode() not in pagina.data

    # Confirma que o usuÃ¡rio B estÃ¡ vendo uma tentativa prÃ³pria.
    assert str(tentativa_a).encode() not in pagina.data

    # Confirma que a resposta privada continua armazenada para A.
    conexao = conectar()

    try:
        registro = conexao.execute(
            """
            SELECT resposta
            FROM respostas_discursivas
            WHERE tentativa_id = %s
              AND questao_numero = %s
              AND item_letra IS NULL
            """,
            (tentativa_a, 1),
        ).fetchone()

        assert registro is not None
        assert registro["resposta"] == resposta_privada

        # A tentativa apresentada a B deve ser a tentativa dele.
        tentativa_b_atual = conexao.execute(
            """
            SELECT id
            FROM tentativas_provas_discursivas
            WHERE id = %s
              AND usuario_id = %s
            """,
            (tentativa_b, usuario_b),
        ).fetchone()

        assert tentativa_b_atual is not None

    finally:
        conexao.close()


def test_resultado_discursivo_sem_login_redireciona(cliente):
    resposta = cliente.get(
        "/provas/ita/2025/segunda-fase/resultado/1",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_historico_discursivo_sem_login_redireciona(cliente):
    resposta = cliente.get(
        "/provas/ita/2025/segunda-fase/historico",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_usuario_nao_acessa_resultado_de_outro_usuario(
    cliente,
    dados_discursivos,
):
    usuario_a, _ = dados_discursivos["usuarios"]
    _, tentativa_b = dados_discursivos["tentativas"]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_a
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.get(
        f"/provas/ita/2025/segunda-fase/resultado/{tentativa_b}"
    )

    assert resposta.status_code == 404


def test_usuario_visualiza_proprio_resultado_discursivo(
    cliente,
    dados_discursivos,
):
    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    from database.conexao import conectar

    conexao = conectar()

    try:
        conexao.execute(
            """
            UPDATE tentativas_provas_discursivas
            SET status = 'finalizada',
                data_finalizacao = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (tentativa_id,),
        )

        conexao.execute(
            """
            INSERT INTO respostas_discursivas (
                tentativa_id,
                questao_numero,
                item_letra,
                resposta
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                tentativa_id,
                1,
                "a",
                "Resposta exclusiva do teste de resultado",
            ),
        )

        conexao.commit()

    finally:
        conexao.close()

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.get(
        f"/provas/ita/2025/segunda-fase/resultado/{tentativa_id}"
    )

    assert resposta.status_code == 200
    assert b"Resposta exclusiva do teste de resultado" in resposta.data
    assert b"Aguardando corre" in resposta.data


@pytest.mark.parametrize(
    ("status", "intervalo", "segundos", "tempo_historico"),
    [
        ("finalizada", 3661, 3661, "01:01:01"),
        ("corrigida", 18000, 14400, "04:00:00"),
        ("em_andamento", None, 0, "—"),
    ],
)
def test_tempo_discursivo_no_historico_menu_e_estatisticas(
    cliente, dados_discursivos, status, intervalo, segundos, tempo_historico
):
    from database.conexao import conectar
    from services.dashboard_service import carregar_dashboard

    usuario_id, outro_usuario = dados_discursivos["usuarios"]
    tentativa_id = dados_discursivos["tentativas"][0]

    with conectar() as conexao:
        data = conexao.execute(
            """
            UPDATE tentativas_provas_discursivas
            SET status = %s,
                data_inicio = LOCALTIMESTAMP - (%s * INTERVAL '1 second'),
                data_finalizacao = CASE WHEN %s THEN LOCALTIMESTAMP END
            WHERE id = %s
            RETURNING CURRENT_DATE AS data
            """,
            (status, intervalo or 600, intervalo is not None, tentativa_id),
        ).fetchone()["data"]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    historico = cliente.get("/provas/historico")
    assert historico.status_code == 200
    celula_tempo = historico.get_data(as_text=True).split('class="tempo-prova">', 1)[1]
    assert celula_tempo.split("</td>", 1)[0].strip() == tempo_historico

    dashboard = carregar_dashboard(usuario_id)
    assert dashboard["metas"]["estudo_atual"] == segundos
    assert carregar_dashboard(outro_usuario)["metas"]["estudo_atual"] == 0

    resumo = cliente.get("/estatisticas/resumo")
    assert resumo.status_code == 200
    assert resumo.json["horas_estudadas"] == segundos

    evolucao = cliente.get(f"/estatisticas/evolucao?ano={data.year}&mes={data.month}")
    assert evolucao.status_code == 200
    assert sum(dia["duracao"] for dia in evolucao.json) == segundos
    assert {"data": data.isoformat(), "duracao": segundos} in evolucao.json


def test_historico_discursivo_lista_tentativa_do_usuario(
    cliente,
    dados_discursivos,
):
    usuario_id = dados_discursivos["usuarios"][0]
    tentativa_id = dados_discursivos["tentativas"][0]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_id
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.get("/provas/historico")

    assert resposta.status_code == 200

    assert (
        f"/provas/ita/2025/segunda-fase/resultado/{tentativa_id}".encode()
        in resposta.data
    )


def test_historico_discursivo_nao_exibe_tentativas_de_outro_usuario(
    cliente,
    dados_discursivos,
):
    usuario_a = dados_discursivos["usuarios"][0]
    tentativa_b = dados_discursivos["tentativas"][1]

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario_a
        sessao["nome"] = "Usuario Teste 1"

    resposta = cliente.get("/provas/historico")

    assert resposta.status_code == 200

    assert (
        f"/provas/ita/2025/segunda-fase/resultado/{tentativa_b}".encode()
        not in resposta.data
    )



def test_grafico_menu_restringe_evolucao_a_sete_dias(cliente, dados_discursivos):
    from datetime import date, timedelta

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = dados_discursivos["usuarios"][0]

    resposta = cliente.get("/estatisticas/evolucao?dias=7")
    assert resposta.status_code == 200
    assert len(resposta.json) == 7
    assert date.fromisoformat(resposta.json[0]["data"]) == date.today() - timedelta(days=6)
    assert resposta.json[-1]["data"] == date.today().isoformat()
    assert cliente.get("/estatisticas/evolucao?dias=0").status_code == 400
    assert cliente.get("/estatisticas/evolucao?ano=0&mes=1").status_code == 400


def test_salvamento_ajax_confirma_antes_de_finalizar(cliente, dados_discursivos):
    usuario, outro = dados_discursivos["usuarios"]
    tentativa, tentativa_alheia = dados_discursivos["tentativas"]
    caminho = "/provas/ita/2025/segunda-fase/matematica"
    headers = {"X-Requested-With": "XMLHttpRequest"}
    assert cliente.post(caminho + "/salvar", headers=headers).status_code == 401
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario
    dados = {"tentativa_id": tentativa, "resposta_1_1": "Resposta do teste"}
    invalida = cliente.post(caminho + "/salvar", headers=headers,
                            data=dict(dados, tentativa_id=tentativa_alheia))
    assert invalida.status_code == 400
    assert invalida.json["status"] == "erro"
    salva = cliente.post(caminho + "/salvar", headers=headers, data=dados)
    assert salva.status_code == 200
    assert salva.json == {"status": "ok"}
    finaliza = cliente.post(caminho + "/finalizar", data=dados)
    assert finaliza.status_code == 302
    assert f"/resultado/{tentativa}" in finaliza.location


@pytest.mark.parametrize("disciplina", ["fisica", "quimica"])
def test_finaliza_tentativa_aberta_pela_pagina_da_disciplina(cliente, dados_discursivos, disciplina):
    import re

    from database.conexao import conectar

    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = dados_discursivos["usuarios"][0]
    caminho = f"/provas/ita/2025/segunda-fase/{disciplina}"
    prova = cliente.get(caminho)
    assert prova.status_code == 200
    tentativa = int(re.search(r'name="tentativa_id"\s+value="(\d+)"', prova.get_data(as_text=True))[1])
    campo = min(obter_campos_permitidos(carregar_prova_ita_segunda_fase(disciplina)))
    respostas = {"tentativa_id": tentativa, campo: "Resposta de teste"}
    salva = cliente.post(caminho + "/salvar", data=respostas, headers={"X-Requested-With": "XMLHttpRequest"})
    assert salva.status_code == 200
    assert salva.json == {"status": "ok"}
    finaliza = cliente.post(caminho + "/finalizar", data=respostas)
    assert finaliza.status_code == 302
    assert finaliza.location.endswith(f"/resultado/{tentativa}")
    with conectar() as conexao:
        registro = conexao.execute("""
            SELECT t.status, r.resposta
            FROM tentativas_provas_discursivas t
            JOIN respostas_discursivas r ON r.tentativa_id = t.id
            WHERE t.id = %s
        """, (tentativa,)).fetchone()
    assert registro == {"status": "finalizada", "resposta": "Resposta de teste"}


def test_resultado_provisorio_aparece_no_historico_e_no_backup(cliente, dados_discursivos):
    from database.conexao import conectar
    from database.respostas_discursivas_repository import (
        reivindicar_correcao_discursiva, salvar_resultado_correcao_discursiva,
    )

    usuario = dados_discursivos["usuarios"][0]
    tentativa = dados_discursivos["tentativas"][0]
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario
    with conectar() as conexao:
        conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET status = 'finalizada', disciplina = 'Física', data_finalizacao = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (tentativa,))
    assert reivindicar_correcao_discursiva(tentativa, usuario)
    assert not reivindicar_correcao_discursiva(tentativa, usuario)
    assert salvar_resultado_correcao_discursiva(
        tentativa, usuario,
        {"status": "provisoria", "nota_provisoria": 55, "nota_maxima": 100},
        "finalizada", None, 100,
    )
    historico = cliente.get("/provas/historico").get_data(as_text=True)
    assert "Correção provisória" in historico
    assert "55/100.0" in historico
    backup = cliente.get("/configuracoes/dados/exportar").json
    assert backup["provas_discursivas"][0]["resultado_correcao"]["nota_provisoria"] == 55
    assert {"leituras_idiomas", "redacoes", "respostas_discursivas"} <= backup.keys()
    pdf = cliente.get("/configuracoes/dados/exportar/pdf")
    assert pdf.status_code == 200
    assert pdf.data.startswith(b"%PDF")


def test_painel_e_estatisticas_separam_as_provas(cliente, dados_discursivos, monkeypatch):
    import app as modulo

    monkeypatch.setattr(modulo, "obter_desempenho_por_area", lambda _, **__: {
        ("ENEM", "Matemática"): {"questoes": 5, "acertos": 3},
        ("ITA", "Matemática"): {"questoes": 4, "acertos": 1},
    })
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = dados_discursivos["usuarios"][0]
    estatisticas = cliente.get("/estatisticas").get_data(as_text=True)
    assert 'id="desempenho-enem"' in estatisticas
    assert 'id="desempenho-ita"' in estatisticas
    assert 'value="3" max="5"' in estatisticas
    assert 'value="1" max="4"' in estatisticas
    assert "Desempenho Totais de Questões" in estatisticas
    assert "<dt>Resolvidas</dt><dd>9</dd>" in estatisticas
    assert "<dt>Acertos</dt><dd>4</dd>" in estatisticas
    assert "ENEM · Matemática · 60,0%" in estatisticas
    assert "ITA · Matemática · 25,0%" in estatisticas
    menu = cliente.get("/dashboard").get_data(as_text=True)
    assert "Prática e resultados" in menu
    tarefas = cliente.get("/tarefas").get_data(as_text=True)
    assert 'id="editor-tarefa"' in tarefas


def test_exportacoes_identificam_provas_ita_e_incluem_estatisticas(cliente, dados_discursivos, monkeypatch):
    from database.conexao import conectar
    from reportlab import rl_config

    usuario = dados_discursivos["usuarios"][0]
    with cliente.session_transaction() as sessao:
        sessao["usuario_id"] = usuario
    monkeypatch.setattr(rl_config, "pageCompression", 0)
    try:
        with conectar() as conexao:
            conexao.execute("""
                INSERT INTO resultados_provas
                    (usuario_id, prova_id, acertos, erros, tempo_gasto, nao_respondidas, total, porcentagem)
                VALUES (%s, 3, 13, 35, '00:02:33', 0, 48, 27.08),
                       (%s, 4, 2, 13, '00:00:35', 0, 15, 13.33)
            """, (usuario, usuario))

        backup = cliente.get("/configuracoes/dados/exportar").json
        assert [(item["prova_id"], item["instituicao"], item["prova"])
                for item in backup["resultados_provas"]] == [
            (3, "ITA", "ITA 2025 — Primeira Fase"),
            (4, "ITA", "ITA 2025 — Segunda Fase — Português"),
        ]
        estatisticas = backup["estatisticas"]
        assert estatisticas["evolucao_mensal"] == cliente.get("/estatisticas/evolucao").json
        assert estatisticas["tempo_total_segundos"] == 188
        assert "ITA" in estatisticas["desempenho_provas"]
        assert "dificuldade" in estatisticas["analise_questoes_praticadas"]
        pdf = cliente.get("/configuracoes/dados/exportar/pdf")
        assert pdf.status_code == 200
        assert b"ITA 2025" in pdf.data
        assert b"Primeira" in pdf.data
        assert b"Segunda" in pdf.data
        assert b"Prova 3" not in pdf.data
        assert b"Prova 4" not in pdf.data
    finally:
        with conectar() as conexao:
            conexao.execute("DELETE FROM resultados_provas WHERE usuario_id = %s", (usuario,))

