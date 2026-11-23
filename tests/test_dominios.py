import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


pytestmark = pytest.mark.matematica


x = sp.Symbol("x", real=True)


@pytest.mark.parametrize("name,expressao,expected", [
    pytest.param("restrição 1/(x-3)", "1/(x - 3)", [3], id="restrição 1/(x-3)"),
    pytest.param("restrição 1/(x²-4)", "1/(x**2 - 4)", [-2, 2], id="restrição 1/(x²-4)"),
    pytest.param("restrição de dois denominadores", "1/x + 1/(x - 1)", [0, 1], id="restrição de dois denominadores"),
    pytest.param("sem denominadores", "x + 1", [], id="sem denominadores"),
    pytest.param("denominador sem raiz real", "1/(x**2 + 1)", [], id="denominador sem raiz real"),
    pytest.param("denominador multivariável", "1/(x + y)", None, id="denominador multivariável"),
])
def test_identificar_restricoes(name, expressao, expected):
    assert_legacy_equal(name, vm.identificar_restricoes(expressao), expected)


@pytest.mark.parametrize("name,expressao,expected", [
    pytest.param("condição de denominador (qtd)", "1/(x - 2)", 1, id="condição de denominador (qtd)"),
    pytest.param("condição de denominador (lhs)", "1/(x - 2)", x - 2, id="condição de denominador (lhs)"),
    pytest.param("denominador constante", "1/2", [], id="denominador constante"),
])
def test_condicoes_denominadores(name, expressao, expected):
    conditions = vm.obter_condicoes_denominadores(expressao)
    actual = len(conditions) if name.endswith("(qtd)") else (conditions[0].lhs if conditions else conditions)
    assert_legacy_equal(name, actual, expected)


def test_condicao_raiz_lhs():
    assert_legacy_equal("condição de raiz (lhs)", vm.obter_condicoes_raizes("sqrt(x - 2)")[0].lhs, x - 2)


@pytest.mark.parametrize("name,expressao,expected", [
    pytest.param("domínio sqrt(x-2)", "sqrt(x - 2)", sp.Interval(2, sp.oo), id="domínio sqrt(x-2)"),
    pytest.param("domínio 1/(x-3)", "1/(x - 3)", sp.Union(sp.Interval.open(-sp.oo, 3), sp.Interval.open(3, sp.oo)), id="domínio 1/(x-3)"),
    pytest.param("domínio sqrt((x-1)/(x+2))", "sqrt((x - 1)/(x + 2))", sp.Union(sp.Interval.open(-sp.oo, -2), sp.Interval(1, sp.oo)), id="domínio sqrt((x-1)/(x+2))"),
])
def test_obter_dominio(name, expressao, expected):
    assert_legacy_equal(name, vm.obter_dominio(expressao), expected)


@pytest.mark.parametrize("name,expressao,expected", [
    pytest.param("restrição com notação do estudante", "1/(2x - 6)", [3], id="restrição com notação do estudante"),
    pytest.param("raiz com notação do estudante", "sqrt(2x - 4)", sp.Interval(2, sp.oo), id="raiz com notação do estudante"),
])
def test_dominio_notacao_estudante(name, expressao, expected):
    actual = vm.identificar_restricoes(expressao) if name.startswith("restrição") else vm.obter_dominio(expressao)
    assert_legacy_equal(name, actual, expected)


@pytest.mark.parametrize("name,expressao,expected", [
    pytest.param("restrição: 1/x**2", "1/x**2", [0], id="restrição: 1/x**2"),
    pytest.param("restrição: x**(-2)", "x**(-2)", [0], id="restrição: x**(-2)"),
    pytest.param("restrição: x**(-1)", "x**(-1)", [0], id="restrição: x**(-1)"),
    pytest.param("restrição: x⁻¹", "x⁻¹", [0], id="restrição: x⁻¹"),
    pytest.param("restrição: 2**(-1) é constante", "2**(-1)", [], id="restrição: 2**(-1) é constante"),
])
def test_restricoes_potencias(name, expressao, expected):
    assert_legacy_equal(name, vm.identificar_restricoes(expressao), expected)


def test_condicao_x_expoente_menos_um():
    actual = vm.obter_condicoes_denominadores("x**(-1)")[0].lhs
    assert_legacy_equal("condição de x**(-1)", actual, x)


@pytest.mark.parametrize("name,expressao1,expressao2,expected", [
    pytest.param("domínios: 1/x vs x**(-1)", "1/x", "x**(-1)", True, id="domínios: 1/x vs x**(-1)"),
    pytest.param("domínios: x/x vs 1", "x/x", "1", False, id="domínios: x/x vs 1"),
    pytest.param("domínios: sqrt(x²) vs |x|", "sqrt(x**2)", "abs(x)", True, id="domínios: sqrt(x²) vs |x|"),
    pytest.param("domínios: sqrt(x) vs x", "sqrt(x)", "x", False, id="domínios: sqrt(x) vs x"),
    pytest.param("domínios: multivar: x*y/x vs y", "x*y/x", "y", False, id="domínios: multivar: x*y/x vs y"),
    pytest.param("domínios: multivar: 1/(x*y) vs 1/x/y", "1/(x*y)", "1/x/y", True, id="domínios: multivar: 1/(x*y) vs 1/x/y"),
    pytest.param("domínios: multivar: (x+y)/(x+y) vs 1", "(x + y)/(x + y)", "1", False, id="domínios: multivar: (x+y)/(x+y) vs 1"),
    pytest.param("domínios: multivar: 1/(x*y) vs 1/(x+y)", "1/(x*y)", "1/(x + y)", False, id="domínios: multivar: 1/(x*y) vs 1/(x+y)"),
])
def test_comparar_dominios(name, expressao1, expressao2, expected):
    assert_legacy_equal(name, vm.comparar_dominios_expressoes(expressao1, expressao2), expected)
