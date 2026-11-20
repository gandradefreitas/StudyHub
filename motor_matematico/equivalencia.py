"""Equivalência de expressões, equações e vetores de coeficientes."""

import ast
import itertools

import sympy as sp

from .dominio import (
    comparar_dominios_expressoes,
    obter_condicoes_dominio_expressao,
    verificar_condicoes_dominio,
)
from .equacoes import interpretar_equacao
from .interpretador import interpretar_expressao
from .normalizacao import _analisar_sintaxe


def _comparar_simbolicamente(
        esperado,
        apresentado,
        condicoes_dominio=()
):
    """
    Compara duas expressões SymPy como identidades.

    condicoes_dominio: condições que o ponto de um contraexemplo
    precisa satisfazer. None significa "domínio desconhecido":
    nesse caso nenhum contraexemplo numérico é aceito.

    Retorna:
        True: diferença comprovadamente nula.
        False: contraexemplo encontrado.
        None: não foi possível determinar.
    """

    diferenca = sp.simplify(esperado - apresentado)

    if diferenca == 0 or diferenca.is_zero is True:
        return True

    if diferenca.is_zero is False:
        return False

    if condicoes_dominio is None:
        return None

    simbolos = set(diferenca.free_symbols)

    for condicao in condicoes_dominio:
        simbolos |= condicao.free_symbols

    simbolos = sorted(simbolos, key=str)

    # Busca limitada, para evitar explosão combinatória.
    # Nunca é usada para provar equivalência.
    if len(simbolos) > 3:
        return None

    candidatos = [0, 1, -1, 2, sp.Rational(1, 2)]

    for valores in itertools.product(candidatos, repeat=len(simbolos)):
        ponto = dict(zip(simbolos, valores))

        # O contraexemplo precisa estar no domínio.
        if (
            condicoes_dominio
            and verificar_condicoes_dominio(
                condicoes_dominio,
                ponto
            ) is not True
        ):
            continue

        valor = diferenca.subs(ponto)

        if valor.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
            continue

        if valor.is_real is True and valor.is_zero is False:
            return False

    return None


