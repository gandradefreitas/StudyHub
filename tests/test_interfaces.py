import json

import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


@pytest.mark.parametrize("name,e1,e2,expected", [
    pytest.param("interface expressões: equivalentes", "(x + 1)^2", "x² + 2x + 1", "correct", id="interface expressões: equivalentes"),
    pytest.param("interface expressões: condicional x/x vs 1", "x/x", "1", "conditional", id="interface expressões: condicional x/x vs 1"),
    pytest.param("interface expressões: incorreto", "x² + 1", "(x + 1)²", "incorrect", id="interface expressões: incorreto"),
    pytest.param("interface expressões: domínios diferentes e funções diferentes", "1/x", "2/x", "incorrect", id="interface expressões: domínios diferentes e funções diferentes"),
    pytest.param("interface expressões: entrada inválida", "2 +", "2", "invalid", id="interface expressões: entrada inválida"),
])
def test_interface_expressoes_status(name, e1, e2, expected):
    actual = vm.avaliar_equivalencia_expressoes(e1, e2)["status"]
    assert_legacy_equal(name, actual, expected)


@pytest.mark.parametrize("name,e1,e2,campo,expected", [
    pytest.param("interface expressões: condições do caso condicional", "x/x", "1", "condicoes", ["x != 0"], id="interface expressões: condições do caso condicional"),
    pytest.param("interface expressões: restrições", "1/x", "2/x", "restricoes", ["x != 0"], id="interface expressões: restrições"),
    pytest.param("interface expressões: resultado booleano em correct", "x + x", "2x", "resultado", True, id="interface expressões: resultado booleano em correct"),
    pytest.param("interface expressões: resultado nulo em conditional", "x/x", "1", "resultado", None, id="interface expressões: resultado nulo em conditional"),
])
def test_interface_expressoes_campos(name, e1, e2, campo, expected):
    actual = vm.avaliar_equivalencia_expressoes(e1, e2)[campo]
    assert_legacy_equal(name, actual, expected)


def test_interface_expressoes_entrada_nao_textual():
    actual = vm.avaliar_equivalencia_expressoes(None, None)["status"]
    assert_legacy_equal("interface expressões: entrada não textual", actual, "invalid")


@pytest.mark.parametrize("name,e1,e2,expected", [
    pytest.param("interface equações: x²=4 vs fatorada", "x² = 4", "(x - 2)(x + 2) = 0", "correct", id="interface equações: x²=4 vs fatorada"),
    pytest.param("interface equações: perde solução", "x² = 4", "x = 2", "incorrect", id="interface equações: perde solução"),
    pytest.param("interface equações: com domínio", "(x² - 1)/(x - 1) = 0", "x + 1 = 0", "correct", id="interface equações: com domínio"),
    pytest.param("interface equações: duas variáveis equivalentes", "x + y = 1", "y = 1 - x", "correct", id="interface equações: duas variáveis equivalentes"),
    pytest.param("interface equações: duas variáveis diferentes", "x + y = 1", "x - y = 0", "incorrect", id="interface equações: duas variáveis diferentes"),
    pytest.param("interface equações: sem variáveis", "1 = 1", "2 = 2", "indeterminate", id="interface equações: sem variáveis"),
    pytest.param("interface equações: sem sinal de igualdade", "x + 1", "x = 1", "invalid", id="interface equações: sem sinal de igualdade"),
])
def test_interface_equacoes_status(name, e1, e2, expected):
    actual = vm.avaliar_equivalencia_equacoes(e1, e2)["status"]
    assert_legacy_equal(name, actual, expected)


def test_interface_equacoes_restricoes():
    actual = vm.avaliar_equivalencia_equacoes(
        "(x² - 1)/(x - 1) = 0", "x + 1 = 0"
    )["restricoes"]
    assert_legacy_equal("interface equações: restrições", actual, ["x - 1 != 0"])


