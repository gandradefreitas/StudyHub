from datetime import datetime, timezone
from utils.horario import horario_studyhub

from database.resultados_repository import listar_resultados_usuario
from services.resumo_discursivas import resumir_correcao_discursiva
from database.respostas_discursivas_repository import (
listar_tentativas_discursivas_usuario,
)


def _data_para_ordenacao(data):
    if data is None:
        return datetime.min

    if data.tzinfo is not None:
        return data.astimezone(timezone.utc).replace(tzinfo=None)

    return data

def obter_historico(usuario_id):
    """
    Retorna um histórico unificado de provas objetivas e discursivas.
    """


    # --------------------------------------------------
    # PROVAS OBJETIVAS
    # --------------------------------------------------

    resultados_objetivos = listar_resultados_usuario(usuario_id)

    historico = []

    for resultado in resultados_objetivos:
        item = dict(resultado)

        item["modalidade"] = "objetiva"
        item["situacao"] = "Realizada"

        historico.append(item)

    # --------------------------------------------------
    # PROVAS DISCURSIVAS
    # --------------------------------------------------

    tentativas_discursivas = listar_tentativas_discursivas_usuario(
        usuario_id=usuario_id,
    )

    for tentativa in tentativas_discursivas:

        tentativa_id = tentativa["id"]
        instituicao = tentativa["instituicao"]
        ano = tentativa["ano"]
        fase = tentativa["fase"]
        disciplina = tentativa["disciplina"]
        data_inicio = tentativa["data_inicio"]
        data_finalizacao = tentativa["data_finalizacao"]
        duracao = tentativa["duracao_segundos"]
        tempo_gasto = "—"
        if duracao is not None:
            horas, restante = divmod(duracao, 3600)
            minutos, segundos = divmod(restante, 60)
            tempo_gasto = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        data_historico = (
            data_finalizacao
            if data_finalizacao is not None
            else data_inicio
        )
        data_para_ordenacao = data_historico

        if data_historico is not None:
            data_historico = horario_studyhub(data_historico).strftime("%d/%m/%Y às %H:%M")

        historico.append({
            "id": tentativa_id,
            "modalidade": "discursiva",
            "data_realizacao": data_historico,
            "prova": f"{instituicao} {ano} — {fase}",
            "disciplina": disciplina,
            **resumir_correcao_discursiva(tentativa),
            "tempo_gasto": tempo_gasto,
            "_data_ordem": data_para_ordenacao,
        })


    # --------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------

    historico.sort(
        key=lambda item: (
            _data_para_ordenacao(item.get("_data_ordem")),
            item["id"],
        ),
        reverse=True,
    )

    for item in historico:
        item.pop("_data_ordem", None)

    return historico
