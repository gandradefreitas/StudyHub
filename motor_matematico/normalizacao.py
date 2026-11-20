"""Normalização da notação do estudante (², ^, vírgula decimal, multiplicação implícita)."""

import ast
import re


_SUPERESCRITOS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


_SUBSTITUICOES = {
    "−": "-",
    "–": "-",
    "×": "*",
    "·": "*",
    "÷": "/",
}


_REGEX_TOKEN = re.compile(
    r"(?P<NUM>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<NOME>[^\W\d]\w*)"
    r"|(?P<OP>\*\*|\S)"
)


def normalizar_entrada(texto):
    """
    Converte a notação usada por estudantes para sintaxe
    Python, sem interpretar o significado matemático.

    Converte: ², ³, ⁻¹, ^, ×, ·, ÷, −, vírgula decimal e
    multiplicação implícita.

    Rejeita (ValueError) o que seria ambíguo:
        - multiplicação implícita logo após divisão: 1/2x
        - número seguido de j/J: 2j
    """

    if not isinstance(texto, str):
        return texto

    for original, novo in _SUBSTITUICOES.items():
        texto = texto.replace(original, novo)

    texto = re.sub(
        r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+",
        lambda m: "**" + m.group().translate(_SUPERESCRITOS),
        texto
    )

    # Vírgula entre dígitos é separador decimal.
    texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)

    tokens = [
        (m.lastgroup, "**" if m.group() == "^" else m.group())
        for m in _REGEX_TOKEN.finditer(texto)
    ]

    saida = []
    pilha = []              # token anterior a cada "(" aberto
    anterior = None         # (tipo, texto) do token anterior
    antes_do_atomo = None   # token anterior ao último operando

    for tipo, txt in tokens:

        multiplica = False

        if anterior is not None:
            tipo_ant, txt_ant = anterior

            if tipo_ant == "NUM" and tipo == "NOME" and txt in ("j", "J"):
                raise ValueError("Número complexo não permitido.")

            multiplica = (
                (
                    (tipo_ant == "NUM" or txt_ant == ")")
                    and (tipo == "NOME" or txt == "(")
                )
                or (txt_ant == ")" and tipo == "NUM")
                or (
                    tipo_ant == "NOME"
                    and len(txt_ant) == 1
                    and txt == "("
                )
            )

        if multiplica:
            if antes_do_atomo == "/":
                raise ValueError(
                    "Multiplicação implícita ambígua após divisão; "
                    "use parênteses."
                )

            saida.append("*")
            antes_do_novo = "*"
        else:
            antes_do_novo = anterior[1] if anterior else None

        if txt == "(":
            chamada_de_funcao = (
                anterior is not None
                and anterior[0] == "NOME"
                and not multiplica
            )

            pilha.append(
                antes_do_atomo if chamada_de_funcao else antes_do_novo
            )

        elif txt == ")":
            antes_do_atomo = pilha.pop() if pilha else None

        elif tipo in ("NUM", "NOME"):
            antes_do_atomo = antes_do_novo

        saida.append(txt)
        anterior = (tipo, txt)

    return " ".join(saida)


def _analisar_sintaxe(expressao):
    """Ponto único de entrada para o ast.parse."""

    if not isinstance(expressao, str):
        raise ValueError("Expressão inválida.")

    return ast.parse(normalizar_entrada(expressao), mode="eval")
