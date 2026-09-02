from dataclasses import dataclass

@dataclass
class Questao:

    numero: int

    area: str

    lingua: str | None

    habilidade: str

    competencia: str

    dificuldade: str

    enunciado: str

    pergunta: str | None

    imagem: str | None

    alternativas: list[str]

    resposta: int

    comentario: str