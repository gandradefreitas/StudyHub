import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


@pytest.fixture
def symbols():
    return sp.symbols("x y", real=True)


@pytest.mark.parametrize("name,expressao1,expressao2,expected", [
    pytest.param("equivalência: quadrado da soma", "x**2 + 2*x + 1", "(x + 1)**2", True, id="equivalência: quadrado da soma"),
    pytest.param("equivalência: expansão", "(x + 2)*(x + 3)", "x**2 + 5*x + 6", True, id="equivalência: expansão"),
    pytest.param("equivalência: fatoração", "x**2 - 9", "(x - 3)*(x + 3)", True, id="equivalência: fatoração"),
    pytest.param("equivalência: simplificação", "(2*x + 4)/2", "x + 2", True, id="equivalência: simplificação"),
    pytest.param("equivalência: sqrt(x²) = |x|", "sqrt(x**2)", "abs(x)", True, id="equivalência: sqrt(x²) = |x|"),
    pytest.param("equivalência: x²+1 ≠ (x+1)²", "x**2 + 1", "(x + 1)**2", False, id="equivalência: x²+1 ≠ (x+1)²"),
    pytest.param("equivalência: x ≠ 2x", "x", "2*x", False, id="equivalência: x ≠ 2x"),
    pytest.param("equivalência: sqrt(x²) ≠ x", "sqrt(x**2)", "x", False, id="equivalência: sqrt(x²) ≠ x"),
    pytest.param("equivalência: 1/x ≠ 2/x", "1/x", "2/x", False, id="equivalência: 1/x ≠ 2/x"),
    pytest.param("equivalência: entrada inválida", "2 +", "2", None, id="equivalência: entrada inválida"),
])
def test_equivalencia_caracterizacao(name, expressao1, expressao2, expected):
    assert_legacy_equal(name, vm.verificar_equivalencia(expressao1, expressao2), expected)


@pytest.mark.parametrize("name,expressao,resultado,expected", [
    pytest.param("operação 2+3=5", "2 + 3", "5", True, id="operação 2+3=5"),
    pytest.param("operação 2+3=6", "2 + 3", "6", False, id="operação 2+3=6"),
    pytest.param("operação distributiva", "2*(x + 3)", "2*x + 6", True, id="operação distributiva"),
    pytest.param("operação inválida (1/0)", "1/0", "1", None, id="operação inválida (1/0)"),
])
def test_verificar_operacao(name, expressao, resultado, expected):
    actual = vm.verificar_operacao(expressao, resultado)["correta"]
    assert_legacy_equal(name, actual, expected)


@pytest.mark.parametrize("name,expressao1,expressao2,expected", [
    pytest.param("análise de equivalência: x/x vs 1", "x/x", "1", "condicional", id="análise de equivalência: x/x vs 1"),
    pytest.param("análise de equivalência: (x²-1)/(x-1) vs x+1", "(x² - 1)/(x - 1)", "x + 1", "condicional", id="análise de equivalência: (x²-1)/(x-1) vs x+1"),
    pytest.param("análise de equivalência: domínios distintos, mesma função", "x/x", "(x + 1)/(x + 1)", "condicional", id="análise de equivalência: domínios distintos, mesma função"),
    pytest.param("análise de equivalência: sqrt(x)² vs x", "sqrt(x)**2", "x", "condicional", id="análise de equivalência: sqrt(x)² vs x"),
    pytest.param("análise de equivalência: 1/x vs x**(-1)", "1/x", "x**(-1)", "equivalentes", id="análise de equivalência: 1/x vs x**(-1)"),
    pytest.param("análise de equivalência: denominador em outra forma", "1/(x*(x - 1))", "1/(x**2 - x)", "equivalentes", id="análise de equivalência: denominador em outra forma"),
    pytest.param("análise de equivalência: sqrt(x²) vs |x|", "sqrt(x**2)", "abs(x)", "equivalentes", id="análise de equivalência: sqrt(x²) vs |x|"),
    pytest.param("análise de equivalência: expansão sem restrições", "(x + 1)(x - 2)", "x² - x - 2", "equivalentes", id="análise de equivalência: expansão sem restrições"),
    pytest.param("análise de equivalência: x²+1 vs (x+1)²", "x**2 + 1", "(x + 1)**2", "diferentes", id="análise de equivalência: x²+1 vs (x+1)²"),
    pytest.param("análise de equivalência: 1/x vs 2/x", "1/x", "2/x", "diferentes", id="análise de equivalência: 1/x vs 2/x"),
    pytest.param("análise de equivalência: multivar: x*y/x vs y", "x*y/x", "y", "condicional", id="análise de equivalência: multivar: x*y/x vs y"),
    pytest.param("análise de equivalência: multivar: (x+y)/(x+y) vs 1", "(x + y)/(x + y)", "1", "condicional", id="análise de equivalência: multivar: (x+y)/(x+y) vs 1"),
    pytest.param("análise de equivalência: multivar: 1/(x*y) vs 1/x/y", "1/(x*y)", "1/x/y", "equivalentes", id="análise de equivalência: multivar: 1/(x*y) vs 1/x/y"),
    pytest.param("análise de equivalência: entrada inválida", "2 +", "2", "invalido", id="análise de equivalência: entrada inválida"),
])
def test_analisar_equivalencia(name, expressao1, expressao2, expected):
    actual = vm.analisar_equivalencia_expressoes(expressao1, expressao2)["resultado"]
    assert_legacy_equal(name, actual, expected)


@pytest.mark.parametrize("name,expressao1,expressao2,expected", [
    pytest.param("verificar_equivalencia: x/x vs 1 é falso (domínio)", "x/x", "1", False, id="verificar_equivalencia: x/x vs 1 é falso (domínio)"),
    pytest.param("verificar_equivalencia: 1/x vs x**(-1)", "1/x", "x**(-1)", True, id="verificar_equivalencia: 1/x vs x**(-1)"),
])
def test_equivalencia_estrita(name, expressao1, expressao2, expected):
    assert_legacy_equal(name, vm.verificar_equivalencia(expressao1, expressao2), expected)


@pytest.mark.parametrize("name,expressao1,expressao2,expected", [
    pytest.param("equivalência com notação do estudante", "(x + 1)(x - 2)", "x² - x - 2", True, id="equivalência com notação do estudante"),
])
def test_notacao_de_estudante(name, expressao1, expressao2, expected):
    assert_legacy_equal(name, vm.verificar_equivalencia(expressao1, expressao2), expected)
