"""Variáveis, restrições e domínio de validade."""

import ast
import itertools

import sympy as sp

from .interpretador import interpretar_expressao
from .normalizacao import _analisar_sintaxe


def verificar_condicoes_dominio(condicoes, valores):
    """
    Verifica se todas as condições de domínio
    são satisfeitas para os valores informados.

    Retorna:
        True: todas satisfeitas.
        False: alguma condição não satisfeita.
        None: não foi possível determinar.
    """

    for condicao in condicoes:

        try:
            resultado = condicao.subs(valores)

            resultado = sp.simplify(resultado)

            if resultado is sp.false:
                return False

            if resultado is not sp.true:
                return None

        except (TypeError, ValueError, ZeroDivisionError):
            return None

    return True


def identificar_denominadores(expressao):
    try:
        arvore = _analisar_sintaxe(expressao)

        denominadores = []

        for no in ast.walk(arvore):

            if not isinstance(no, ast.BinOp):
                continue

            # Divisão: o denominador é o operando da direita.
            if isinstance(no.op, ast.Div):
                denominadores.append(
                    interpretar_expressao(ast.unparse(no.right))
                )

            # Potência de expoente inteiro negativo: a base
            # funciona como denominador.
            elif isinstance(no.op, ast.Pow):
                expoente = interpretar_expressao(ast.unparse(no.right))

                if expoente.is_Integer and expoente < 0:
                    denominadores.append(
                        interpretar_expressao(ast.unparse(no.left))
                    )

        return denominadores

    except (
        ValueError,
        TypeError,
        SyntaxError,
        ZeroDivisionError,
        OverflowError
    ):
        return None


def obter_condicoes_denominadores(expressao):
    denominadores = identificar_denominadores(expressao)

    if denominadores is None:
        return None

    condicoes = []

    for denominador in denominadores:

        if denominador == 0:
            return None

        if denominador.free_symbols:
            condicoes.append(
                sp.Ne(denominador, 0, evaluate=False)
            )

    return condicoes


def obter_condicoes_dominio_expressao(expressao):
    """
    Condições Ne(denominador, 0) e Ge(radicando, 0) de uma
    expressão. Retorna None se não for possível determinar.
    """

    try:
        denominadores = obter_condicoes_denominadores(expressao)
        raizes = obter_condicoes_raizes(expressao)

    except (ValueError, TypeError, SyntaxError):
        return None

    if denominadores is None or raizes is None:
        return None

    return list(denominadores) + list(raizes)


def _normalizar_condicoes_dominio(condicoes):
    """
    Converte as condições em um conjunto canônico:
        Ne(f, 0): um item por fator irredutível de f.
        Ge(r, 0): r fatorado.
    Descarta as condições sempre verdadeiras.

    Retorna frozenset, ou None se não for possível normalizar.
    """

    try:
        chaves = set()

        for condicao in condicoes:
            expr = condicao.lhs

            if isinstance(condicao, sp.core.relational.Unequality):

                if expr.is_zero is False:
                    continue

                _, fatores = sp.factor_list(expr)

                for fator, _ in fatores:
                    if fator.is_zero is False and not fator.free_symbols:
                        continue

                    chaves.add(("ne", fator))

            elif isinstance(condicao, sp.core.relational.GreaterThan):

                if expr.is_nonnegative is True:
                    continue

                chaves.add(("ge", sp.factor(sp.expand(expr))))

            else:
                return None

        return frozenset(chaves)

    except (TypeError, ValueError, sp.PolynomialError, NotImplementedError):
        return None


def _existe_ponto_separador(condicoes_1, condicoes_2):
    """
    Procura um ponto que satisfaça exatamente um dos dois
    conjuntos de condições. Se existir, os domínios diferem.
    """

    simbolos = set()

    for condicao in list(condicoes_1) + list(condicoes_2):
        simbolos |= condicao.free_symbols

    simbolos = sorted(simbolos, key=str)

    if not simbolos or len(simbolos) > 3:
        return False

    candidatos = {
        simbolo: [0, 1, -1, 2, -2, sp.Rational(1, 2)]
        for simbolo in simbolos
    }

    # Raízes reais de condições com uma única variável.
    for condicao in list(condicoes_1) + list(condicoes_2):
        livres = condicao.lhs.free_symbols

        if len(livres) != 1:
            continue

        simbolo = next(iter(livres))

        try:
            raizes = sp.solveset(condicao.lhs, simbolo, domain=sp.S.Reals)
        except (NotImplementedError, TypeError, ValueError):
            continue

        if isinstance(raizes, sp.FiniteSet):
            candidatos[simbolo].extend(list(raizes)[:4])

    for valores in itertools.product(*(candidatos[s] for s in simbolos)):
        ponto = dict(zip(simbolos, valores))

        valido_1 = verificar_condicoes_dominio(condicoes_1, ponto)
        valido_2 = verificar_condicoes_dominio(condicoes_2, ponto)

        if (valido_1 is True and valido_2 is False) or (
            valido_1 is False and valido_2 is True
        ):
            return True

    return False


def _comparar_conjuntos_reais(conjunto_1, conjunto_2):
    """
    Compara dois conjuntos pela diferença entre eles.

    Retorna:
        True: iguais.
        False: existe elemento em um e não no outro.
        None: não foi possível determinar.
    """

    so_no_1 = sp.Complement(conjunto_1, conjunto_2)
    so_no_2 = sp.Complement(conjunto_2, conjunto_1)

    if so_no_1.is_empty is True and so_no_2.is_empty is True:
        return True

    if so_no_1.is_empty is False or so_no_2.is_empty is False:
        return False

    return None


