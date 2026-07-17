import bcrypt


def gerar_hash(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")

    salt = bcrypt.gensalt()

    senha_hash = bcrypt.hashpw(senha_bytes, salt)

    return senha_hash.decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(
        senha.encode("utf-8"),
        senha_hash.encode("utf-8")
    )