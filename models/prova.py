from dataclasses import dataclass
from models.questao import Questao

@dataclass
class Prova:

    id: int

    nome: str

    dia: str

    tempo: str

    total_questoes: int

    questoes: list[Questao]