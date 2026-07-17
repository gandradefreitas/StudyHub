import sys

from studyhub.controllers.login_controller import realizar_login
from studyhub.controllers.cadastro_controller import realizar_cadastro
from studyhub.utils.entrada import ler_inteiro
from studyhub.interface.menus import primeiro_menu
from studyhub.utils.limpar_tela import limpar_tela
from studyhub.utils.formatacao import linha

from rich import print


def menu_inicial():

    while True:

        limpar_tela()
        primeiro_menu()


        escolha = ler_inteiro("Escolha uma opção: ")
        linha()

        match escolha:

            case 1:
                usuario = realizar_login()

                if usuario:
                    return usuario

            case 2:
                realizar_cadastro()

            case 3:
                print("[yellow]Encerrando o sistema...[/]")
                sys.exit(0)

            case _:
                print("[red]Escolha apenas 1, 2 ou 3.[/]")
