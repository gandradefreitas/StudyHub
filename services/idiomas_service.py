import json
import re
from calendar import monthrange
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

IDIOMAS = {"en": "Inglês", "es": "Espanhol"}
DIFICULDADES = ("Fácil",) * 4 + ("Média",) * 4 + ("Difícil",) * 2
MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
    "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)
# Apóstrofos e hifens internos mantêm as partes na mesma palavra.
PALAVRA = re.compile(r"[^\W_]+(?:['’‑-][^\W_]+)*")


def carregar_textos():
    arquivo = Path(__file__).resolve().parents[1] / "dados" / "idiomas.json"
    catalogo = json.loads(arquivo.read_text(encoding="utf-8"))
    for texto in catalogo:
        texto["palavras"] = sum(len(PALAVRA.findall(p)) for p in texto["paragrafos"])
        for questao, dificuldade in zip(texto["questoes"], DIFICULDADES, strict=True):
            questao["dificuldade"] = dificuldade
    return {texto["id"]: texto for texto in catalogo}


TEXTOS = carregar_textos()


def montar_estatisticas(leituras, hoje, mes_pedido):
    palavras_por_dia = Counter()
    for leitura in leituras:
        palavras_por_dia[leitura["concluido_em"]] += leitura["palavras"]

    mes_atual = hoje.replace(day=1)
    mes = mes_atual
    if mes_pedido:
        try:
            mes = min(date.fromisoformat(f"{mes_pedido}-01"), mes_atual)
        except ValueError:
            pass

    quantidade_dias = monthrange(mes.year, mes.month)[1]
    dias = [palavras_por_dia[mes.replace(day=dia)] for dia in range(1, quantidade_dias + 1)]
    anterior = (mes - timedelta(days=1)).replace(day=1) if mes > date.min else None
    seguinte = mes + timedelta(days=quantidade_dias) if mes < mes_atual else None

    return {
        "hoje": palavras_por_dia[hoje],
        "total": sum(palavras_por_dia.values()),
        "total_mes": sum(dias),
        "dias": dias,
        "pico": max(dias) or 1,
        "rotulo_mes": f"{MESES[mes.month - 1]} de {mes.year}",
        "mes": mes.isoformat()[:7],
        "mes_atual": mes_atual.isoformat()[:7],
        "anterior": anterior.isoformat()[:7] if anterior else None,
        "seguinte": seguinte.isoformat()[:7] if seguinte else None,
    }