@pytest.mark.parametrize("name,s1,s2,expected", [
    pytest.param("interface sistemas: mesma solução", ["x + y = 3", "x - y = 1"], ["2x = 4", "y = 1"], "correct", id="interface sistemas: mesma solução"),
    pytest.param("interface sistemas: solução diferente", ["x + y = 3", "x - y = 1"], ["x + y = 3", "x + y = 2"], "incorrect", id="interface sistemas: solução diferente"),
    pytest.param("interface sistemas: ambos impossíveis", ["x + y = 1", "x + y = 2"], ["x = 1", "x = 2"], "correct", id="interface sistemas: ambos impossíveis"),
    pytest.param("interface sistemas: não linear", ["x² + y = 1"], ["y = 1 - x²"], "indeterminate", id="interface sistemas: não linear"),
    pytest.param("interface sistemas: com restrição de domínio", ["1/x = y"], ["1/x = y"], "indeterminate", id="interface sistemas: com restrição de domínio"),
    pytest.param("interface sistemas: equação sem igualdade", ["x + y"], ["x = 1"], "invalid", id="interface sistemas: equação sem igualdade"),
    pytest.param("interface sistemas: não é lista", "x = 1", ["x = 1"], "invalid", id="interface sistemas: não é lista"),
])
def test_interface_sistemas_status(name, s1, s2, expected):
    actual = vm.avaliar_equivalencia_sistemas(s1, s2)["status"]
    assert_legacy_equal(name, actual, expected)


def test_interface_sistemas_parametricos_equacao_multiplicada():
    actual = vm.avaliar_equivalencia_sistemas(
        ["a*x + y = 1", "x + a*y = 1"],
        ["2*a*x + 2*y = 2", "x + a*y = 1"],
        incognitas=["x", "y"],
    )["status"] in ("correct", "conditional")
    # Preserve the original broad condition exactly.
    assert_legacy_equal("interface sistemas paramétricos: equação multiplicada", actual, True)


def test_interface_sistemas_parametricos_termo_alterado():
    actual = vm.avaliar_equivalencia_sistemas(
        ["a*x + y = 1", "x + a*y = 1"],
        ["a*x + y = 1", "x + a*y = 2"],
        incognitas=["x", "y"],
    )["status"]
    assert_legacy_equal("interface sistemas paramétricos: termo alterado", actual, "conditional")


def test_interface_sistemas_parametricos_parametros_reportados():
    actual = vm.avaliar_equivalencia_sistemas(
        ["a*x + y = 1", "x + a*y = 1"],
        ["a*x + y = 1", "x + a*y = 2"],
        incognitas=["x", "y"],
    )["detalhes"]["parametros"]
    assert_legacy_equal("interface sistemas paramétricos: parâmetros reportados", actual, ["a"])


@pytest.mark.parametrize("name,expressao,campo,expected", [
    pytest.param("interface domínio: denominador", "1/(x - 3)", "restricoes", ["x - 3 != 0"], id="interface domínio: denominador"),
    pytest.param("interface domínio: radical", "sqrt(x - 2)", "restricoes", ["x - 2 >= 0"], id="interface domínio: radical"),
    pytest.param("interface domínio: conjunto", "sqrt(x - 2)", "detalhes", "Interval(2, oo)", id="interface domínio: conjunto"),
])
def test_interface_dominio(name, expressao, campo, expected):
    resultado = vm.analisar_dominio_expressao(expressao)
    actual = resultado[campo]["dominio"] if campo == "detalhes" else resultado[campo]
    assert_legacy_equal(name, actual, expected)


def test_interface_dominio_entrada_invalida():
    actual = vm.analisar_dominio_expressao("sqrt(-4)")["status"]
    assert_legacy_equal("interface domínio: entrada inválida", actual, "invalid")


@pytest.mark.parametrize("name,call", [
    pytest.param("interface serializável em JSON: expressões", lambda: vm.avaliar_equivalencia_expressoes("x/x", "1"), id="interface serializável em JSON: expressões"),
    pytest.param("interface serializável em JSON: equações", lambda: vm.avaliar_equivalencia_equacoes("(x² - 1)/(x - 1) = 0", "x + 1 = 0"), id="interface serializável em JSON: equações"),
    pytest.param("interface serializável em JSON: sistemas", lambda: vm.avaliar_equivalencia_sistemas(["a*x + y = 1", "x + a*y = 1"], ["a*x + y = 1", "x + a*y = 2"], incognitas=["x", "y"]), id="interface serializável em JSON: sistemas"),
    pytest.param("interface serializável em JSON: domínio", lambda: vm.analisar_dominio_expressao("sqrt(x - 2)"), id="interface serializável em JSON: domínio"),
])
def test_interface_serializavel_json(name, call):
    json.dumps(call())
    assert_legacy_equal(name, True, True)
