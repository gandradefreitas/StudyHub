from datetime import datetime, timezone

from database.resultados_repository import listar_resultados_usuario
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
        status = tentativa["status"]
        nota_total = tentativa["nota_total"]
        nota_maxima = tentativa["nota_maxima"]
        data_inicio = tentativa["data_inicio"]
        data_finalizacao = tentativa["data_finalizacao"]
        duracao = tentativa["duracao_segundos"]
        tempo_gasto = "—"
        if duracao is not None:
            horas, restante = divmod(duracao, 3600)
            minutos, segundos = divmod(restante, 60)
            tempo_gasto = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        parecer = tentativa.get("resultado_correcao") or {}
        if parecer.get("status") == "provisoria":
            situacao = "Correção provisória"
            nota_total = parecer.get("nota_provisoria")
            nota_maxima = nota_maxima if nota_maxima is not None else parecer.get("nota_maxima")

        elif parecer.get("status") == "revisao_necessaria":
            situacao = "Revisão necessária"

        elif status == "corrigida" or parecer.get("status") == "corrigida":
            situacao = "Corrigida"
            nota_total = nota_total if nota_total is not None else parecer.get("nota")
            nota_maxima = nota_maxima if nota_maxima is not None else parecer.get("nota_maxima")
            situacao = "Corrigida"

        elif status == "finalizada":
            situacao = "Aguardando correção"

        else:
            situacao = "Em andamento"

        data_historico = (
            data_finalizacao
            if data_finalizacao is not None
            else data_inicio
        )
        data_para_ordenacao = data_historico

        if data_historico is not None:
            data_historico = data_historico.strftime("%d/%m/%Y às %H:%M")

        if nota_total is not None and nota_maxima is not None:
            resultado_formatado = f"{nota_total}/{nota_maxima}"
        else:
            resultado_formatado = (
                "Parecer disponível" if parecer.get("correcao")
                else "Correção pendente" if status == "finalizada"
                else "—"
            )

        historico.append({
            "id": tentativa_id,
            "modalidade": "discursiva",
            "data_realizacao": data_historico,
            "prova": f"{instituicao} {ano} — {fase}",
            "disciplina": disciplina,
            "situacao": situacao,
            "nota_total": nota_total,
            "nota_maxima": nota_maxima,
            "resultado_formatado": resultado_formatado,
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
