from rich import print

def ler_inteiro(mensagem):

    while True:

        try:
            return int(input(mensagem))

        except ValueError:
            print("[red]Digite apenas números.[/]")