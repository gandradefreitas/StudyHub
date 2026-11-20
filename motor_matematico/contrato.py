"""Formato único de retorno das funções públicas."""

import sympy as sp


# ----------------------------------------------------------------
# Interface pública para a IA corretora
# ----------------------------------------------------------------
STATUS_CORRETO = "correct"


STATUS_INCORRETO = "incorrect"


STATUS_CONDICIONAL = "conditional"


STATUS_INDETERMINADO = "indeterminate"


STATUS_INVALIDO = "invalid"


_ERROS_DE_ENTRADA = (
    ValueError,
    TypeError,
    SyntaxError,
    ZeroDivisionError,
    OverflowError,
    sp.SympifyError
)


def montar_resultado(
        status,
        justificativa,
        restricoes=None,
        condicoes=None,
        detalhes=None
):
    """Formato único de retorno das funções públicas."""

    if status == STATUS_CORRETO:
        resultado = True
    elif status == STATUS_INCORRETO:
        resultado = False
    else:
        resultado = None

    return {
        "status": status,
        "resultado": resultado,
        "justificativa": justificativa,
        "restricoes": list(restricoes or []),
        "condicoes": list(condicoes or []),
        "detalhes": dict(detalhes or {})
    }


def _resultado_invalido(erro):
    return montar_resultado(
        STATUS_INVALIDO,
        f"Entrada inválida: {erro}",
        detalhes={"erro": str(erro)}
    )


def _formatar_condicao(condicao):
    if isinstance(condicao, sp.core.relational.Unequality):
        return f"{condicao.lhs} != {condicao.rhs}"

    if isinstance(condicao, sp.core.relational.GreaterThan):
        return f"{condicao.lhs} >= {condicao.rhs}"

    return str(condicao)


def _formatar_condicoes(condicoes):
    """Converte condições em texto, sem repetições."""

    return list(dict.fromkeys(
        _formatar_condicao(condicao) for condicao in condicoes
    ))
