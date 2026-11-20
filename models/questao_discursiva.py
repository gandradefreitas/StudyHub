from dataclasses import dataclass


@dataclass
class CriterioCorrecao:
    criterio: str
    pontos: float


@dataclass
class ItemDiscursivo:
    letra: str | None
    enunciado: str | None
    valor: float
    resposta_esperada: str
    resolucao_referencia: str
    criterios_correcao: list[CriterioCorrecao]


@dataclass
class QuestaoDiscursiva:
    numero: int
    area: str
    enunciado: str
    imagem: str | None
    itens: list[ItemDiscursivo]


@dataclass
class ProvaDiscursiva:
    instituicao: str
    ano: int
    fase: str
    tipo: str
    tempo: str
    convencoes: list[str]
    questoes: list[QuestaoDiscursiva]
    disciplina: str = "Matemática"
