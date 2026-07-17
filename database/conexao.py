import sqlite3

def conectar():
    conexao = sqlite3.connect("database/sistema.db")
    return conexao