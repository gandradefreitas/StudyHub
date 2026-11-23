import bcrypt

def gerar_hash(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")

    salt = bcrypt.gensalt()

    senha_hash = bcrypt.hashpw(senha_bytes, salt)

    return senha_hash.decode("utf-8")


def verificar_senha(senha: str, senha_hash: str | None) -> bool:
    if not senha_hash:
        return False

    senha_bytes = senha.encode("utf-8")
    if len(senha_bytes) > 72:
        return False

    try:
        return bcrypt.checkpw(senha_bytes, senha_hash.encode("utf-8"))
    except ValueError:
        return False