def comparar_dominios_expressoes(expressao_1, expressao_2):
    """
    Compara os domínios reais de duas expressões.

    Retorna:
        True: domínios comprovadamente iguais.
        False: domínios comprovadamente diferentes.
        None: não foi possível determinar.
    """

    try:
        variaveis = (
            identificar_variaveis(expressao_1)
            | identificar_variaveis(expressao_2)
        )

        # Zero ou uma variável: compara os conjuntos.
        if len(variaveis) <= 1:
            dominio_1 = obter_dominio(expressao_1)
            dominio_2 = obter_dominio(expressao_2)

            if dominio_1 is None or dominio_2 is None:
                return None

            return _comparar_conjuntos_reais(dominio_1, dominio_2)

        # Várias variáveis: compara as condições.
        condicoes_1 = obter_condicoes_dominio_expressao(expressao_1)
        condicoes_2 = obter_condicoes_dominio_expressao(expressao_2)

        if condicoes_1 is None or condicoes_2 is None:
            return None

        chaves_1 = _normalizar_condicoes_dominio(condicoes_1)
        chaves_2 = _normalizar_condicoes_dominio(condicoes_2)

        if chaves_1 is None or chaves_2 is None:
            return None

        if chaves_1 == chaves_2:
            return True

        if _existe_ponto_separador(condicoes_1, condicoes_2):
            return False

        return None

    except (
        ValueError,
        TypeError,
        SyntaxError,
        NotImplementedError,
        ZeroDivisionError,
        sp.PolynomialError
    ):
        return None


def identificar_restricoes(expressao):

    denominadores = identificar_denominadores(expressao)

    if denominadores is None:
        return None

    variaveis = set()

    for denominador in denominadores:
        variaveis.update(denominador.free_symbols)

    if len(variaveis) > 1:
        return None

    if not variaveis:
        if any(denominador == 0 for denominador in denominadores):
            return None

        return []

    variavel = next(iter(variaveis))

    restricoes = set()

    for denominador in denominadores:
        solucoes = sp.solveset(
            denominador,
            variavel,
            domain=sp.S.Reals
        )

        if not isinstance(solucoes, sp.FiniteSet):
            if solucoes == sp.S.EmptySet:
                continue

            return None

        restricoes.update(solucoes)

    return sorted(restricoes, key=str)


def identificar_radicandos(expressao):
    arvore = _analisar_sintaxe(expressao)

    radicandos = []

    for no in ast.walk(arvore):
        if (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Name)
            and no.func.id == "sqrt"
            and len(no.args) == 1
        ):
            radicando = ast.unparse(no.args[0])
            radicandos.append(
                interpretar_expressao(radicando)
            )

    return radicandos


def obter_condicoes_raizes(expressao):
    radicandos = identificar_radicandos(expressao)

    condicoes = []

    for radicando in radicandos:

        if not radicando.free_symbols:
            if radicando.is_nonnegative is not True:
                return None

            continue

        condicoes.append(
            sp.Ge(radicando, 0, evaluate=False)
        )

    return condicoes


def identificar_restricoes_raizes(expressao):
    radicandos = identificar_radicandos(expressao)

    restricoes = []

    for radicando in radicandos:
        variaveis = radicando.free_symbols

        if len(variaveis) > 1:
            return None

        if not variaveis:
            if radicando.is_nonnegative is not True:
                return None

            continue

        variavel = next(iter(variaveis))

        try:
            valores_proibidos = sp.solve_univariate_inequality(
                radicando < 0,
                variavel,
                relational=False
            )

        except (NotImplementedError, ValueError):
            return None

        restricoes.append(valores_proibidos)

    return restricoes


def combinar_restricoes_raizes(expressao):
    restricoes = identificar_restricoes_raizes(expressao)

    if restricoes is None:
        return None

    if not restricoes:
        return sp.S.EmptySet

    return sp.Union(*restricoes)


def obter_dominio_raizes(expressao):
    restricoes = combinar_restricoes_raizes(expressao)

    if restricoes is None:
        return None

    return sp.Complement(
        sp.S.Reals,
        restricoes
    )


def obter_dominio(expressao):
    restricoes_raizes = combinar_restricoes_raizes(expressao)
    restricoes_denominadores = identificar_restricoes(expressao)

    variaveis = identificar_variaveis(expressao)

    if len(variaveis) > 1:
        return None

    if (
        restricoes_raizes is None
        or restricoes_denominadores is None
    ):
        return None

    restricoes = restricoes_raizes

    if restricoes_denominadores:
        restricoes = sp.Union(
            restricoes,
            sp.FiniteSet(*restricoes_denominadores)
        )

    return sp.Complement(
        sp.S.Reals,
        restricoes
    )


def identificar_variaveis(expressao):
    arvore = _analisar_sintaxe(expressao)

    variaveis = set()

    for no in ast.walk(arvore):
        if isinstance(no, ast.Name):
            if no.id not in ("sqrt", "abs"):
                variaveis.add(no.id)

    return variaveis


def inspecionar_variaveis_denominadores(expressao):
    denominadores = identificar_denominadores(expressao)

    variaveis = identificar_variaveis(expressao)

    if len(variaveis) > 1:
        return None

    for denominador in denominadores:
        print(
            f"Denominador: {denominador} | "
            f"Variáveis: {denominador.free_symbols}"
        )


def obter_variaveis_equacao(equacao):
    variaveis = set()

    esquerda, direita = equacao.split("=")

    for membro in (esquerda, direita):
        arvore = _analisar_sintaxe(membro.strip())

        for no in ast.walk(arvore):
            if isinstance(no, ast.Name):
                if no.id not in ("sqrt", "abs"):
                    variaveis.add(
                        sp.Symbol(no.id, real=True)
                    )

    return variaveis
