import json
from pathlib import Path

from models.questao_discursiva import (
    CriterioCorrecao,
    ItemDiscursivo,
    QuestaoDiscursiva,
    ProvaDiscursiva,
)


BASE_DIR = Path(__file__).resolve().parent.parent


def carregar_dados_prova(caminho_arquivo: str) -> dict:
    caminho = BASE_DIR / "dados" / caminho_arquivo

    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def criar_criterios(dados: list[dict]) -> list[CriterioCorrecao]:
    return [
        CriterioCorrecao(
            criterio=criterio["criterio"],
            pontos=criterio["pontos"],
        )
        for criterio in dados
    ]


def criar_itens(dados: list[dict]) -> list[ItemDiscursivo]:
    itens = []

    for item in dados:
        itens.append(
            ItemDiscursivo(
                letra=item.get("letra"),
                enunciado=item.get("enunciado"),
                valor=item["valor"],
                resposta_esperada=item["resposta_esperada"],
                resolucao_referencia=item["resolucao_referencia"],
                criterios_correcao=criar_criterios(
                    item["criterios_correcao"]
                ),
            )
        )

    return itens


def criar_questoes(dados: list[dict]) -> list[QuestaoDiscursiva]:
    questoes = []

    for questao in dados:
        questoes.append(
            QuestaoDiscursiva(
                numero=questao["numero"],
                area=questao["area"],
                enunciado=questao["enunciado"],
                imagem=questao.get("imagem"),
                itens=criar_itens(questao["itens"]),
            )
        )

    return questoes


def obter_prova_discursiva(caminho_arquivo: str) -> ProvaDiscursiva:
    dados = carregar_dados_prova(caminho_arquivo)

    return ProvaDiscursiva(
        instituicao=dados["instituicao"],
        ano=dados["ano"],
        fase=dados["fase"],
        tipo=dados["tipo"],
        tempo=dados["tempo"],
        convencoes=dados["convencoes"],
        questoes=criar_questoes(dados["questoes"]),
        disciplina=dados.get("disciplina", "Matemática"),
    )
