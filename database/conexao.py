import sqlite3

from pathlib import Path

# Caminho para a pasta do projeto (studyhub)
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminho completo para o banco
DB_PATH = BASE_DIR / "database" / "sistema.db"


def conectar():

    conexao = sqlite3.connect(DB_PATH)

    conexao.row_factory = sqlite3.Row

    return conexao