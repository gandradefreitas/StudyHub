"""Resolução de equações reais de uma variável."""

import sympy as sp

from .contrato import (
    STATUS_CORRETO,
    STATUS_INCORRETO,
    STATUS_INDETERMINADO,
    _ERROS_DE_ENTRADA,
    _formatar_condicoes,
    _resultado_invalido,
    montar_resultado,
)
from .dominio import (
    obter_variaveis_equacao,
    verificar_condicoes_dominio,
)
from .equacoes import (
    interpretar_equacao,
    obter_condicoes_dominio,
)
from .interpretador import interpretar_expressao
from .tempo import _interface_protegida


# ----------------------------------------------------------------
# Resolução de equações
# ----------------------------------------------------------------
def _conjunto_resolvido(conjunto):
    """True se o conjunto é um resultado concreto do SymPy."""

    if conjunto.has(sp.ConditionSet, sp.ImageSet):
        return False

    return (
        isinstance(conjunto, (sp.FiniteSet, sp.Interval, sp.Union))
        or conjunto == sp.S.EmptySet
    )


def _ordenar_reais(valores):
    try:
        return sorted(valores, key=lambda valor: float(valor))
    except (TypeError, ValueError):
        return sorted(valores, key=str)


def obter_conjunto_solucao_equacao(equacao):
    """
    Resolve uma equação real de uma variável.

    Retorna um dicionário com:
        variavel
        conjunto: conjunto solução (domínio já descontado).
        candidatas: soluções antes de descontar o domínio.
        descartadas_dominio: candidatas que violam o domínio.
        descartadas_verificacao: candidatas que não satisfazem
            a equação original.
        condicoes_dominio: condições de existência.

    Retorna None quando não é possível resolver.
    Levanta ValueError para equação inválida.
    """

    dados = interpretar_equacao(equacao)
    variaveis = obter_variaveis_equacao(equacao)

    if len(variaveis) != 1:
        return None

    variavel = next(iter(variaveis))

    try:
        candidatas = sp.solveset(
            dados["diferenca"],
            variavel,
            domain=sp.S.Reals
        )
    except (NotImplementedError, TypeError, ValueError, sp.PolynomialError):
        return None

    if not _conjunto_resolvido(candidatas):
        return None

    # Valores proibidos pelos denominadores e pelos radicais.
    proibidos = sp.FiniteSet(
        *(dados["restricoes_esquerda"] + dados["restricoes_direita"])
    )

    restricoes_raizes = (
        dados["restricoes_raizes_esquerda"]
        + dados["restricoes_raizes_direita"]
    )

    if restricoes_raizes:
        proibidos = sp.Union(proibidos, *restricoes_raizes)

    conjunto = sp.Complement(candidatas, proibidos)
    descartadas_dominio = sp.Intersection(candidatas, proibidos)

    if not _conjunto_resolvido(conjunto):
        return None

    # Verificação por substituição na equação original.
    descartadas_verificacao = []

    if isinstance(conjunto, sp.FiniteSet):
        validas = []

        for candidata in conjunto:
            residuo = sp.simplify(
                (dados["esquerda"] - dados["direita"]).subs(
                    variavel,
                    candidata
                )
            )

            if residuo.is_zero is False:
                descartadas_verificacao.append(candidata)
            else:
                validas.append(candidata)

        conjunto = sp.FiniteSet(*validas)

    return {
        "variavel": variavel,
        "conjunto": conjunto,
        "candidatas": candidatas,
        "descartadas_dominio": descartadas_dominio,
        "descartadas_verificacao": descartadas_verificacao,
        "condicoes_dominio": obter_condicoes_dominio(dados)
    }