def verificar_ponto_contraexemplo(
        diferenca,
        condicoes_origem,
        condicoes_destino,
        variaveis
):
    """
    Procura uma solução da equação de origem que não
    pertença ao domínio da equação de destino.
    """

    try:
        # Começa com a própria equação.
        equacoes = [diferenca]

        # Identifica condições do tipo Ne(expressao, 0).
        for condicao in condicoes_destino:

            if (
                isinstance(condicao, sp.core.relational.Unequality)
                and condicao.rhs == 0
            ):
                equacoes.append(condicao.lhs)

            elif (
                isinstance(condicao, sp.core.relational.Unequality)
                and condicao.lhs == 0
            ):
                equacoes.append(condicao.rhs)

        # Resolve o sistema para encontrar pontos candidatos.
        solucoes = sp.solve(
            equacoes,
            tuple(variaveis),
            dict=True
        )

        if not solucoes:
            return None

        for solucao in solucoes:

            origem_valida = verificar_condicoes_dominio(
                condicoes_origem,
                solucao
            )

            if origem_valida is False:
                continue

            if origem_valida is None:
                return None

            destino_valido = verificar_condicoes_dominio(
                condicoes_destino,
                solucao
            )

            if destino_valido is False:
                return False

            if destino_valido is None:
                return None

        return None

    except (
        TypeError,
        ValueError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def comparar_condicoes_dominio(condicoes_1, condicoes_2, variaveis):

    try:
        dominio_1 = sp.simplify(sp.And(*condicoes_1))
        dominio_2 = sp.simplify(sp.And(*condicoes_2))

        if dominio_1 == dominio_2:
            return True

        return None

    except (TypeError, ValueError, NotImplementedError):
        return None


def verificar_operacao(expressao, resultado_apresentado):
    try:
        resultado_esperado = interpretar_expressao(expressao)

        resultado_apresentado = interpretar_expressao(
            str(resultado_apresentado)
        )

        correta = _comparar_simbolicamente(
            resultado_esperado,
            resultado_apresentado
        )

        return {
            "expressao": expressao,
            "resultado_esperado": str(resultado_esperado),
            "resultado_apresentado": str(resultado_apresentado),
            "correta": correta
        }

    except (
        ValueError,
        TypeError,
        SyntaxError,
        ZeroDivisionError,
        OverflowError,
        sp.SympifyError
    ):
        return {
            "expressao": expressao,
            "resultado_esperado": None,
            "resultado_apresentado": str(resultado_apresentado),
            "correta": None,
            "erro": "Não foi possível interpretar a operação."
        }


def analisar_equivalencia_expressoes(expressao_1, expressao_2):
    """
    Analisa a equivalência considerando os domínios.

    Retorna um dicionário com:
        igualdade_algebrica: True/False/None. As expressões
            coincidem onde ambas estão definidas?
        dominios_iguais: True/False/None.
        resultado:
            "equivalentes": mesma função (mesmo domínio).
            "condicional": coincidem onde ambas existem, mas
                os domínios são diferentes (ex.: x/x e 1).
            "diferentes": comprovadamente distintas.
            "indeterminado": não foi possível concluir.
            "invalido": entrada inválida.
    """

    analise = {
        "igualdade_algebrica": None,
        "dominios_iguais": None,
        "resultado": "indeterminado"
    }

    try:
        expr_1 = interpretar_expressao(expressao_1)
        expr_2 = interpretar_expressao(expressao_2)

    except (
        ValueError,
        TypeError,
        SyntaxError,
        ZeroDivisionError,
        OverflowError,
        sp.SympifyError
    ):
        analise["resultado"] = "invalido"
        return analise

    try:
        condicoes_1 = obter_condicoes_dominio_expressao(expressao_1)
        condicoes_2 = obter_condicoes_dominio_expressao(expressao_2)

        if condicoes_1 is None or condicoes_2 is None:
            condicoes = None
        else:
            condicoes = condicoes_1 + condicoes_2

        igualdade = _comparar_simbolicamente(expr_1, expr_2, condicoes)
        dominios = comparar_dominios_expressoes(expressao_1, expressao_2)

    except (
        ValueError,
        TypeError,
        SyntaxError,
        ZeroDivisionError,
        OverflowError,
        NotImplementedError,
        sp.SympifyError,
        sp.PolynomialError
    ):
        return analise

    analise["igualdade_algebrica"] = igualdade
    analise["dominios_iguais"] = dominios

    if igualdade is False:
        analise["resultado"] = "diferentes"

    elif igualdade is True and dominios is True:
        analise["resultado"] = "equivalentes"

    elif igualdade is True and dominios is False:
        analise["resultado"] = "condicional"

    return analise


def verificar_equivalencia(expressao_1, expressao_2):
    """
    Equivalência estrita: as expressões são a mesma função,
    com o mesmo domínio.

    Retorna:
        True: equivalentes.
        False: diferentes, ou iguais apenas onde ambas estão
               definidas (domínios diferentes). Use
               analisar_equivalencia_expressoes para distinguir.
        None: não foi possível determinar, ou entrada inválida.
    """

    resultado = analisar_equivalencia_expressoes(
        expressao_1,
        expressao_2
    )["resultado"]

    if resultado == "equivalentes":
        return True

    if resultado in ("diferentes", "condicional"):
        return False

    return None


def verificar_equivalencia_equacoes(equacao_1, equacao_2):
    try:
        resultado_1 = interpretar_equacao(equacao_1)
        resultado_2 = interpretar_equacao(equacao_2)

        diferenca_1 = resultado_1["diferenca"]
        diferenca_2 = resultado_2["diferenca"]

        # Identifica as variáveis presentes nas equações originais.
        variaveis = set()

        for equacao in (equacao_1, equacao_2):
            esquerda, direita = equacao.split("=")

            for membro in (esquerda, direita):
                arvore = _analisar_sintaxe(membro.strip())

                for no in ast.walk(arvore):
                    if isinstance(no, ast.Name) and no.id not in ("sqrt", "abs"):
                        variaveis.add(sp.Symbol(no.id, real=True))

        # Aceita inicialmente apenas uma variável.
        if len(variaveis) != 1:
            return None

        variavel = next(iter(variaveis))

        def obter_solucoes(resultado):
            solucoes = sp.solveset(
                resultado["diferenca"],
                variavel,
                domain=sp.S.Reals
            )

            if not (
                    isinstance(
                        solucoes,
                        (
                                sp.FiniteSet,
                                sp.Interval,
                                sp.Union,
                                sp.Intersection,
                                sp.Complement
                        )
                    )
                    or solucoes == sp.S.EmptySet
                    or solucoes == sp.S.Reals
            ):
                return None

            # Valores proibidos pelos denominadores.
            restricoes_denominadores = (
                    resultado["restricoes_esquerda"]
                    + resultado["restricoes_direita"]
            )

            valores_proibidos = sp.FiniteSet(
                *restricoes_denominadores
            )

            # Intervalos proibidos pelas raízes.
            restricoes_raizes = (
                    resultado["restricoes_raizes_esquerda"]
                    + resultado["restricoes_raizes_direita"]
            )

            if restricoes_raizes:
                valores_proibidos = sp.Union(
                    valores_proibidos,
                    *restricoes_raizes
                )

            return sp.Complement(
                solucoes,
                valores_proibidos
            )

        solucoes_1 = obter_solucoes(resultado_1)
        solucoes_2 = obter_solucoes(resultado_2)

        if solucoes_1 is None or solucoes_2 is None:
            return None

        return solucoes_1 == solucoes_2

    except (
            ValueError,
            TypeError,
            SyntaxError,
            IndentationError,
            ZeroDivisionError,
            OverflowError,
            sp.SympifyError,
            sp.PolynomialError
    ):
        return None


def _existe_ponto_separador_equacoes(
        diferenca_1,
        diferenca_2,
        variaveis
):
    """
    Procura um ponto real onde uma das equações f = 0 é
    satisfeita e a outra não. Se existir, os conjuntos solução
    são diferentes (isso é uma prova).

    Não encontrar um ponto não prova nada.
    Não é usada quando há parâmetros livres.
    """

    variaveis = sorted(set(variaveis), key=str)

    if not variaveis or len(variaveis) > 3:
        return False

    livres = diferenca_1.free_symbols | diferenca_2.free_symbols

    if livres - set(variaveis):
        return False

    candidatos = [0, 1, -1, 2, -2, sp.Rational(1, 2)]

    for satisfeita, outra in (
        (diferenca_1, diferenca_2),
        (diferenca_2, diferenca_1)
    ):
        for resolvida in variaveis:

            fixas = [v for v in variaveis if v != resolvida]

            for valores in itertools.product(
                candidatos,
                repeat=len(fixas)
            ):
                parcial = dict(zip(fixas, valores))

                try:
                    raizes = sp.solveset(
                        satisfeita.subs(parcial),
                        resolvida,
                        domain=sp.S.Reals
                    )
                except (NotImplementedError, TypeError, ValueError):
                    continue

                if raizes == sp.S.Reals:
                    pontos = list(candidatos)

                elif isinstance(raizes, sp.FiniteSet):
                    pontos = list(raizes)[:4]

                else:
                    continue

                for raiz in pontos:
                    ponto = dict(parcial)
                    ponto[resolvida] = raiz

                    valor_satisfeita = sp.simplify(satisfeita.subs(ponto))
                    valor_outra = sp.simplify(outra.subs(ponto))

                    if (
                        valor_satisfeita == 0
                        and valor_outra.is_zero is False
                    ):
                        return True

    return False


def verificar_equivalencia_multivariavel(
        diferenca_1,
        diferenca_2,
        variaveis,
        condicoes_1=None,
        condicoes_2=None
):
    try:
        variaveis = sorted(set(variaveis), key=str)

        # Obtém os numeradores das diferenças.
        diferenca_1 = sp.together(diferenca_1).as_numer_denom()[0]
        diferenca_2 = sp.together(diferenca_2).as_numer_denom()[0]

        # Preserva a fatoração das expressões.
        diferenca_1 = sp.factor(diferenca_1)
        diferenca_2 = sp.factor(diferenca_2)

        # Verifica se as informações de domínio estão disponíveis.
        if (condicoes_1 is None) != (condicoes_2 is None):
            return None

        equivalencia_dominio = None

        if condicoes_1 is not None:

            equivalencia_dominio = comparar_condicoes_dominio(
                condicoes_1,
                condicoes_2,
                variaveis
            )

            # Procura contraexemplos nas duas direções.
            contraexemplo_1 = verificar_ponto_contraexemplo(
                diferenca_1,
                condicoes_1,
                condicoes_2,
                variaveis
            )

            contraexemplo_2 = verificar_ponto_contraexemplo(
                diferenca_2,
                condicoes_2,
                condicoes_1,
                variaveis
            )

            # Um contraexemplo demonstra a não equivalência.
            if (
                contraexemplo_1 is False
                or contraexemplo_2 is False
            ):
                return False

            # Sem equivalência de domínio comprovada,
            # não podemos afirmar equivalência.
            if equivalencia_dominio is not True:
                return None

        # As duas equações representam 0 = 0.
        if diferenca_1 == 0 and diferenca_2 == 0:
            return True

        # Apenas uma equação representa uma identidade.
        if diferenca_1 == 0 or diferenca_2 == 0:

            outra_diferenca = (
                diferenca_2 if diferenca_1 == 0
                else diferenca_1
            )

            # Identifica os parâmetros, excluindo as incógnitas.
            parametros = outra_diferenca.free_symbols - set(variaveis)

            if parametros:
                return None

            return False

        # Verifica se uma equação é múltipla da outra
        # por um fator necessariamente diferente de zero.
        try:
            razao = sp.cancel(diferenca_2 / diferenca_1)

            if razao.is_polynomial(*variaveis):

                # Sem condições de domínio, somente uma razão
                # comprovadamente não nula pode ser aceita.
                if condicoes_1 is None:
                    hipoteses = sp.true
                else:
                    hipoteses = sp.And(*condicoes_1)

                fator_nao_nulo = sp.ask(
                    sp.Q.nonzero(razao),
                    hipoteses
                )

                if fator_nao_nulo is True:
                    return True

        except (TypeError, ValueError, ZeroDivisionError):
            pass

        # Converte as expressões em polinômios.
        variaveis = sorted(variaveis, key=str)

        polinomio_1 = sp.Poly(diferenca_1, *variaveis)
        polinomio_2 = sp.Poly(diferenca_2, *variaveis)

        # Obtém todos os monômios presentes nos dois polinômios.
        monomios = set(polinomio_1.monoms()) | set(polinomio_2.monoms())

        # Obtém os coeficientes associados a cada monômio.
        coeficientes_dict_1 = dict(zip(
            polinomio_1.monoms(),
            polinomio_1.coeffs()
        ))

        coeficientes_dict_2 = dict(zip(
            polinomio_2.monoms(),
            polinomio_2.coeffs()
        ))

        # Alinha os coeficientes, considerando ausências como zero.
        monomios = sorted(monomios)

        coeficientes_1 = [
            coeficientes_dict_1.get(monomio, sp.Integer(0))
            for monomio in monomios
        ]

        coeficientes_2 = [
            coeficientes_dict_2.get(monomio, sp.Integer(0))
            for monomio in monomios
        ]

        resultado = analisar_equivalencia_vetores(
            coeficientes_1,
            coeficientes_2
        )

        # Sem conclusão: procura um ponto que prove a
        # não equivalência. Sem ponto, continua indeterminado.
        if (
            resultado is None
            and _existe_ponto_separador_equacoes(
                diferenca_1,
                diferenca_2,
                variaveis
            )
        ):
            return False

        return resultado

    except (
        TypeError,
        ValueError,
        sp.PolynomialError,
        ZeroDivisionError,
        NotImplementedError
    ):
        return None


def verificar_coeficientes_nulos(coeficientes):
    """
    Verifica se os coeficientes podem ser simultaneamente
    iguais a zero para valores reais dos parâmetros.

    Retorna:
        True: todos são identicamente zero.
        False: não podem ser simultaneamente zero.
        None: podem ser zero dependendo dos parâmetros.
    """

    coeficientes = [
        sp.factor(sp.simplify(coeficiente))
        for coeficiente in coeficientes
    ]

    # Todos são identicamente zero.
    if all(coeficiente == 0 for coeficiente in coeficientes):
        return True

    # Identifica os parâmetros.
    parametros = set()

    for coeficiente in coeficientes:
        parametros.update(coeficiente.free_symbols)

    # Sem parâmetros, não podem ser todos zero.
    if not parametros:
        return False

    # Procura valores reais que zerem todos os coeficientes.
    equacoes = [
        coeficiente
        for coeficiente in coeficientes
        if coeficiente != 0
    ]

    solucoes = sp.solve(
        equacoes,
        sorted(parametros, key=str),
        dict=True
    )

    if solucoes:
        return None

    return False


def verificar_proporcionalidade_vetores(coeficientes_1, coeficientes_2):
    """
    Verifica se dois vetores de coeficientes são
    proporcionalmente relacionados por meio de produtos cruzados.

    Não realiza divisões entre coeficientes.

    Retorna:
        True: todos os produtos cruzados são identicamente zero.
        False: pelo menos um produto cruzado não é identicamente zero.
        None: não foi possível determinar.
    """

    if len(coeficientes_1) != len(coeficientes_2):
        raise ValueError("Os vetores devem possuir o mesmo tamanho.")

    condicoes = []

    for i in range(len(coeficientes_1)):
        for j in range(i + 1, len(coeficientes_1)):

            condicao = sp.simplify(
                coeficientes_1[i] * coeficientes_2[j]
                - coeficientes_1[j] * coeficientes_2[i]
            )

            condicoes.append(condicao)

    # Todos os produtos cruzados são identicamente zero.
    if all(condicao == 0 for condicao in condicoes):
        return True

    # Pelo menos um produto cruzado não é identicamente zero.
    if any(condicao.is_zero is False for condicao in condicoes):
        return False

    return None


def obter_condicoes_anulacao(coeficientes):
    """
    Obtém as condições necessárias para que todos os
    coeficientes de um vetor sejam simultaneamente zero.

    Retorna uma lista de expressões.
    """

    condicoes = []

    for coeficiente in coeficientes:

        coeficiente = sp.factor(
            sp.simplify(coeficiente)
        )

        if coeficiente != 0:
            condicoes.append(coeficiente)

    return condicoes


def verificar_condicoes_anulacao(condicoes):
    """
    Verifica se as condições de anulação podem ser
    satisfeitas simultaneamente por valores reais.

    Retorna:
        True: existe uma solução real.
        False: não existe solução real.
        None: não foi possível determinar com segurança.
    """

    # Nenhuma condição precisa ser satisfeita.
    if not condicoes:
        return True

    # Identifica os parâmetros presentes nas condições.
    parametros = set()

    for condicao in condicoes:
        parametros.update(condicao.free_symbols)

    # Caso sem parâmetros.
    if not parametros:
        return False

    # Por enquanto, trabalhamos com apenas um parâmetro.
    if len(parametros) != 1:
        return None

    parametro = next(iter(parametros))

    try:
        # Começa considerando todos os números reais.
        solucoes = sp.S.Reals

        # Intersecta as soluções de cada condição.
        for condicao in condicoes:

            conjunto = sp.solveset(
                condicao,
                parametro,
                domain=sp.S.Reals
            )

            solucoes = sp.Intersection(
                solucoes,
                conjunto
            )

            # Nenhum valor satisfaz todas as condições.
            if solucoes is sp.S.EmptySet:
                return False

        # Verifica se o conjunto final está vazio.
        if solucoes.is_empty is True:
            return False

        if solucoes.is_empty is False:
            return True

        return None

    except (
        TypeError,
        ValueError,
        NotImplementedError,
        sp.SympifyError
    ):
        return None


def analisar_equivalencia_vetores(coeficientes_1, coeficientes_2):
    """
    Analisa a equivalência entre dois vetores de coeficientes.

    Retorna:
        True: equivalência para todos os valores reais
              dos parâmetros.
        False: apenas quando um dos vetores é identicamente nulo
               e o outro nunca pode ser nulo.
        None: equivalência condicional, indeterminada ou vetores
              não proporcionais (sem prova de não equivalência).
    """

    if len(coeficientes_1) != len(coeficientes_2):
        raise ValueError("Os vetores devem possuir o mesmo tamanho.")

    # Converte todos os coeficientes para objetos SymPy.
    coeficientes_1 = [
        sp.sympify(coeficiente)
        for coeficiente in coeficientes_1
    ]

    coeficientes_2 = [
        sp.sympify(coeficiente)
        for coeficiente in coeficientes_2
    ]

    # Identifica os parâmetros presentes nos vetores.
    parametros = set()

    for coeficiente in coeficientes_1 + coeficientes_2:
        parametros.update(coeficiente.free_symbols)

    # Verifica a proporcionalidade algébrica.
    proporcionalidade = verificar_proporcionalidade_vetores(
        coeficientes_1,
        coeficientes_2
    )

    # Vetores não proporcionais NÃO implicam conjuntos solução
    # diferentes (ex.: x²+y²=0 e x²+2y²=0 têm o mesmo conjunto
    # solução real). A não equivalência só pode ser provada por
    # um ponto separador (ver verificar_equivalencia_multivariavel).
    if proporcionalidade is False:
        return None

    if proporcionalidade is None:
        return None

    # Obtém as condições de anulação dos dois vetores.
    condicoes_1 = obter_condicoes_anulacao(coeficientes_1)
    condicoes_2 = obter_condicoes_anulacao(coeficientes_2)

    # Ambos os vetores são identicamente nulos.
    if not condicoes_1 and not condicoes_2:
        return True

    # Verifica se apenas um dos vetores é identicamente nulo.
    if not condicoes_1 and condicoes_2:

        if verificar_condicoes_anulacao(condicoes_2) is False:
            return False

        return None

    if not condicoes_2 and condicoes_1:

        if verificar_condicoes_anulacao(condicoes_1) is False:
            return False

        return None

    # Analisa se cada vetor pode ser simultaneamente nulo.
    nulo_1 = verificar_condicoes_anulacao(condicoes_1)
    nulo_2 = verificar_condicoes_anulacao(condicoes_2)

    # Ambos nunca podem ser nulos.
    if nulo_1 is False and nulo_2 is False:
        return True

    # Apenas um dos vetores pode ser nulo.
    if nulo_1 != nulo_2:
        if nulo_1 is not None and nulo_2 is not None:
            return None

    # Sem parâmetros, podemos comparar diretamente.
    if not parametros:
        return (
            True
            if all(c == 0 for c in coeficientes_1)
            == all(c == 0 for c in coeficientes_2)
            else False
        )

    # Comparamos os fatores comuns sem dividir
    # expressões que dependam dos parâmetros.
    try:
        fator_bruto_1 = sp.gcd_list(coeficientes_1)
        fator_bruto_2 = sp.gcd_list(coeficientes_2)

        # Calcula a parte livre de quadrados somente
        # quando o fator possui variáveis simbólicas.
        fator_1 = (
            sp.sqf_part(fator_bruto_1)
            if fator_bruto_1.free_symbols
            else fator_bruto_1
        )

        fator_2 = (
            sp.sqf_part(fator_bruto_2)
            if fator_bruto_2.free_symbols
            else fator_bruto_2
        )

        razao = sp.simplify(fator_1 / fator_2)

        if not razao.free_symbols and razao.is_zero is False:
            return True

    except (
            TypeError,
            ValueError,
            sp.PolynomialError,
            ZeroDivisionError
    ):
        return None

    # Para os demais casos com múltiplos parâmetros,
    # ainda não temos um procedimento geral de decisão.
    if len(parametros) != 1:
        return None
