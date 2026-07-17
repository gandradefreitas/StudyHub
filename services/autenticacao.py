from studyhub.database.usuario_repository import buscar_por_email
from studyhub.security.hash import verificar_senha


def autenticar(email, senha):

    usuario = buscar_por_email(email)

    if usuario is None:
        return None

    senha_hash = usuario[3]

    if verificar_senha(senha, senha_hash):
        return usuario

    return None