from studyhub.database.usuario_repository import (
    obter_usuario_por_id,
    obter_configuracoes,
    atualizar_usuario,
    atualizar_senha,
    salvar_tema,
    salvar_metas,
    excluir_usuario
)
from studyhub.security.validacoes import (
    validar_nome,
    validar_email
)
from studyhub.security.hash import (
    gerar_hash,
    verificar_senha
)

from studyhub.security.validacoes import (
    validar_senha
)

TEMAS_PERMITIDOS = {
    "claro",
    "escuro",
    "sistema"
}

def obter_dados_configuracoes(usuario_id):

    usuario = obter_usuario_por_id(
        usuario_id
    )

    configuracoes = obter_configuracoes(
        usuario_id
    )

    return {
        "usuario": usuario,
        "configuracoes": configuracoes
    }

def atualizar_dados_conta(usuario_id, nome, email):

    valido, mensagem = validar_nome(nome)

    if not valido:
        return False, mensagem


    valido, mensagem = validar_email(email)

    if not valido:
        return False, mensagem


    atualizar_usuario(
        usuario_id,
        nome,
        email
    )

    return True, "Dados atualizados com sucesso."

def alterar_senha_usuario(
    usuario_id,
    senha_atual,
    nova_senha,
    confirmar_senha
):

    usuario = obter_usuario_por_id(
        usuario_id
    )

    if not usuario:

        return False, "Usuário não encontrado."


    senha_correta = verificar_senha(
        senha_atual,
        usuario["senha"]
    )

    if not senha_correta:

        return False, "A senha atual está incorreta."


    if nova_senha != confirmar_senha:

        return False, "As novas senhas não coincidem."


    valido, mensagem = validar_senha(
        nova_senha
    )

    if not valido:

        return False, mensagem


    senha_hash = gerar_hash(
        nova_senha
    )


    atualizar_senha(
        usuario_id,
        senha_hash
    )


    return True, "Senha alterada com sucesso."

def alterar_tema(usuario_id, tema):

    if tema not in TEMAS_PERMITIDOS:

        return False, "Tema inválido."


    salvar_tema(
        usuario_id,
        tema
    )


    return True, "Aparência atualizada com sucesso."

def atualizar_metas(
    usuario_id,
    meta_estudo,
    meta_questoes
):

    try:

        meta_estudo = int(meta_estudo)
        meta_questoes = int(meta_questoes)

    except (TypeError, ValueError):

        return False, "As metas devem conter valores válidos."


    if meta_estudo < 1:

        return False, "A meta de estudo deve ser maior que zero."


    if meta_questoes < 1:

        return False, "A meta de questões deve ser maior que zero."


    salvar_metas(
        usuario_id,
        meta_estudo,
        meta_questoes
    )


    return True, "Metas atualizadas com sucesso."


def excluir_conta_usuario(
    usuario_id,
    senha_atual
):

    usuario = obter_usuario_por_id(
        usuario_id
    )

    if not usuario:

        return False, "Usuário não encontrado."


    senha_correta = verificar_senha(
        senha_atual,
        usuario["senha"]
    )

    if not senha_correta:

        return False, "A senha atual está incorreta."


    sucesso = excluir_usuario(
        usuario_id
    )

    if not sucesso:

        return False, "Não foi possível excluir a conta."


    return True, "Conta excluída com sucesso."