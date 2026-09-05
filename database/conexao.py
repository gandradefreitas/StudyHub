import os
import psycopg
from psycopg.rows import dict_row


def conectar():

    conexao = psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    )

    return conexao