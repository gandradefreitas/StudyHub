"""Verificação de transformações algébricas."""

import itertools

import sympy as sp

from .avaliacao import (
    avaliar_equivalencia_equacoes,
    avaliar_equivalencia_expressoes,
)
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
    obter_variaveis_equacao,
    verificar_condicoes_dominio,
)
from .equacoes import interpretar_equacao
from .interpretador import interpretar_expressao
from .resolucao import (
    _ordenar_reais,
    obter_conjunto_solucao_equacao,
)
from .tempo import _interface_protegida


# ----------------------------------------------------------------
# Verificação de transformações algébricas
# ----------------------------------------------------------------
def _eh_equacao(texto):
    return isinstance(texto, str) and "=" in texto


def _listar_conjunto(conjunto):
    """Lista textual de um conjunto de reais."""

    if isinstance(conjunto, sp.FiniteSet):
        return [str(valor) for valor in _ordenar_reais(conjunto)]

    if conjunto == sp.S.EmptySet:
        return []

    return [str(conjunto)]


def _procurar_contraexemplo(esperado, apresentado, condicoes_dominio=()):
    """
    Procura um ponto, dentro do domínio, onde as duas expressões
    têm valores diferentes.

    Retorna (ponto, valor_1, valor_2) ou None.
    Serve apenas para exibir um contraexemplo; nunca prova
    equivalência.
    """

    diferenca = sp.simplify(esperado - apresentado)

    simbolos = (
        set(diferenca.free_symbols)
        | set(esperado.free_symbols)
        | set(apresentado.free_symbols)
    )

    for condicao in condicoes_dominio:
        simbolos |= condicao.free_symbols

    simbolos = sorted(simbolos, key=str)

    if not simbolos or len(simbolos) > 3:
        return None

    candidatos = [1, -1, 2, 0, sp.Rational(1, 2), -2]

    for valores in itertools.product(candidatos, repeat=len(simbolos)):
        ponto = dict(zip(simbolos, valores))

        if (
            condicoes_dominio
            and verificar_condicoes_dominio(
                condicoes_dominio,
                ponto
            ) is not True
        ):
            continue

        valor_1 = esperado.subs(ponto)
        valor_2 = apresentado.subs(ponto)

        if valor_1.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
            continue

        if valor_2.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
            continue

        if sp.simplify(valor_1 - valor_2).is_zero is False:
            return ponto, valor_1, valor_2

    return None


def _contraexemplo_expressoes(anterior, novo):
    """Contraexemplo em formato textual, ou None."""

    try:
        expr_1 = interpretar_expressao(anterior)
        expr_2 = interpretar_expressao(novo)

        condicoes_1 = obter_condicoes_dominio_expressao(anterior)
        condicoes_2 = obter_condicoes_dominio_expressao(novo)

    except _ERROS_DE_ENTRADA:
        return None

    if condicoes_1 is None or condicoes_2 is None:
        return None

    achado = _procurar_contraexemplo(
        expr_1,
        expr_2,
        condicoes_1 + condicoes_2
    )

    if achado is None:
        return None

    ponto, valor_1, valor_2 = achado

    return {
        "ponto": {str(simbolo): str(valor) for simbolo, valor in ponto.items()},
        "valor_anterior": str(valor_1),
        "valor_novo": str(valor_2)
    }


def _verificar_transformacao_expressao(anterior, novo):
    resultado = avaliar_equivalencia_expressoes(anterior, novo)

    status = resultado["status"]
    detalhes = resultado["detalhes"]

    if status == STATUS_CORRETO:
        detalhes["tipo"] = "equivalente"
        resultado["justificativa"] = (
            "A transformação preserva a expressão, inclusive o domínio."
        )

    elif status == STATUS_CONDICIONAL:
        detalhes["tipo"] = "valida_sob_condicoes"
        resultado["justificativa"] = (
            "A transformação só é válida onde as duas expressões "
            "estão definidas."
        )

    elif status == STATUS_INCORRETO:
        detalhes["tipo"] = "nao_equivalente"
        resultado["justificativa"] = (
            "A transformação não preserva a expressão."
        )

        contraexemplo = _contraexemplo_expressoes(anterior, novo)

        if contraexemplo is not None:
            detalhes["contraexemplo"] = contraexemplo

    return resultado


