from rich import print

def primeiro_menu():
    print('[purple]=' * 40)
    print('[1] - [green]Fazer login[/]\n'
          '[2] - [green]Cadastrar-se[/]\n'
          '[3] - [green]Sair[/]\n')

def segundo_menu():
    print('[purple]~' * 40)
    print('[1] - [green]Listar e gerenciar as tarefas[/]\n'
          '[2] - [green]Logout[/]\n')

def sub_menu():
    print('[purple]~' * 40)
    print("[1][blue]Adicionar tarefas[/] [2][blue]Editar tarefas[/] [3][blue]Concluir tarefas[/] ")
    print()
    print("[4][red]Excluir tarefas[/] [5][yellow]Voltar[/]")