import os
import uuid

import psycopg
import pytest

from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from database.criar_banco import criar_tabelas


@pytest.fixture(autouse=True)
def proteger_banco_de_testes(request):
    if request.node.get_closest_marker("matematica") is None:
        request.getfixturevalue("verificar_banco_de_testes")


@pytest.fixture(scope="session")
def verificar_banco_de_testes():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        pytest.fail("DATABASE_URL não está configurada.")

    if conninfo_to_dict(database_url).get("dbname") != "studyhub_test":
        pytest.fail("DATABASE_URL deve apontar explicitamente para studyhub_test.")

    try:
        with psycopg.connect(database_url) as conexao:
            banco = conexao.execute(
                "SELECT current_database()"
            ).fetchone()[0]
    except psycopg.Error as erro:
        pytest.fail(
            f"Não foi possível conectar ao banco de testes: {erro}"
        )

    if banco != "studyhub_test":
        pytest.fail(
            "Testes cancelados: o banco conectado não é "
            "'studyhub_test'."
        )

    criar_tabelas()


@pytest.fixture
def dados_discursivos(verificar_banco_de_testes):
    database_url = os.environ["DATABASE_URL"]

    identificador = uuid.uuid4().hex

    usuarios_ids = []
    tentativas_ids = []

    with psycopg.connect(
        database_url,
        row_factory=dict_row,
    ) as conexao:

        try:
            # Confirma novamente o banco antes de escrever.
            banco = conexao.execute(
                "SELECT current_database() AS nome"
            ).fetchone()["nome"]

            if banco != "studyhub_test":
                pytest.fail(
                    "Operação cancelada: banco diferente de studyhub_test."
                )

            # Cria dois usuários exclusivos para este teste.
            for numero in (1, 2):
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
                        f"Usuario Teste {numero}",
                        f"teste_{numero}_{identificador}@example.invalid",
                        "senha-nao-utilizada",
                        "sistema",
                    ),
                ).fetchone()

                usuarios_ids.append(usuario["id"])

            # Cria uma tentativa em andamento para cada usuário.
            for usuario_id in usuarios_ids:
                tentativa = conexao.execute(
                    """
                    INSERT INTO tentativas_provas_discursivas (
                        usuario_id,
                        instituicao,
                        ano,
                        fase,
                        disciplina,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
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

                tentativas_ids.append(tentativa["id"])

            conexao.commit()

        except Exception:
            conexao.rollback()
            raise

    dados = {
        "usuarios": usuarios_ids,
        "tentativas": tentativas_ids,
    }

    try:
        yield dados

    finally:
        # Remove somente os registros criados por esta fixture.
        with psycopg.connect(
            database_url,
            row_factory=dict_row,
        ) as conexao:

            try:
                banco = conexao.execute(
                    "SELECT current_database() AS nome"
                ).fetchone()["nome"]

                if banco != "studyhub_test":
                    pytest.fail(
                        "Limpeza cancelada: banco inesperado."
                    )

                if tentativas_ids:
                    conexao.execute(
                        """
                        DELETE FROM tentativas_provas_discursivas
                        WHERE usuario_id = ANY(%s)
                        """,
                        (usuarios_ids,),
                    )

                if usuarios_ids:
                    conexao.execute(
                        """
                        DELETE FROM usuarios
                        WHERE id = ANY(%s)
                        """,
                        (usuarios_ids,),
                    )

                conexao.commit()

            except Exception:
                conexao.rollback()
                raise
