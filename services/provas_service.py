from models.questao import Questao
from models.prova import Prova
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def listar_provas():

    caminho = BASE_DIR / "dados" / "provas.json"

    with open(caminho, encoding="utf-8") as arquivo:

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

    with open(caminho, encoding="utf-8") as arquivo:

        return json.load(arquivo)

def obter_prova(id_prova):

    catalogo = obter_catalogo_por_id(id_prova)

    if catalogo is None:
        return None

    dados = carregar_questoes(catalogo["arquivo"])

    questoes = criar_questoes(dados)

    return Prova(

        id=catalogo["id"],
        nome=catalogo["nome"],
        dia=catalogo["dia"],
        tempo=catalogo["tempo"],
        total_questoes=len(questoes),
        questoes=questoes

    )

def criar_questoes(dados):

    questoes = []

    for questao in dados:

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
                resposta=questao["resposta"],
                comentario=questao["comentario"]

            )

        )

    return questoes