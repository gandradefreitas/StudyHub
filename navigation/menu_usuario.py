from studyhub.controllers.tarefas_controller import gerenciar_tarefas

from studyhub.interface.menus import segundo_menu
from studyhub.utils.entrada import ler_inteiro
from studyhub.utils.limpar_tela import limpar_tela
from studyhub.utils.formatacao import linha
from studyhub.utils.pausas import pausas

from rich import print


def menu_usuario(usuario):

    limpar_tela()

    linha()
    print("[yellow]GERENCIADOR DE TAREFAS[/]".center(50))
    linha()

    while True:

        segundo_menu()

        escolha = ler_inteiro("Escolha a opção: ")
        linha()

        match escolha:

            case 1:
                gerenciar_tarefas(usuario)

            case 2:
                print("[red]Deslogando...[/]")
                pausas()
                limpar_tela()
                return

            case _:
                print("[red]Escolha uma opção válida.[/]")
                