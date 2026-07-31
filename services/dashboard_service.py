from studyhub.database.usuario_repository import obter_usuario_por_id

from studyhub.database.tarefa_repository import (
    contar_tarefas_usuario,
    obter_proximas_tarefas
)


def carregar_dashboard(usuario_id):

    usuario = obter_usuario_por_id(usuario_id)

    estatisticas = contar_tarefas_usuario(usuario_id)

    tarefas = obter_proximas_tarefas(usuario_id)

    return {
        "usuario": usuario,
        "estatisticas": estatisticas,
        "tarefas": tarefas
    }