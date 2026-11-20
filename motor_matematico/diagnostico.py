"""Diagnóstico de erros em transformações."""

import sympy as sp

from .contrato import (
    STATUS_CONDICIONAL,
    STATUS_INCORRETO,
    _formatar_condicoes,
)
from .dominio import verificar_condicoes_dominio
from .equacoes import interpretar_equacao
from .interpretador import interpretar_expressao
from .resolucao import obter_conjunto_solucao_equacao
from .tempo import _interface_protegida
from .transformacoes import (
    _eh_equacao,
    verificar_transformacao,
)


# ----------------------------------------------------------------
# Diagnóstico de erros
# ----------------------------------------------------------------
def _termo_em_texto(monomio, coeficiente, simbolos):
    termo = coeficiente

    for simbolo, expoente in zip(simbolos, monomio):
        termo = termo * simbolo**expoente

    return str(termo)


def _diagnostico(categoria, descricao, evidencias=None, especifico=True):
    return {
        "categoria": categoria,
        "descricao": descricao,
        "evidencias": dict(evidencias or {}),
        "especifico": especifico
    }


def _diagnostico_generico(tipo, evidencias=None):
    descricoes = {
        "perda_de_solucoes": (
            "perda_de_solucoes",
            "A transformação eliminou soluções da equação anterior."
        ),
        "solucoes_extras": (
            "solucoes_extras",
            "A nova equação possui soluções que não satisfazem a anterior."
        ),
        "perda_e_solucoes_extras": (
            "perda_e_solucoes_extras",
            "A transformação eliminou soluções da equação anterior e "
            "introduziu soluções que não a satisfazem."
        )
    }

    categoria, descricao = descricoes.get(
        tipo,
        (
            "transformacao_invalida",
            "A transformação não preserva a equivalência; a causa "
            "específica não pôde ser determinada."
        )
    )

    return _diagnostico(
        categoria,
        descricao,
        evidencias,
        especifico=False
    )


