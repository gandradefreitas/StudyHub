from studyhub.services.configuracoes import (
    obter_dados_configuracoes,
    atualizar_dados_conta,
    alterar_senha_usuario,
    alterar_tema,
    atualizar_metas,
    excluir_conta_usuario
)


def carregar_configuracoes(usuario_id):

    dados = obter_dados_configuracoes(
        usuario_id
    )

    return dados

def atualizar_conta(usuario_id, nome, email):

    return atualizar_dados_conta(
        usuario_id,
        nome,
        email
    )

def alterar_senha(
    usuario_id,
    senha_atual,
    nova_senha,
    confirmar_senha
):

    return alterar_senha_usuario(
        usuario_id,
        senha_atual,
        nova_senha,
        confirmar_senha
    )

def atualizar_tema(
    usuario_id,
    tema
):

    return alterar_tema(
        usuario_id,
        tema
    )

def atualizar_metas_configuracoes(
    usuario_id,
    meta_estudo,
    meta_questoes
):

    return atualizar_metas(
        usuario_id,
        meta_estudo,
        meta_questoes
    )

def excluir_conta(
    usuario_id,
    senha_atual
):

    return excluir_conta_usuario(
        usuario_id,
        senha_atual
    )