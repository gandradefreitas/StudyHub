from collections import Counter
from datetime import date, timedelta

from database.estudos_repository import obter_estudos_por_periodo, obter_total_segundos
from database.resultados_repository import (
    converter_tempo_para_segundos, obter_provas_por_periodo, obter_segundos_provas,
)
from database.tempo_provas_escritas import obter_duracao_provas_escritas_por_dia


def obter_tempo_total_estudado(usuario_id):
    return obter_total_segundos(usuario_id) + obter_segundos_provas(usuario_id)


def resumir_desempenho_objetivo(desempenho):
    grupos = {prova: {} for prova in ("ENEM", "ITA")}
    for (prova, area), dados in desempenho.items():
        if prova in grupos:
            grupos[prova][area] = dados

    areas = [
        (prova, area, dados["acertos"] * 100 / dados["questoes"])
        for prova, disciplinas in grupos.items()
        for area, dados in disciplinas.items()
        if dados["questoes"]
    ]
    areas.sort(key=lambda item: item[2], reverse=True)
    total_questoes = sum(dados["questoes"] for disciplinas in grupos.values() for dados in disciplinas.values())
    total_acertos = sum(dados["acertos"] for disciplinas in grupos.values() for dados in disciplinas.values())

    return dict(
        desempenho_provas=grupos,
        total_questoes=total_questoes,
        total_acertos=total_acertos,
        ponto_forte=areas[0] if areas else None,
        ponto_atencao=areas[-1] if areas else None,
    )


def obter_evolucao_estudos(usuario_id, inicio, fim):
    """Agrupa estudo, provas objetivas e escritas nos mesmos dias do relatório."""
    duracoes = Counter()

    def data_iso(data):
        return data.isoformat() if isinstance(data, date) else data

    inicio_iso, fim_iso = inicio.isoformat(), fim.isoformat()
    for estudo in obter_estudos_por_periodo(usuario_id, inicio_iso, fim_iso):
        duracoes[data_iso(estudo["data"])] += estudo["duracao"]
    for prova in obter_provas_por_periodo(usuario_id, inicio_iso, fim_iso):
        duracoes[data_iso(prova["data"])] += converter_tempo_para_segundos(prova["tempo_gasto"])
    for prova in obter_duracao_provas_escritas_por_dia(usuario_id, inicio, fim):
        duracoes[data_iso(prova["data"])] += prova["duracao"]

    dias = []
    for deslocamento in range((fim - inicio).days + 1):
        dia = (inicio + timedelta(days=deslocamento)).isoformat()
        dias.append({"data": dia, "duracao": duracoes[dia]})
    return dias
