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

    enunciado_apos_imagem: str | None = None

    @property
    def dados_aplicacao(self) -> dict:
        return {
            "numero": self.numero,
            "lingua": self.lingua,
            "enunciado": self.enunciado,
            "pergunta": self.pergunta,
            "imagem": self.imagem,
            "enunciado_apos_imagem": self.enunciado_apos_imagem,
            "alternativas": self.alternativas,
        }