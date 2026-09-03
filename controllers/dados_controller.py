from services.dados import (preparar_exportacao,limpar_historico_usuario)

def obter_dados_exportacao(usuario_id):

    return preparar_exportacao(usuario_id)

def limpar_historico(usuario_id):

    return limpar_historico_usuario(usuario_id)