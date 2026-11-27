from models.questao import Questao
from models.prova import Prova

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def listar_provas():

    caminho = BASE_DIR / "dados" / "provas.json"

    with open(
        caminho,
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)


def obter_catalogo_por_id(id_prova):

    provas = listar_provas()

    for prova in provas:

        if prova["id"] == id_prova:

            return prova

    return None


def carregar_questoes(caminho_arquivo):

    caminho = BASE_DIR / "dados" / caminho_arquivo

    if not caminho.exists():

        return []

    with open(
        caminho,
        encoding="utf-8"
    ) as arquivo:

        return json.load(arquivo)


def obter_prova(id_prova):

    catalogo = obter_catalogo_por_id(id_prova)

    if catalogo is None:
        return None

    dados = carregar_questoes(catalogo["arquivo"])
    questoes = criar_questoes([questao for questao in dados if not questao.get("anulada")])
    anuladas = tuple(questao["numero"] for questao in dados if questao.get("anulada"))

    return Prova(
        id=catalogo["id"],
        tipo=catalogo["tipo"],
        nome=catalogo["nome"],
        dia=catalogo.get("dia"),
        areas=catalogo["areas"],
        tempo=catalogo["tempo"],
        total_questoes=catalogo.get("total_questoes", len(questoes)),
        questoes=questoes,
        questoes_anuladas=anuladas,
    )


def criar_questoes(dados):

    questoes = []

    for questao in dados:
        resposta = questao["resposta"]
        if isinstance(resposta, str):
            if len(resposta) != 1 or resposta not in "ABCDE":
                raise ValueError(f'Gabarito inválido na questão {questao["numero"]}.')
            resposta = "ABCDE".index(resposta)

        questoes.append(
            Questao(
                numero=questao["numero"],
                area=questao["area"],
                lingua=questao.get("lingua"),
                habilidade=questao["habilidade"],
                competencia=questao["competencia"],
                dificuldade=questao["dificuldade"],
                enunciado=questao["enunciado"],
                pergunta=questao.get("pergunta"),
                imagem=questao["imagem"],
                alternativas=questao["alternativas"],
                resposta=resposta,
                comentario=questao["comentario"],
                enunciado_apos_imagem=questao.get("enunciado_apos_imagem"),
            )
        )

    return questoes