@_interface_protegida
def resolver_equacao(equacao):
    """
    Determina o conjunto solução de uma equação real de uma
    variável, considerando as restrições de domínio.

    detalhes:
        tipo: "finito", "vazio" ou "infinito".
        quantidade: número de soluções (None se infinito).
        solucoes: lista de soluções (apenas se finito).
        conjunto_solucao: representação do conjunto.
        descartadas_por_dominio: candidatas eliminadas pelo domínio.
        descartadas_por_verificacao: candidatas que não satisfazem
            a equação.
    """

    try:
        resolucao = obter_conjunto_solucao_equacao(equacao)
    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    if resolucao is None:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível resolver a equação. Apenas equações "
            "reais de uma variável, sem parâmetros, são suportadas."
        )

    conjunto = resolucao["conjunto"]

    descartadas_dominio = resolucao["descartadas_dominio"]

    if isinstance(descartadas_dominio, sp.FiniteSet):
        descartadas_dominio = [
            str(valor) for valor in _ordenar_reais(descartadas_dominio)
        ]
    else:
        descartadas_dominio = []

    detalhes = {
        "variavel": str(resolucao["variavel"]),
        "conjunto_solucao": str(conjunto),
        "solucoes": [],
        "descartadas_por_dominio": descartadas_dominio,
        "descartadas_por_verificacao": [
            str(valor)
            for valor in _ordenar_reais(resolucao["descartadas_verificacao"])
        ]
    }

    if conjunto == sp.S.EmptySet:
        detalhes["tipo"] = "vazio"
        detalhes["quantidade"] = 0
        justificativa = "A equação não possui solução real."

    elif isinstance(conjunto, sp.FiniteSet):
        quantidade = len(conjunto)

        detalhes["tipo"] = "finito"
        detalhes["quantidade"] = quantidade
        detalhes["solucoes"] = [
            str(valor) for valor in _ordenar_reais(conjunto)
        ]

        justificativa = (
            "A equação possui 1 solução real."
            if quantidade == 1
            else f"A equação possui {quantidade} soluções reais."
        )

    else:
        detalhes["tipo"] = "infinito"
        detalhes["quantidade"] = None
        justificativa = (
            "A equação possui infinitas soluções reais "
            "(identidade no domínio)."
        )

    return montar_resultado(
        STATUS_CORRETO,
        justificativa,
        restricoes=_formatar_condicoes(resolucao["condicoes_dominio"]),
        detalhes=detalhes
    )


@_interface_protegida
def verificar_solucao_equacao(equacao, valor):
    """
    Verifica se um valor numérico é solução de uma equação real
    de uma variável.

    detalhes["motivo"] indica por que o valor foi rejeitado:
        "fora_do_dominio": o valor viola o domínio da equação.
        "nao_satisfaz": o valor está no domínio, mas não
            satisfaz a equação.
    """

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        valor = str(valor)

    try:
        dados = interpretar_equacao(equacao)
        variaveis = obter_variaveis_equacao(equacao)
        valor_simbolico = interpretar_expressao(valor)

        if valor_simbolico.free_symbols:
            raise ValueError("O valor informado deve ser numérico.")

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    if len(variaveis) != 1:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Apenas equações de uma variável são suportadas."
        )

    variavel = next(iter(variaveis))
    ponto = {variavel: valor_simbolico}

    condicoes = obter_condicoes_dominio(dados)
    restricoes = _formatar_condicoes(condicoes)

    detalhes = {
        "variavel": str(variavel),
        "valor": str(valor_simbolico)
    }

    no_dominio = verificar_condicoes_dominio(condicoes, ponto)

    if no_dominio is False:
        detalhes["motivo"] = "fora_do_dominio"

        return montar_resultado(
            STATUS_INCORRETO,
            "O valor não pertence ao domínio da equação.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    if no_dominio is None:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível verificar se o valor pertence ao "
            "domínio da equação.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    residuo = sp.simplify(
        (dados["esquerda"] - dados["direita"]).subs(ponto)
    )

    if residuo == 0 or residuo.is_zero is True:
        return montar_resultado(
            STATUS_CORRETO,
            "O valor satisfaz a equação.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    if residuo.is_zero is False:
        detalhes["motivo"] = "nao_satisfaz"

        return montar_resultado(
            STATUS_INCORRETO,
            "O valor pertence ao domínio, mas não satisfaz a equação.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    return montar_resultado(
        STATUS_INDETERMINADO,
        "Não foi possível determinar se o valor satisfaz a equação.",
        restricoes=restricoes,
        detalhes=detalhes
    )
