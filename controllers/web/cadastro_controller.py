from security.validacoes import (validar_nome,validar_email,validar_senha)
from services.usuarios import cadastrar_usuario

def realizar_cadastro(nome, email, senha):

    valido, mensagem = validar_nome(nome)

    if not valido:
        return False, mensagem


    valido, mensagem = validar_email(email)

    if not valido:
        return False, mensagem


    valido, mensagem = validar_senha(senha)

    if not valido:
        return False, mensagem


    resultado, mensagem = cadastrar_usuario(nome,email,senha)


    return resultado, mensagem