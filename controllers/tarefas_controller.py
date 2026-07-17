from studyhub.interface.menus import sub_menu
from studyhub.utils.formatacao import linha
from studyhub.utils.pausas import pausas
from studyhub.services.tarefas import obter_tarefas, adicionar_tarefa, editar_tarefa, concluir_tarefa, excluir_tarefa
from rich import print

from studyhub.utils.entrada import ler_inteiro

def selecionar_tarefa(usuario_id):

    tarefas = obter_tarefas(usuario_id)

    if not tarefas:
        print("[red]Não há tarefas cadastradas.[/]")
        return None

    while True:

        numero = ler_inteiro("Escolha o número da tarefa: ")

        if 1 <= numero <= len(tarefas):
            return tarefas[numero - 1][0]

        print("[red]Número inválido.[/]")

def adicionar_tarefas_controller(usuario_id):

    while True:
        tarefa = input("Informe a tarefa: ").strip()

        if tarefa:
            break

        print("[red]Digite uma tarefa válida.[/]")

    adicionar_tarefa(tarefa, usuario_id)

    print("[green]Tarefa adicionada com sucesso![/]")
    pausas()
    linha()

def listar_tarefas(usuario_id):
    print("[yellow]LISTA DE TAREFAS[/]")
    linha()

    tarefas = obter_tarefas(usuario_id)

    if not tarefas:
        print("[red]LISTA VAZIA[/]")
    else:
        for indice, tarefa in enumerate(tarefas, start=1):
            status = "✓" if tarefa[2] else " "

            print(f"{indice}. [{status}] {tarefa[1]}")

    linha()

def editar_tarefa_controller(usuario_id):

    id_tarefa = selecionar_tarefa(usuario_id)

    if id_tarefa is None:
        return

    while True:
        novo_nome = input("Novo nome da tarefa: ").strip()

        if novo_nome:
            break

        print("[red]Digite um nome válido.[/]")

    editar_tarefa(id_tarefa, novo_nome, usuario_id)

    print("[green]Tarefa editada com sucesso![/]")
    pausas()
    linha()

def concluir_tarefa_controller(usuario_id):

    id_tarefa = selecionar_tarefa(usuario_id)

    if id_tarefa is None:
        return

    if concluir_tarefa(id_tarefa, usuario_id):
        print("[green]Status da tarefa atualizado![/]")
    else:
        print("[red]Tarefa não encontrada.[/]")

    pausas()
    linha()

def excluir_tarefa_controller(usuario_id):

    id_tarefa = selecionar_tarefa(usuario_id)

    if id_tarefa is None:
        return

    while True:
        confirmar = input("Tem certeza que deseja excluir? [s/n] ").strip().lower()

        if confirmar in ("s", "n"):
            break

        print("[red]Digite apenas 's' ou 'n'.[/]")

    if confirmar == "n":
        return

    excluir_tarefa(id_tarefa, usuario_id)

    print("[green]Tarefa excluída com sucesso![/]")

    pausas()
    linha()

def gerenciar_tarefas(usuario):
    usuario_id = usuario[0]

    while True:
        listar_tarefas(usuario_id)

        sub_menu()

        linha()
        escolha = ler_inteiro("Escolha uma opção a ser feita: ")
        linha()

        match escolha:

            case 1:
                adicionar_tarefas_controller(usuario_id)

            case 2:
                editar_tarefa_controller(usuario_id)

            case 3:
                concluir_tarefa_controller(usuario_id)

            case 4:
                excluir_tarefa_controller(usuario_id)

            case 5:
                break
