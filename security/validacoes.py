
CARACTERES_ESPECIAIS = "!@#$%&*()-_=+[]{};:,.<>?/\\|"

def validar_nome(nome):
    nome = nome.strip()

    if len(nome) < 3:
        return False, "O nome deve ter pelo menos 3 caracteres."

    if len(nome) > 50:
        return False, "O nome deve ter no máximo 50 caracteres."

    permitido = " -'"

    if not all(c.isalpha() or c in permitido for c in nome):
        return False, "Use apenas letras, espaços, hífen e apóstrofo."

    if nome.startswith("-") or nome.endswith("-"):
        return False, "O hífen não pode estar no início nem no fim."

    if nome.startswith("'") or nome.endswith("'"):
        return False, "O apóstrofo não pode estar no início nem no fim."

    if "--" in nome or "''" in nome or "-'" in nome or "'-" in nome:
        return False, "Não utilize símbolos consecutivos."

    if "  " in nome:
        return False, "Não utilize espaços consecutivos."

    if "- " in nome or " -" in nome:
        return False, "O hífen deve ficar entre duas letras."

    if "' " in nome or " '" in nome:
        return False, "O apóstrofo deve ficar entre duas letras."

    for i, caractere in enumerate(nome):

        if caractere in "-'":

            if not nome[i - 1].isalpha():
                return False, "O hífen ou apóstrofo deve estar entre letras."

            if not nome[i + 1].isalpha():
                return False, "O hífen ou apóstrofo deve estar entre letras."

    return True, ""

def validar_email(email):
    email = email.strip()

    if len(email) < 6:
        return False, "O e-mail é muito curto."

    if len(email) > 254:
        return False, "O e-mail é muito longo."

    if " " in email:
        return False, "O e-mail não pode conter espaços."

    if email.count("@") != 1:
        return False, "O e-mail deve conter exatamente um '@'."

    usuario, dominio = email.split("@")

    if not usuario:
        return False, "O e-mail deve possuir um nome de usuário antes do '@'."

    if not dominio:
        return False, "O e-mail deve possuir um domínio após o '@'."

    if usuario.startswith(".") or usuario.endswith("."):
        return False, "O nome de usuário não pode começar ou terminar com ponto."

    if dominio.startswith(".") or dominio.endswith("."):
        return False, "O domínio não pode começar ou terminar com ponto."

    if ".." in email:
        return False, "O e-mail não pode conter pontos consecutivos."

    if "." not in dominio:
        return False, "O domínio deve conter pelo menos um ponto."

    caracteres_permitidos = "._-"

    for caractere in usuario:
        if not (caractere.isalnum() or caractere in caracteres_permitidos):
            return False, "O nome de usuário possui caracteres inválidos."

    for caractere in dominio:
        if not (caractere.isalnum() or caractere in ".-"):
            return False, "O domínio possui caracteres inválidos."

    return True, ""

def validar_senha(senha):
    senha = senha.strip()

    if len(senha) < 8:
        return False, "A senha deve possuir pelo menos 8 caracteres."

    if len(senha) > 64:
        return False, "A senha deve possuir no máximo 64 caracteres."

    if " " in senha:
        return False, "A senha não pode conter espaços."

    if not any(c.islower() for c in senha):
        return False, "A senha deve possuir pelo menos uma letra minúscula."

    if not any(c.isupper() for c in senha):
        return False, "A senha deve possuir pelo menos uma letra maiúscula."

    if not any(c.isdigit() for c in senha):
        return False, "A senha deve possuir pelo menos um número."

    if not any(c in CARACTERES_ESPECIAIS for c in senha):
        return False, "A senha deve possuir pelo menos um caractere especial."

    return True, ""