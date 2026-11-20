"""Interpretador seguro de expressões matemáticas."""

import ast

import sympy as sp

from .normalizacao import _analisar_sintaxe


_LIMITE_BITS = 10_000


def _validar_tamanho_numerico(valor):
    """Rejeita números racionais com representação grande demais."""

    if valor.is_Rational:
        bits = max(
            int(abs(valor.p)).bit_length(),
            int(valor.q).bit_length()
        )

        if bits > _LIMITE_BITS:
            raise ValueError("Número muito grande.")

    return valor


def interpretar_expressao(expressao):
    """
    Interpreta uma expressão matemática utilizando apenas
    operações explicitamente autorizadas.
    """

    if not isinstance(expressao, str) or len(expressao) > 200:
        raise ValueError("Expressão inválida.")

    arvore = _analisar_sintaxe(expressao)

    if sum(1 for _ in ast.walk(arvore)) > 50:
        raise ValueError("Expressão muito complexa.")

    def converter(no):

        # Números inteiros e decimais
        if isinstance(no, ast.Constant):
            if isinstance(no.value, bool):
                raise ValueError("Valor booleano não permitido.")

            if isinstance(no.value, int):
                if abs(no.value) > 10**15:
                    raise ValueError("Número muito grande.")

                return sp.Integer(no.value)

            if isinstance(no.value, float):
                return sp.Rational(str(no.value))

            raise ValueError("Tipo de valor não permitido.")

        # Variáveis matemáticas
        if isinstance(no, ast.Name):
            if len(no.id) != 1 or not no.id.isalpha():
                raise ValueError("Variável não permitida.")

            return sp.Symbol(no.id, real=True)

        # Operações matemáticas
        if isinstance(no, ast.BinOp):

            esquerda = converter(no.left)
            direita = converter(no.right)

            if isinstance(no.op, ast.Add):
                return esquerda + direita

            if isinstance(no.op, ast.Sub):
                return esquerda - direita

            if isinstance(no.op, ast.Mult):
                return _validar_tamanho_numerico(esquerda * direita)

            if isinstance(no.op, ast.Div):
                if direita == 0:
                    raise ValueError("Divisão por zero não permitida.")

                return esquerda / direita

            if isinstance(no.op, ast.Pow):
                if direita.is_Integer is not True:
                    raise ValueError("Expoente deve ser inteiro.")

                if abs(int(direita)) > 100:
                    raise ValueError("Expoente muito grande.")

                if esquerda == 0 and direita < 0:
                    raise ValueError("Zero não pode ter expoente negativo.")

                if esquerda.is_Rational:
                    bits_base = max(
                        int(abs(esquerda.p)).bit_length(),
                        int(esquerda.q).bit_length()
                    )

                    if bits_base * abs(int(direita)) > _LIMITE_BITS:
                        raise ValueError("Resultado da potência muito grande.")

                resultado = esquerda ** direita

                if (
                    resultado.is_Pow
                    and resultado.exp.is_Integer
                    and abs(int(resultado.exp)) > 100
                ):
                    raise ValueError("Expoente efetivo muito grande.")

                return _validar_tamanho_numerico(resultado)

            raise ValueError("Operação não permitida.")

        # Sinais positivo e negativo
        if isinstance(no, ast.UnaryOp):

            valor = converter(no.operand)

            if isinstance(no.op, ast.UAdd):
                return valor

            if isinstance(no.op, ast.USub):
                return -valor

            raise ValueError("Operação não permitida.")

        # Funções matemáticas autorizadas
        if isinstance(no, ast.Call):

            if not isinstance(no.func, ast.Name):
                raise ValueError("Função não permitida.")

            if no.func.id not in ("sqrt", "abs"):
                raise ValueError("Função não permitida.")

            if len(no.args) != 1 or no.keywords:
                raise ValueError("Argumentos inválidos.")

            argumento = converter(no.args[0])

            # Valor absoluto
            if no.func.id == "abs":
                return sp.Abs(argumento)

            # Raiz quadrada
            if argumento.is_real is False:
                raise ValueError("Radicando não real.")

            if argumento.is_negative is True:
                raise ValueError(
                    "Raiz quadrada de número negativo não permitida."
                )

            return sp.sqrt(argumento)


        raise ValueError("Expressão contém elementos não permitidos.")

    return converter(arvore.body)
