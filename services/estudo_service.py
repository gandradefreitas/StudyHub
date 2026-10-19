from database.resultados_repository import obter_segundos_provas

from database.estudos_repository import (
    obter_total_segundos,
    iniciar_estudo,
    obter_estudo_ativo,
    finalizar_estudo,
    possui_estudo_ativo,
    registrar_atividade_estudo,
)

from datetime import datetime


def iniciar_estudo_service(usuario_id):

    if possui_estudo_ativo(usuario_id):
        return False, "Já existe uma sessão de estudo ativa."

    iniciar_estudo(usuario_id)

    return True, "Sessão de estudo iniciada."


def obter_estudo_ativo_service(usuario_id):

    return obter_estudo_ativo(usuario_id)


def obter_horas_estudadas(usuario_id):

    segundos_estudos = obter_total_segundos(
        usuario_id
    )

    segundos_provas = obter_segundos_provas(
        usuario_id
    )

    segundos = (
        segundos_estudos +
        segundos_provas
    )

    horas = segundos // 3600

    minutos = (
        segundos % 3600
    ) // 60

    return f"{horas}h {minutos}min"


def finalizar_estudo_service(usuario_id):

    estudo = obter_estudo_ativo(
        usuario_id
    )

    if estudo is None:
        return (
            False,
            "Nenhuma sessão de estudo ativa encontrada."
        )

    estudo_id = estudo["id"]

    inicio = estudo["inicio"]

    if isinstance(inicio, str):
        inicio = datetime.fromisoformat(
            inicio
        )

    fim = datetime.now()

    duracao = int(
        (fim - inicio).total_seconds()
    )

    finalizar_estudo(
        estudo_id,
        fim,
        duracao,
        usuario_id
    )

    return True, "Sessão de estudo finalizada."


def formatar_duracao(segundos):

    segundos = int(
        segundos or 0
    )

    horas = segundos // 3600

    minutos = (
        segundos % 3600
    ) // 60

    if horas > 0 and minutos > 0:

        return f"{horas}h {minutos}min"

    if horas > 0:

        return f"{horas}h"

    return f"{minutos}min"

def iniciar_estudo_automatico_service(usuario_id):
    """
    Inicia uma sessão automática ou recupera uma já existente.
    """

    estudo = obter_estudo_ativo(usuario_id)

    if estudo is not None:
        return True, "Sessão de estudo recuperada.", estudo

    estudo = iniciar_estudo(usuario_id)

    return True, "Sessão de estudo iniciada.", estudo


def registrar_atividade_estudo_service(usuario_id, tipo_evento):
    """
    Registra uma interação ou um heartbeat do cronômetro.
    """

    return registrar_atividade_estudo(
        usuario_id,
        tipo_evento,
    )


def finalizar_estudo_automatico_service(usuario_id):
    """
    Finaliza uma sessão automática preservando o tempo
    acumulado no banco de dados.
    """

    # Primeiro, registra o último intervalo contabilizável.
    registrar_atividade_estudo(
        usuario_id,
        "heartbeat",
    )

    estudo = obter_estudo_ativo(usuario_id)

    if estudo is None:
        return False, "Nenhuma sessão de estudo ativa encontrada."

    fim = datetime.now()
    duracao = int(estudo["duracao"] or 0)

    sucesso = finalizar_estudo(
        estudo["id"],
        fim,
        duracao,
        usuario_id,
    )

    if not sucesso:
        return False, "Não foi possível finalizar a sessão."

    return True, "Sessão de estudo finalizada."