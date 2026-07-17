from studyhub.security.validacoes import validar_nome, validar_email, validar_senha
from studyhub.utils.formatacao import linha
from studyhub.utils.pausas import pausas
from studyhub.services.usuarios import cadastrar_usuario
from rich import print

def realizar_cadastro():
    while True:
        nome = input('Informe o seu nome:  ').strip().title()
        pausas()
        linha()

        valido, mensagem = validar_nome(nome)

        if valido:
            break

        print(f"[red]{mensagem}[/]")

    while True:
        email = input('Informe o seu e-mail:  ')
        pausas()
        linha()

        valido, mensagem = validar_email(email)

        if valido:
            break

        print(f"[red]{mensagem}[/]")

    while True:
        senha = input('Informe a sua senha:  ') # Desenvolver banco de dados
        pausas()
        linha()

        valido, mensagem = validar_senha(senha)

        if valido:
            break

        print(f"[red]{mensagem}[/]")

    cadastrar_usuario(
        nome,
        email,
        senha
    )

    linha()
    print(f"Usuário {nome} cadastrado com sucesso!")
    print("Agora faça [yellow]login[/] para acessar o sistema.")
    pausas()
    linha()
