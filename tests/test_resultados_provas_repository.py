from unittest.mock import patch

import pytest

from database import resultados_repository


class QuestaoTeste:

    def __init__(self, numero, alternativas, resposta):
        self.numero = numero
        self.alternativas = alternativas
        self.resposta = resposta


def test_falha_ao_salvar_resposta_reverte_transacao():
    """
    Simula uma falha durante a inserção das respostas e verifica
    se o resultado inserido anteriormente também é revertido.
    """

    # 1. Conecta ao banco e confirma que é o banco de testes.
    conexao = resultados_repository.conectar()

    try:
        banco = conexao.execute(
            "SELECT current_database() AS nome"
        ).fetchone()["nome"]

        assert banco == "studyhub_test"

        # Cria um usuário exclusivo para este teste.
        usuario = conexao.execute(
            """
            INSERT INTO usuarios (
                nome,
                email,
                senha,
                tema
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                "Teste Atomicidade",
                "teste_atomicidade@example.invalid",
                "senha-nao-utilizada",
                "sistema",
            ),
        ).fetchone()

        usuario_id = usuario["id"]
        conexao.commit()

    finally:
        conexao.close()

    # 2. Prepara questões fictícias e suas respostas.
    questoes = [
        QuestaoTeste(
            numero=1,
            alternativas=["A", "B", "C", "D", "E"],
            resposta=0,
        ),
        QuestaoTeste(
            numero=2,
            alternativas=["A", "B", "C", "D", "E"],
            resposta=1,
        ),
    ]

    respostas = {
        "1": 0,
        "2": 1,
    }

    resultado = {
        "usuario_id": usuario_id,
        "prova_id": 1,
        "acertos": 2,
        "erros": 0,
        "nao_respondidas": 0,
        "total": 2,
        "tempo_gasto": "00:05:00",
        "porcentagem": 100.0,
    }

    conectar_original = resultados_repository.conectar

    # 3. Cria um cursor que provoca uma falha controlada.
    class CursorComFalha:

        def __init__(self, cursor_real):
            self.cursor_real = cursor_real
            self.inseriu_resultado = False

        def execute(self, comando, parametros=None):
            comando_normalizado = comando.strip().upper()

            if (
                comando_normalizado.startswith("INSERT INTO")
                and "RESULTADOS_PROVAS" in comando_normalizado
            ):
                retorno = self.cursor_real.execute(
                    comando,
                    parametros,
                )

                self.inseriu_resultado = True

                return retorno

            if (
                comando_normalizado.startswith("INSERT INTO")
                and "RESPOSTAS_PROVAS" in comando_normalizado
                and self.inseriu_resultado
            ):
                raise RuntimeError(
                    "Falha simulada ao inserir resposta."
                )

            return self.cursor_real.execute(
                comando,
                parametros,
            )

        def fetchone(self):
            return self.cursor_real.fetchone()

        def close(self):
            self.cursor_real.close()

    # 4. Encapsula a conexão real para permitir a simulação.
    class ConexaoComFalha:

        def __init__(self, conexao_real):
            self.conexao_real = conexao_real

        def cursor(self):
            return CursorComFalha(
                self.conexao_real.cursor()
            )

        def commit(self):
            self.conexao_real.commit()

        def rollback(self):
            self.conexao_real.rollback()

        def close(self):
            self.conexao_real.close()

    def conectar_com_falha():
        conexao_real = conectar_original()

        banco_atual = conexao_real.execute(
            "SELECT current_database() AS nome"
        ).fetchone()["nome"]

        if banco_atual != "studyhub_test":
            conexao_real.close()

            raise RuntimeError(
                "Teste cancelado: banco diferente de studyhub_test."
            )

        return ConexaoComFalha(conexao_real)

    try:
        # 5. Substitui temporariamente a função de conexão.
        with patch.object(
            resultados_repository,
            "conectar",
            side_effect=conectar_com_falha,
        ):

            # Espera que a função falhe ao inserir uma resposta.
            with pytest.raises(
                RuntimeError,
                match="Falha simulada ao inserir resposta",
            ):

                resultados_repository.salvar_resultado_com_respostas(
                    resultado=resultado,
                    questoes=questoes,
                    respostas=respostas,
                )

        # 6. Abre uma nova conexão para conferir o banco.
        conexao_verificacao = conectar_original()

        try:
            banco = conexao_verificacao.execute(
                "SELECT current_database() AS nome"
            ).fetchone()["nome"]

            assert banco == "studyhub_test"

            resultado_existente = conexao_verificacao.execute(
                """
                SELECT id
                FROM resultados_provas
                WHERE usuario_id = %s
                  AND prova_id = %s
                """,
                (usuario_id, resultado["prova_id"]),
            ).fetchall()

            respostas_existentes = conexao_verificacao.execute(
                """
                SELECT questao_numero
                FROM respostas_provas
                WHERE usuario_id = %s
                  AND prova_id = %s
                """,
                (usuario_id, resultado["prova_id"]),
            ).fetchall()

            # Nenhum registro da tentativa deve ter sido persistido.
            assert resultado_existente == []
            assert respostas_existentes == []

        finally:
            conexao_verificacao.close()

    finally:
        # 7. Remove somente o usuário criado pelo teste.
        conexao_limpeza = conectar_original()

        try:
            banco = conexao_limpeza.execute(
                "SELECT current_database() AS nome"
            ).fetchone()["nome"]

            if banco != "studyhub_test":
                raise RuntimeError(
                    "Limpeza cancelada: banco inesperado."
                )

            conexao_limpeza.execute(
                "DELETE FROM usuarios WHERE id = %s",
                (usuario_id,),
            )

            conexao_limpeza.commit()

        except Exception:
            conexao_limpeza.rollback()
            raise

        finally:
            conexao_limpeza.close()
