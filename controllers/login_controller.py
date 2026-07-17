from studyhub.security.validacoes import validar_email, validar_senha
from studyhub.utils.formatacao import linha
from studyhub.utils.pausas import pausas
from studyhub.services.autenticacao import autenticar
from rich import print

def realizar_login():
        while True:
            email = input('Informe o seu e-mail:  ').strip()
            pausas()
            linha()

            valido, mensagem = validar_email(email)

            if valido:
                break

            print(f"[red]{mensagem}[/]")

        while True:
            senha = input('Informe a sua senha:  ') # Desenvolver melhor após implementar criptografia e banco de dados

            if not validar_senha(senha):
                print("A senha não pode ficar vazia.")
                continue

            usuario = autenticar(email, senha)

            if usuario:
                linha()
                print(f"Bem-vindo [blue]{usuario[1]}[/]!")
                pausas()
                linha()
                return usuario
            else:
                print("E-mail ou senha incorretos.")

            pausas()
            linha()

            valido, mensagem = validar_senha(senha)

            if valido:
                break

            print(f"[red]{mensagem}[/]")
