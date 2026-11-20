"""Interface pública: equivalência de expressões, equações, sistemas e domínio."""

import sympy as sp

from .contrato import (
    STATUS_CONDICIONAL,
    STATUS_CORRETO,
    STATUS_INCORRETO,
    STATUS_INDETERMINADO,
    _ERROS_DE_ENTRADA,
    _formatar_condicoes,
    _resultado_invalido,
    montar_resultado,
)
from .dominio import (
    obter_condicoes_dominio_expressao,
    obter_dominio,
    obter_variaveis_equacao,
)
from .equacoes import (
    interpretar_equacao,
    obter_condicoes_dominio,
)
from .equivalencia import (
    analisar_equivalencia_expressoes,
    verificar_equivalencia_equacoes,
    verificar_equivalencia_multivariavel,
)
from .interpretador import interpretar_expressao
from .sistemas import (
    analisar_equivalencia_sistemas_parametricos,
    construir_matriz_sistema,
    identificar_parametros_sistema,
    verificar_equivalencia_sistemas_numericos,
)
from .tempo import _interface_protegida


@_interface_protegida
def avaliar_equivalencia_expressoes(expressao_1, expressao_2):
    """
    Compara duas expressões considerando os domínios.

    correct: mesma função (mesmo domínio).
    conditional: coincidem onde ambas estão definidas, mas os
        domínios são diferentes (ex.: x/x e 1).
    incorrect: comprovadamente diferentes.
    """

    try:
        interpretar_expressao(expressao_1)
        interpretar_expressao(expressao_2)
    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    analise = analisar_equivalencia_expressoes(expressao_1, expressao_2)

    restricoes_1 = _formatar_condicoes(
        obter_condicoes_dominio_expressao(expressao_1) or []
    )
    restricoes_2 = _formatar_condicoes(
        obter_condicoes_dominio_expressao(expressao_2) or []
    )
    restricoes = list(dict.fromkeys(restricoes_1 + restricoes_2))

    detalhes = {
        "igualdade_algebrica": analise["igualdade_algebrica"],
        "dominios_iguais": analise["dominios_iguais"],
        "restricoes_expressao_1": restricoes_1,
        "restricoes_expressao_2": restricoes_2
    }

    resultado = analise["resultado"]

    if resultado == "equivalentes":
        return montar_resultado(
            STATUS_CORRETO,
            "As expressões são matematicamente equivalentes e "
            "possuem o mesmo domínio.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    if resultado == "condicional":
        return montar_resultado(
            STATUS_CONDICIONAL,
            "As expressões coincidem onde ambas estão definidas, "
            "mas possuem domínios diferentes.",
            restricoes=restricoes,
            condicoes=restricoes,
            detalhes=detalhes
        )

    if resultado == "diferentes":
        return montar_resultado(
            STATUS_INCORRETO,
            "As expressões não são equivalentes.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    return montar_resultado(
        STATUS_INDETERMINADO,
        "Não foi possível determinar a equivalência com segurança.",
        restricoes=restricoes,
        detalhes=detalhes
    )


@_interface_protegida
def avaliar_equivalencia_equacoes(equacao_1, equacao_2):
    """
    Compara os conjuntos solução de duas equações, considerando
    as restrições de domínio. Aceita uma ou várias variáveis.
    """

    try:
        dados_1 = interpretar_equacao(equacao_1)
        dados_2 = interpretar_equacao(equacao_2)

        variaveis = (
            obter_variaveis_equacao(equacao_1)
            | obter_variaveis_equacao(equacao_2)
        )

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    condicoes_1 = obter_condicoes_dominio(dados_1)
    condicoes_2 = obter_condicoes_dominio(dados_2)

    restricoes = _formatar_condicoes(condicoes_1 + condicoes_2)

    detalhes = {
        "variaveis": sorted(str(v) for v in variaveis)
    }

    if len(variaveis) == 1:
        equivalentes = verificar_equivalencia_equacoes(
            equacao_1,
            equacao_2
        )

    elif len(variaveis) > 1:
        equivalentes = verificar_equivalencia_multivariavel(
            dados_1["diferenca"],
            dados_2["diferenca"],
            variaveis,
            condicoes_1,
            condicoes_2
        )

    else:
        equivalentes = None

    if equivalentes is True:
        return montar_resultado(
            STATUS_CORRETO,
            "As equações possuem o mesmo conjunto solução.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    if equivalentes is False:
        return montar_resultado(
            STATUS_INCORRETO,
            "As equações não possuem o mesmo conjunto solução.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    return montar_resultado(
        STATUS_INDETERMINADO,
        "Não foi possível determinar a equivalência com segurança.",
        restricoes=restricoes,
        detalhes=detalhes
    )


@_interface_protegida
def avaliar_equivalencia_sistemas(sistema_1, sistema_2, incognitas=None):
    """
    Compara dois sistemas lineares.

    sistema_1, sistema_2: listas de strings 'expressao = expressao'.
    incognitas: nomes das incógnitas, por exemplo ["x", "y"].
        Os demais símbolos são parâmetros. Com None, todos os
        símbolos são incógnitas (sistema sem parâmetros).
    """

    try:
        for sistema in (sistema_1, sistema_2):
            if not isinstance(sistema, (list, tuple)) or not sistema:
                raise ValueError(
                    "Cada sistema deve ser uma lista não vazia de equações."
                )

        dados = [
            interpretar_equacao(equacao)
            for equacao in list(sistema_1) + list(sistema_2)
        ]

        simbolos = set()

        for equacao in list(sistema_1) + list(sistema_2):
            simbolos |= obter_variaveis_equacao(equacao)

        if incognitas is None:
            variaveis = simbolos
        else:
            variaveis = {sp.Symbol(nome, real=True) for nome in incognitas}

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    if any(obter_condicoes_dominio(d) for d in dados):
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Sistemas com restrições de domínio ainda não são suportados."
        )

    if len(sistema_1) > 8 or len(sistema_2) > 8 or len(variaveis) > 5:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Sistema grande demais para uma análise segura."
        )

    diferencas_1 = [d["diferenca"] for d in dados[:len(sistema_1)]]
    diferencas_2 = [d["diferenca"] for d in dados[len(sistema_1):]]

    matriz_1 = construir_matriz_sistema(diferencas_1, variaveis)
    matriz_2 = construir_matriz_sistema(diferencas_2, variaveis)

    if matriz_1 is None or matriz_2 is None:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Apenas sistemas lineares são suportados."
        )

    parametros = (
        identificar_parametros_sistema(matriz_1)
        | identificar_parametros_sistema(matriz_2)
    )

    detalhes = {
        "incognitas": sorted(str(v) for v in variaveis),
        "parametros": sorted(str(p) for p in parametros)
    }

    # Sistemas sem parâmetros.
    if not parametros:
        equivalentes = verificar_equivalencia_sistemas_numericos(
            matriz_1,
            matriz_2
        )

        if equivalentes is True:
            return montar_resultado(
                STATUS_CORRETO,
                "Os sistemas possuem o mesmo conjunto solução.",
                detalhes=detalhes
            )

        if equivalentes is False:
            return montar_resultado(
                STATUS_INCORRETO,
                "Os sistemas não possuem o mesmo conjunto solução.",
                detalhes=detalhes
            )

        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível determinar a equivalência com segurança.",
            detalhes=detalhes
        )

    # Sistemas paramétricos.
    analise = analisar_equivalencia_sistemas_parametricos(
        matriz_1,
        matriz_2
    )

    if analise is None:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível analisar o sistema paramétrico.",
            detalhes=detalhes
        )

    equivalentes = analise["equivalentes"]

    if equivalentes is sp.true:
        return montar_resultado(
            STATUS_CORRETO,
            "Os sistemas são equivalentes para quaisquer valores "
            "dos parâmetros.",
            detalhes=detalhes
        )

    if equivalentes is sp.false:
        return montar_resultado(
            STATUS_INCORRETO,
            "Os sistemas não são equivalentes para nenhum valor "
            "dos parâmetros.",
            detalhes=detalhes
        )

    detalhes["nao_equivalentes"] = str(analise["nao_equivalentes"])

    return montar_resultado(
        STATUS_CONDICIONAL,
        "Os sistemas são equivalentes apenas para alguns valores "
        "dos parâmetros.",
        condicoes=[str(equivalentes)],
        detalhes=detalhes
    )


@_interface_protegida
def analisar_dominio_expressao(expressao):
    """Determina as condições de existência de uma expressão."""

    try:
        interpretar_expressao(expressao)
    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    condicoes = obter_condicoes_dominio_expressao(expressao)

    if condicoes is None:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Não foi possível determinar o domínio da expressão."
        )

    detalhes = {}

    try:
        dominio = obter_dominio(expressao)

        if dominio is not None:
            detalhes["dominio"] = str(dominio)

    except (ValueError, TypeError, NotImplementedError):
        pass

    return montar_resultado(
        STATUS_CORRETO,
        "Condições de existência determinadas (nos números reais).",
        restricoes=_formatar_condicoes(condicoes),
        detalhes=detalhes
    )
