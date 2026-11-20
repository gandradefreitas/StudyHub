"""Verificação numérica (exata, aproximada, com regra de precisão)."""

import math
import re
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, localcontext
from fractions import Fraction

import sympy as sp

from .contrato import (
    STATUS_CONDICIONAL,
    STATUS_CORRETO,
    STATUS_INCORRETO,
    STATUS_INDETERMINADO,
    _ERROS_DE_ENTRADA,
    _resultado_invalido,
    montar_resultado,
)
from .interpretador import interpretar_expressao
from .normalizacao import normalizar_entrada
from .tempo import _interface_protegida


# ----------------------------------------------------------------
# Verificação numérica
# ----------------------------------------------------------------
_PRECISAO_AVALIACAO = 60


_PRECISAO_DECIMAL = 400


_MODOS_DE_ARREDONDAMENTO = {
    "arredondamento": (ROUND_HALF_UP,),
    "truncamento": (ROUND_DOWN,),
    "qualquer": (ROUND_HALF_UP, ROUND_DOWN)
}


_REGEX_DECIMAL = re.compile(
    r"^(?:[+-]\s?)?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$"
)


_CONDICAO_DE_PRECISAO = (
    "definir a regra de precisão (casas decimais ou tolerância)"
)


def _como_texto(valor):
    if isinstance(valor, bool):
        raise ValueError("Valor numérico inválido.")

    if isinstance(valor, float) and not math.isfinite(valor):
        raise ValueError("Valor numérico inválido.")

    if isinstance(valor, (int, float)):
        return repr(valor)

    if isinstance(valor, str):
        return valor

    raise ValueError("Valor numérico inválido.")


def _literal_decimal(texto):
    """
    Retorna um Decimal exato se o texto é um literal numérico
    simples (3, 0,5, -1.25, 1,5e2); caso contrário, None.
    """

    candidato = normalizar_entrada(texto)

    if len(candidato) > 100 or not _REGEX_DECIMAL.match(candidato):
        return None

    try:
        valor = Decimal(candidato.replace(" ", ""))
    except ArithmeticError:
        return None

    if not valor.is_finite() or abs(valor.adjusted()) > 300:
        raise ValueError("Número fora do intervalo suportado.")

    return valor


def _valor_numerico(texto):
    """
    Retorna (valor exato em SymPy, literal Decimal ou None).
    Levanta ValueError se o texto não for um número.
    """

    literal = _literal_decimal(texto)

    if literal is not None:
        fracao = Fraction(literal)

        return sp.Rational(fracao.numerator, fracao.denominator), literal

    valor = interpretar_expressao(texto)

    if valor.free_symbols:
        raise ValueError("O valor deve ser numérico, sem variáveis.")

    return valor, None


def _validar_regra_de_precisao(
        tolerancia_absoluta,
        tolerancia_relativa,
        casas_decimais,
        modo_arredondamento
):
    for nome, tolerancia in (
        ("tolerancia_absoluta", tolerancia_absoluta),
        ("tolerancia_relativa", tolerancia_relativa)
    ):
        if tolerancia is not None and (
            isinstance(tolerancia, bool)
            or not isinstance(tolerancia, (int, float))
            or not math.isfinite(tolerancia)
            or tolerancia < 0
        ):
            raise ValueError(f"{nome} deve ser um número não negativo.")

    if casas_decimais is not None and (
        isinstance(casas_decimais, bool)
        or not isinstance(casas_decimais, int)
        or not 0 <= casas_decimais <= 50
    ):
        raise ValueError("casas_decimais deve ser um inteiro entre 0 e 50.")

    if modo_arredondamento not in _MODOS_DE_ARREDONDAMENTO:
        raise ValueError(
            "modo_arredondamento deve ser 'arredondamento', "
            "'truncamento' ou 'qualquer'."
        )

    usa_tolerancia = (
        tolerancia_absoluta is not None or tolerancia_relativa is not None
    )

    if usa_tolerancia and casas_decimais is not None:
        raise ValueError(
            "Informe a tolerância ou as casas decimais, não ambas."
        )


def _iguais_exatamente(valor_1, valor_2):
    diferenca = sp.simplify(valor_1 - valor_2)

    return diferenca == 0 or diferenca.is_zero is True


def _decimal_do_valor(valor):
    """Avalia um valor exato com alta precisão, como Decimal."""

    return Decimal(str(sp.N(valor, _PRECISAO_AVALIACAO)))


def _casas(literal):
    return max(0, -literal.as_tuple().exponent)


def _quantizar(valor, casas, modo):
    return valor.quantize(Decimal(1).scaleb(-casas), rounding=modo)


def _modos_compativeis(aproximado, preciso, casas):
    """
    Modos (arredondamento, truncamento) pelos quais 'aproximado'
    é o valor 'preciso' com 'casas' casas decimais.
    """

    modos = []

    if _quantizar(preciso, casas, ROUND_HALF_UP) == aproximado:
        modos.append("arredondamento")

    if _quantizar(preciso, casas, ROUND_DOWN) == aproximado:
        modos.append("truncamento")

    return modos


