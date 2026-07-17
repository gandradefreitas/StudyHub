from studyhub.database.tarefa_repository import (
    salvar_tarefa,
    listar_tarefas,
    atualizar_tarefa,
    atualizar_status,
    remover_tarefa,
    buscar_tarefa,
)

def editar_tarefa(id_tarefa, novo_nome, usuario_id):
    atualizar_tarefa(id_tarefa, novo_nome, usuario_id)

def concluir_tarefa(id_tarefa, usuario_id):

    tarefa = buscar_tarefa(id_tarefa, usuario_id)

    if not tarefa:
        return False

    novo_status = 0 if tarefa[2] else 1

    atualizar_status(id_tarefa, novo_status, usuario_id)

    return True

def excluir_tarefa(id_tarefa, usuario_id):
    remover_tarefa(id_tarefa, usuario_id)

def adicionar_tarefa(descricao, usuario_id):
    salvar_tarefa(descricao, usuario_id)


def obter_tarefas(usuario_id):
    return listar_tarefas(usuario_id)