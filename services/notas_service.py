from services.resumo_discursivas import resumir_correcao_discursiva
import csv
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from database.resultados_repository import listar_resultados_usuario, listar_acertos_por_tentativa
from database.respostas_discursivas_repository import listar_tentativas_discursivas_usuario
from services.provas_service import obter_prova


AREAS_ENEM = {
    "Linguagens": "Linguagens",
    "Humanas": "Ciências Humanas",
    "Natureza": "Ciências da Natureza",
    "Matematica": "Matemática",
}
AREAS_ITA = ("Matemática", "Física", "Química", "Inglês")


@lru_cache(maxsize=1)
def tabela_enem():
    caminho = Path(__file__).resolve().parents[1] / "dados/enem/faixas_enem_2025.csv"
    tabela = defaultdict(dict)
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        next(arquivo)  # Crédito e metodologia da fonte.
        for linha in csv.DictReader(arquivo):
            tabela[linha["area"]][int(linha["acertos"])] = tuple(
                float(linha[campo]) for campo in ("nota_p10", "nota_mediana", "nota_p90")
            )
    return tabela


def faixa_enem(area, acertos, total):
    faixas = tabela_enem()[area]
    maximo = max(faixas)
    equivalente = (2 * acertos * maximo + total) // (2 * total)
    return faixas[equivalente], equivalente, maximo


def avaliar_ita(acertos):
    ciencias = sum(acertos[area] for area in AREAS_ITA[:3])
    abaixo_do_minimo = [area for area in AREAS_ITA if acertos[area] < 5]
    return {
        "nota": ciencias * 10 / 36,
        "ciencias": ciencias,
        "disciplinas_abaixo": abaixo_do_minimo,
        "eliminado": bool(abaixo_do_minimo or ciencias < 18),
    }


def detalhar_enem(prova, resultado, acertos):
    totais = Counter(q.area for q in prova.questoes)
    if prova.dia == "Primeiro Dia":
        totais = Counter(q.area for q in prova.questoes if not q.lingua)
        idiomas = Counter(q.lingua for q in prova.questoes if q.lingua)
        questoes_idioma = resultado["total"] - sum(totais.values())
        if questoes_idioma in idiomas.values():
            totais["Linguagens"] += questoes_idioma
    areas = []
    for area, nome in AREAS_ENEM.items():
        total = totais[area]
        if total == 0:
            continue
        quantidade = acertos[area]
        if quantidade > total:
            return []
        faixa, equivalente, maximo = faixa_enem(nome, quantidade, total)
        areas.append({
            "nome": nome, "acertos": quantidade, "total": total,
            "faixa": faixa, "equivalente": equivalente, "maximo": maximo,
        })
    return areas


def carregar_notas(usuario_id):
    respostas = defaultdict(list)
    for linha in listar_acertos_por_tentativa(usuario_id):
        respostas[linha["resultado_id"]].append(linha["questao_numero"])

    provas = {}
    enem = {}
    ita_objetivas = []
    for resultado in listar_resultados_usuario(usuario_id):
        prova_id = resultado["prova_id"]
        if prova_id not in provas:
            provas[prova_id] = obter_prova(prova_id)
        prova = provas[prova_id]
        if prova is None:
            continue

        area_por_numero = {q.numero: q.area for q in prova.questoes}
        acertos = Counter(
            area_por_numero[numero] for numero in respostas[resultado["id"]]
            if numero in area_por_numero
        )
        # Resultados antigos podem ter só o total, sem respostas por tentativa.
        tem_detalhes = sum(acertos.values()) == resultado["acertos"]
        if prova.tipo == "ENEM":
            edicao = enem.setdefault(prova.nome, {"Primeiro Dia": [], "Segundo Dia": []})
            edicao[prova.dia].append({
                **resultado,
                "areas": detalhar_enem(prova, resultado, acertos) if tem_detalhes else [],
            })
        elif prova.tipo == "ITA":
            ita_objetivas.append({
                **resultado,
                "primeira_fase": prova.dia == "Primeira Fase",
                "avaliacao": avaliar_ita(acertos) if prova.dia == "Primeira Fase" and tem_detalhes else None,
            })

    ita_discursivas = [
        {**tentativa, **resumir_correcao_discursiva(tentativa)}
        for tentativa in listar_tentativas_discursivas_usuario(usuario_id)
        if tentativa["instituicao"] == "ITA" and tentativa["status"] in ("finalizada", "corrigida")
    ]
    return {"enem": enem, "ita_objetivas": ita_objetivas, "ita_discursivas": ita_discursivas}
