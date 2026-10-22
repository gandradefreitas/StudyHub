from dataclasses import dataclass
from models.questao import Questao

@dataclass
class Prova:

    id: int

    tipo: str

    nome: str

    dia: str | None

    areas: list[str]

    tempo: str

    total_questoes: int

    questoes: list[Questao]
