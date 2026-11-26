from database.dados_repository import (obter_dados_exportacao,limpar_historico)

def converter_para_json(dados):

    resultado = {}

    for chave, valor in dados.items():

        if hasattr(valor, "keys"):

            resultado[chave] = dict(valor)

        elif isinstance(valor, list):

            resultado[chave] = [
                dict(item)
                for item in valor
            ]

        else:

            resultado[chave] = valor


    return resultado


def preparar_exportacao(usuario_id):

    dados = obter_dados_exportacao(usuario_id)

    return converter_para_json(dados)

def limpar_historico_usuario(usuario_id):

    resultado = limpar_historico(usuario_id)

    if not resultado:

        return (
            False,
            "Não foi possível limpar o histórico."
        )


    return (
        True,
        "Histórico limpo com sucesso."
    )