def _diagnosticar_expressoes(anterior, novo, resultado):
    """Diagnóstico para transformações entre expressões."""

    if resultado["detalhes"].get("tipo") == "valida_sob_condicoes":
        return _diagnostico(
            "restricao_de_dominio",
            "A transformação só é válida quando as condições de "
            "domínio são satisfeitas.",
            {"condicoes": list(resultado["condicoes"])}
        )

    expr_1 = interpretar_expressao(anterior)
    expr_2 = interpretar_expressao(novo)

    simbolos = sorted(expr_1.free_symbols | expr_2.free_symbols, key=str)

    # Erro aritmético: expressões numéricas com valores diferentes.
    if not simbolos:
        return _diagnostico(
            "erro_aritmetico",
            f"O valor da expressão anterior é {expr_1}, mas o "
            f"resultado apresentado é {expr_2}.",
            {
                "valor_anterior": str(expr_1),
                "valor_apresentado": str(expr_2)
            }
        )

    # Propriedade: a anterior é igual ao módulo da nova.
    if expr_1 != expr_2 and sp.simplify(expr_1 - sp.Abs(expr_2)) == 0:
        return _diagnostico(
            "erro_de_propriedade",
            f"A expressão anterior é igual ao valor absoluto de "
            f"{expr_2}, e não a {expr_2}.",
            {
                "expressao_anterior": str(expr_1),
                "valor_absoluto_do_resultado": str(sp.Abs(expr_2))
            }
        )

    # Comparação termo a termo (apenas para polinômios).
    try:
        termos_1 = {
            monomio: coeficiente
            for monomio, coeficiente
            in sp.Poly(sp.expand(expr_1), *simbolos).terms()
            if coeficiente != 0
        }

        termos_2 = {
            monomio: coeficiente
            for monomio, coeficiente
            in sp.Poly(sp.expand(expr_2), *simbolos).terms()
            if coeficiente != 0
        }

    except sp.PolynomialError:
        return None

    def texto(monomio, coeficiente):
        return _termo_em_texto(monomio, coeficiente, simbolos)

    omitidos = {m: c for m, c in termos_1.items() if m not in termos_2}
    extras = {m: c for m, c in termos_2.items() if m not in termos_1}
    alterados = {
        m: (termos_1[m], termos_2[m])
        for m in termos_1
        if m in termos_2 and termos_1[m] != termos_2[m]
    }

    evidencias = {}

    if omitidos:
        evidencias["termos_omitidos"] = [
            texto(m, c) for m, c in omitidos.items()
        ]

    if extras:
        evidencias["termos_extras"] = [
            texto(m, c) for m, c in extras.items()
        ]

    if alterados:
        evidencias["termos_alterados"] = [
            f"{texto(m, c1)} -> {texto(m, c2)}"
            for m, (c1, c2) in alterados.items()
        ]

    expandida_1 = expr_1 == sp.expand(expr_1)
    expandida_2 = expr_2 == sp.expand(expr_2)

    if not expandida_1 and expandida_2:
        return _diagnostico(
            "erro_de_expansao",
            "O resultado não corresponde à expansão da expressão "
            "anterior.",
            evidencias
        )

    if expandida_1 and not expandida_2:
        evidencias["expansao_do_resultado"] = str(sp.expand(expr_2))

        return _diagnostico(
            "erro_de_fatoracao",
            "O resultado, ao ser expandido, não coincide com a "
            "expressão anterior.",
            evidencias
        )

    if alterados and not omitidos and not extras:

        if all(c2 == -c1 for c1, c2 in alterados.values()):
            evidencias["termos_com_sinal_invertido"] = [
                texto(m, c1) for m, (c1, c2) in alterados.items()
            ]

            return _diagnostico(
                "erro_de_sinal",
                "Após expandir as duas expressões, elas diferem "
                "apenas pelo sinal de um ou mais termos.",
                evidencias
            )

        if len(alterados) == 1:
            return _diagnostico(
                "erro_de_coeficiente",
                "Após expandir as duas expressões, elas diferem "
                "apenas no coeficiente de um termo.",
                evidencias
            )

        return None

    if omitidos and not extras and not alterados:
        return _diagnostico(
            "termos_omitidos",
            "Após expandir, a nova expressão não possui alguns "
            "termos da anterior.",
            evidencias
        )

    if extras and not omitidos and not alterados:
        return _diagnostico(
            "termos_extras",
            "Após expandir, a nova expressão possui termos que a "
            "anterior não tem.",
            evidencias
        )

    return None


