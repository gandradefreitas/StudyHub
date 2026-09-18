from security.hash import gerar_hash
from database.usuario_repository import salvar_usuario
from psycopg.errors import UniqueViolation

def cadastrar_usuario(nome, email, senha):

    senha_hash = gerar_hash(senha)

    try:
        salvar_usuario(nome, email, senha_hash)

    except UniqueViolation:
        return False, "Este e-mail já está cadastrado."

    return True, "Usuário cadastrado com sucesso."