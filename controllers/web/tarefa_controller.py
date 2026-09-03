from services.tarefa_service import adicionar_tarefa
from database.tarefa_repository import atualizar_status
from database.tarefa_repository import atualizar_tarefa
from database.tarefa_repository import remover_tarefa
from database.tarefa_repository import buscar_tarefa

def adicionar_tarefa_controller(usuario_id, descricao):

    descricao = descricao.strip()

    if not descricao:

        return False, "A descrição da tarefa é obrigatória."

    adicionar_tarefa(usuario_id, descricao)

    return True, "Tarefa criada com sucesso!"

def concluir_tarefa_controller(usuario_id, id_tarefa):

    tarefa = buscar_tarefa(id_tarefa, usuario_id)

    if tarefa is None:
        return False, "Tarefa não encontrada."

    novo_status = 0 if tarefa["concluida"] == 1 else 1

    atualizar_status(id_tarefa,novo_status,usuario_id)

    return True, "Status atualizado com sucesso."

def editar_tarefa_controller(usuario_id, id_tarefa, descricao):

    descricao = descricao.strip()

    if not descricao:

        return False, "A descrição não pode ficar vazia."

    atualizar_tarefa(id_tarefa,descricao,usuario_id)

    return True, "Tarefa atualizada com sucesso."

def excluir_tarefa_controller(usuario_id, id_tarefa):

    remover_tarefa(id_tarefa,usuario_id)

    return True, "Tarefa excluída com sucesso."