@_interface_protegida
def comparar_resultado_numerico(
        esperado,
        apresentado,
        tolerancia_absoluta=None,
        tolerancia_relativa=None,
        casas_decimais=None,
        modo_arredondamento="arredondamento"
):
    """
    Compara um resultado numérico do estudante com o esperado.

    esperado, apresentado: texto ou número (1/3, 0,5, 1,5e2,
        sqrt(2)). Os valores são tratados de forma exata, sem
        ponto flutuante.

    Regra de precisão (use no máximo uma):
        casas_decimais: o apresentado deve ser o esperado
            arredondado ou truncado a essa quantidade de casas,
            conforme modo_arredondamento ("arredondamento",
            "truncamento" ou "qualquer").
        tolerancia_absoluta e/ou tolerancia_relativa: a diferença
            deve ser menor ou igual ao maior dos limites.

    status:
        correct: exatamente igual, ou dentro da regra informada.
        conditional: sem regra, mas o decimal é um arredondamento
            ou truncamento do valor esperado.
        incorrect: incompatível.
        invalid: entrada não numérica.

    detalhes["tipo"]: exato, arredondado_conforme_regra,
        dentro_da_tolerancia, aproximado_sem_regra, incompativel.
    """

    try:
        _validar_regra_de_precisao(
            tolerancia_absoluta,
            tolerancia_relativa,
            casas_decimais,
            modo_arredondamento
        )

        valor_esperado, literal_esperado = _valor_numerico(
            _como_texto(esperado)
        )
        valor_apresentado, literal_apresentado = _valor_numerico(
            _como_texto(apresentado)
        )

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    diferenca = abs(valor_esperado - valor_apresentado)

    detalhes = {
        "valor_esperado": str(valor_esperado),
        "valor_apresentado": str(valor_apresentado),
        "valor_esperado_decimal": str(sp.N(valor_esperado, 15)),
        "diferenca_absoluta": str(sp.N(diferenca, 15)),
        "diferenca_relativa": (
            str(sp.N(diferenca / abs(valor_esperado), 15))
            if valor_esperado != 0
            else None
        ),
        "casas_decimais_apresentadas": (
            _casas(literal_apresentado)
            if literal_apresentado is not None
            else None
        ),
        "regra": None
    }

    if _iguais_exatamente(valor_esperado, valor_apresentado):
        detalhes["tipo"] = "exato"

        return montar_resultado(
            STATUS_CORRETO,
            "Os valores são exatamente iguais.",
            detalhes=detalhes
        )

    try:
        with localcontext() as contexto:
            contexto.prec = _PRECISAO_DECIMAL

            decimal_esperado = _decimal_do_valor(valor_esperado)
            decimal_apresentado = _decimal_do_valor(valor_apresentado)

            # Regra: casas decimais.
            if casas_decimais is not None:
                detalhes["regra"] = {
                    "casas_decimais": casas_decimais,
                    "modo": modo_arredondamento
                }

                aceito = any(
                    _quantizar(decimal_esperado, casas_decimais, modo)
                    == decimal_apresentado
                    for modo in _MODOS_DE_ARREDONDAMENTO[
                        modo_arredondamento
                    ]
                )

                if aceito:
                    detalhes["tipo"] = "arredondado_conforme_regra"

                    return montar_resultado(
                        STATUS_CORRETO,
                        f"O valor corresponde ao esperado com "
                        f"{casas_decimais} casa(s) decimal(is).",
                        detalhes=detalhes
                    )

                detalhes["tipo"] = "incompativel"

                return montar_resultado(
                    STATUS_INCORRETO,
                    "O valor não corresponde ao esperado com a "
                    "precisão exigida.",
                    detalhes=detalhes
                )

            # Regra: tolerância.
            if (
                tolerancia_absoluta is not None
                or tolerancia_relativa is not None
            ):
                limite = Decimal(0)

                if tolerancia_absoluta is not None:
                    limite = max(
                        limite,
                        Decimal(str(tolerancia_absoluta))
                    )

                if tolerancia_relativa is not None:
                    limite = max(
                        limite,
                        Decimal(str(tolerancia_relativa))
                        * abs(decimal_esperado)
                    )

                detalhes["regra"] = {
                    "tolerancia_absoluta": (
                        None if tolerancia_absoluta is None
                        else str(tolerancia_absoluta)
                    ),
                    "tolerancia_relativa": (
                        None if tolerancia_relativa is None
                        else str(tolerancia_relativa)
                    )
                }

                if abs(decimal_esperado - decimal_apresentado) <= limite:
                    detalhes["tipo"] = "dentro_da_tolerancia"

                    return montar_resultado(
                        STATUS_CORRETO,
                        "A diferença está dentro da tolerância.",
                        detalhes=detalhes
                    )

                detalhes["tipo"] = "incompativel"

                return montar_resultado(
                    STATUS_INCORRETO,
                    "A diferença excede a tolerância.",
                    detalhes=detalhes
                )

            # Sem regra: procura evidência de aproximação decimal.
            modos = []
            lado = None
            casas = None

            if (
                literal_apresentado is not None
                and _casas(literal_apresentado) >= 1
            ):
                casas = _casas(literal_apresentado)
                lado = "apresentado"
                modos = _modos_compativeis(
                    literal_apresentado,
                    decimal_esperado,
                    casas
                )

            if (
                not modos
                and literal_esperado is not None
                and literal_apresentado is None
                and _casas(literal_esperado) >= 1
            ):
                casas = _casas(literal_esperado)
                lado = "esperado"
                modos = _modos_compativeis(
                    literal_esperado,
                    decimal_apresentado,
                    casas
                )

            if modos:
                detalhes["tipo"] = "aproximado_sem_regra"
                detalhes["modos_compativeis"] = modos
                detalhes["lado_aproximado"] = lado
                detalhes["casas_decimais_aproximadas"] = casas

                return montar_resultado(
                    STATUS_CONDICIONAL,
                    "Os valores não são exatamente iguais, mas um deles "
                    "é uma aproximação decimal do outro.",
                    condicoes=[_CONDICAO_DE_PRECISAO],
                    detalhes=detalhes
                )

            detalhes["tipo"] = "incompativel"

            return montar_resultado(
                STATUS_INCORRETO,
                "Os valores são incompatíveis.",
                detalhes=detalhes
            )

    except (ArithmeticError, ValueError, TypeError):
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível comparar os valores com segurança.",
            detalhes=detalhes
        )
