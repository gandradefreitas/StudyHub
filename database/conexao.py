import sqlite3

def conectar():

    conexao = sqlite3.connect("database/sistema.db")

    conexao.row_factory = sqlite3.Row

    return conexao