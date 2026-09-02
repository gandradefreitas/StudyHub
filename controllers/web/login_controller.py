from studyhub.security.validacoes import (validar_email,validar_senha)
from studyhub.services.autenticacao import autenticar

def realizar_login(email, senha):

    valido, mensagem = validar_email(email)

    if not valido:

        return None, mensagem

    valido, mensagem = validar_senha(senha)

    if not valido:

        return None, mensagem

    usuario = autenticar(email,senha)

    if usuario:

        return usuario, "Login realizado com sucesso."

    return None, "E-mail ou senha incorretos."