def _diagnosticar_equacoes(anterior, novo, resultado):
    """Diagnóstico para transformações entre equações (uma variável)."""

    detalhes = resultado["detalhes"]
    tipo = detalhes.get("tipo")

    if tipo not in (
        "perda_de_solucoes",
        "solucoes_extras",
        "perda_e_solucoes_extras"
    ):
        return None

    evidencias = {}

    if detalhes.get("solucoes_perdidas"):
        evidencias["solucoes_perdidas"] = detalhes["solucoes_perdidas"]

    if detalhes.get("solucoes_extras"):
        evidencias["solucoes_extras"] = detalhes["solucoes_extras"]

    if tipo == "perda_e_solucoes_extras":
        return None

    dados_anterior = interpretar_equacao(anterior)
    dados_novo = interpretar_equacao(novo)

    variavel = sp.Symbol(detalhes["variavel"], real=True)

    resolucao_anterior = obter_conjunto_solucao_equacao(anterior)
    resolucao_novo = obter_conjunto_solucao_equacao(novo)

    if resolucao_anterior is None or resolucao_novo is None:
        return None

    diferenca_anterior = dados_anterior["diferenca"]
    diferenca_novo = dados_novo["diferenca"]

    if tipo == "solucoes_extras":

        extras = sp.Complement(
            resolucao_novo["conjunto"],
            resolucao_anterior["conjunto"]
        )

        # Todas as soluções extras violam o domínio original.
        if isinstance(extras, sp.FiniteSet) and len(extras) > 0:
            condicoes = resolucao_anterior["condicoes_dominio"]

            if all(
                verificar_condicoes_dominio(
                    condicoes,
                    {variavel: valor}
                ) is False
                for valor in extras
            ):
                evidencias["restricoes_da_equacao_anterior"] = (
                    _formatar_condicoes(condicoes)
                )

                return _diagnostico(
                    "erro_de_dominio",
                    "As soluções extras não pertencem ao domínio da "
                    "equação anterior.",
                    evidencias
                )

        # Os dois lados da nova são os da anterior ao quadrado.
        if (
            sp.expand(
                dados_novo["esquerda"] - dados_anterior["esquerda"]**2
            ) == 0
            and sp.expand(
                dados_novo["direita"] - dados_anterior["direita"]**2
            ) == 0
        ):
            return _diagnostico(
                "elevacao_ao_quadrado",
                "A nova equação é a anterior com os dois lados "
                "elevados ao quadrado.",
                evidencias
            )

        # A nova é a anterior multiplicada por um fator.
        if diferenca_anterior != 0:
            fator = sp.cancel(diferenca_novo / diferenca_anterior)

            if fator.has(variavel) and fator.is_polynomial(variavel):
                evidencias["fator"] = str(fator)

                return _diagnostico(
                    "multiplicacao_por_fator",
                    f"A diferença entre os lados da nova equação é "
                    f"igual à da anterior multiplicada por ({fator}); "
                    f"as soluções de {fator} = 0 podem aparecer como "
                    f"soluções extras.",
                    evidencias
                )

        return None

    # tipo == "perda_de_solucoes"
    if diferenca_novo != 0:
        fator = sp.cancel(diferenca_anterior / diferenca_novo)

        if fator.has(variavel) and fator.is_polynomial(variavel):
            evidencias["fator"] = str(fator)

            return _diagnostico(
                "fator_cancelado",
                f"A diferença entre os lados da equação anterior é "
                f"igual à da nova multiplicada por ({fator}); as "
                f"soluções de {fator} = 0 não aparecem na nova equação.",
                evidencias
            )

    return None


def _diagnosticar(anterior, novo, resultado):
    """
    Diagnostica o erro de uma transformação, reaproveitando o
    resultado de verificar_transformacao.

    Retorna None se a transformação não exige diagnóstico
    (correta, inválida ou indeterminada).
    O diagnóstico nunca interrompe a análise: qualquer falha
    interna produz um diagnóstico genérico.
    """

    if resultado["status"] not in (STATUS_INCORRETO, STATUS_CONDICIONAL):
        return None

    tipo = resultado["detalhes"].get("tipo")

    try:
        if _eh_equacao(anterior):
            diagnostico = _diagnosticar_equacoes(anterior, novo, resultado)
        else:
            diagnostico = _diagnosticar_expressoes(anterior, novo, resultado)

    except Exception:
        diagnostico = None

    if diagnostico is not None:
        return diagnostico

    evidencias = {}

    for chave in ("solucoes_perdidas", "solucoes_extras"):
        if resultado["detalhes"].get(chave):
            evidencias[chave] = resultado["detalhes"][chave]

    return _diagnostico_generico(tipo, evidencias)


@_interface_protegida
def diagnosticar_transformacao(anterior, novo):
    """
    Verifica uma transformação e, se ela não for correta,
    acrescenta detalhes["diagnostico"]:
        categoria, descricao, evidencias e especifico.

    especifico=True: a categoria foi comprovada por uma relação
        matemática verificável (descrita em evidencias).
    especifico=False: descrição genérica; a causa não foi determinada.
    """

    resultado = verificar_transformacao(anterior, novo)

    resultado["detalhes"]["diagnostico"] = _diagnosticar(
        anterior,
        novo,
        resultado
    )

    return resultado
