from studyhub.services.estudo_service import iniciar_estudo_service, finalizar_estudo_service, obter_estudo_ativo_service, obter_horas_estudadas

def obter_estudo_ativo_controller(usuario_id):
    return obter_estudo_ativo_service(usuario_id)

def iniciar_estudo_controller(usuario_id):

    return iniciar_estudo_service(usuario_id)

def finalizar_estudo_controller(usuario_id):

    return finalizar_estudo_service(usuario_id)

def obter_horas_estudadas_controller(usuario_id):

    return obter_horas_estudadas(usuario_id)