def _verificar_transformacao_equacao(anterior, novo):
    try:
        interpretar_equacao(anterior)
        interpretar_equacao(novo)

        variaveis_anterior = obter_variaveis_equacao(anterior)
        variaveis_novo = obter_variaveis_equacao(novo)

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    # Uma variável: compara os conjuntos solução.
    if len(variaveis_anterior) == 1 and variaveis_anterior == variaveis_novo:

        resolucao_anterior = obter_conjunto_solucao_equacao(anterior)
        resolucao_novo = obter_conjunto_solucao_equacao(novo)

        if resolucao_anterior is None or resolucao_novo is None:
            return montar_resultado(
                STATUS_INDETERMINADO,
                "Não foi possível resolver uma das equações."
            )

        # Restrições de domínio das duas equações.
        restricoes = _formatar_condicoes(
            resolucao_anterior["condicoes_dominio"]
            + resolucao_novo["condicoes_dominio"]
        )

        conjunto_anterior = resolucao_anterior["conjunto"]
        conjunto_novo = resolucao_novo["conjunto"]

        perdidas = sp.Complement(conjunto_anterior, conjunto_novo)
        extras = sp.Complement(conjunto_novo, conjunto_anterior)

        sem_perdas = perdidas.is_empty
        sem_extras = extras.is_empty

        detalhes = {
            "variavel": str(next(iter(variaveis_anterior))),
            "solucoes_anteriores": _listar_conjunto(conjunto_anterior),
            "solucoes_novas": _listar_conjunto(conjunto_novo),
            "solucoes_perdidas": (
                _listar_conjunto(perdidas) if sem_perdas is False else []
            ),
            "solucoes_extras": (
                _listar_conjunto(extras) if sem_extras is False else []
            )
        }

        if sem_perdas is None or sem_extras is None:
            return montar_resultado(
                STATUS_INDETERMINADO,
                "Não foi possível comparar os conjuntos solução.",
                restricoes=restricoes,
                detalhes=detalhes
            )

        if sem_perdas and sem_extras:
            detalhes["tipo"] = "equivalente"

            return montar_resultado(
                STATUS_CORRETO,
                "As equações possuem o mesmo conjunto solução.",
                restricoes=restricoes,
                detalhes=detalhes
            )

        if sem_perdas and not sem_extras:
            detalhes["tipo"] = "solucoes_extras"

            return montar_resultado(
                STATUS_CONDICIONAL,
                "Todas as soluções da equação anterior foram "
                "preservadas, mas a nova equação possui soluções que "
                "não satisfazem a anterior.",
                restricoes=restricoes,
                condicoes=[
                    "verificar as soluções encontradas na equação original"
                ],
                detalhes=detalhes
            )

        if not sem_perdas and sem_extras:
            detalhes["tipo"] = "perda_de_solucoes"

            return montar_resultado(
                STATUS_INCORRETO,
                "A transformação eliminou soluções da equação anterior.",
                restricoes=restricoes,
                detalhes=detalhes
            )

        detalhes["tipo"] = "perda_e_solucoes_extras"

        return montar_resultado(
            STATUS_INCORRETO,
            "A transformação eliminou soluções da equação anterior e "
            "introduziu soluções que não a satisfazem.",
            restricoes=restricoes,
            detalhes=detalhes
        )

    # Outros casos: apenas equivalente ou não.
    resultado = avaliar_equivalencia_equacoes(anterior, novo)

    if resultado["status"] == STATUS_CORRETO:
        resultado["detalhes"]["tipo"] = "equivalente"

    elif resultado["status"] == STATUS_INCORRETO:
        resultado["detalhes"]["tipo"] = "nao_equivalente"

    return resultado


@_interface_protegida
def verificar_transformacao(anterior, novo):
    """
    Verifica se uma transformação feita pelo estudante preserva
    a equivalência matemática.

    anterior: expressão ou equação de partida.
    novo: expressão ou equação obtida pela transformação.
    O tipo (expressão ou equação) é detectado pelo sinal '='.
    A direção importa: 'anterior' é o ponto de partida.

    detalhes["tipo"]:
        equivalente, valida_sob_condicoes, nao_equivalente,
        solucoes_extras, perda_de_solucoes,
        perda_e_solucoes_extras.
    """

    if _eh_equacao(anterior) != _eh_equacao(novo):
        return _resultado_invalido(
            ValueError(
                "Uma expressão não pode ser comparada com uma equação."
            )
        )

    if _eh_equacao(anterior):
        return _verificar_transformacao_equacao(anterior, novo)

    return _verificar_transformacao_expressao(anterior, novo)
