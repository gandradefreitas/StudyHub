from security.hash import gerar_hash
from database.usuario_repository import salvar_usuario

def cadastrar_usuario(nome, email, senha):

    senha_hash = gerar_hash(senha)

    salvar_usuario(nome,email,senha_hash)

    return True