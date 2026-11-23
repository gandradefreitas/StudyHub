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

    @property
    def dados_aplicacao(self) -> dict:
        return {
            "numero": self.numero,
            "lingua": self.lingua,
            "enunciado": self.enunciado,
            "pergunta": self.pergunta,
            "imagem": self.imagem,
            "alternativas": self.alternativas,
        }