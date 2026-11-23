import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal, assert_legacy_error


pytestmark = pytest.mark.matematica


x = sp.Symbol("x", real=True)


@pytest.mark.parametrize("name,call,expected", [
    pytest.param("interpretar 2 + 3", lambda: vm.interpretar_expressao("2 + 3"), 5, id="interpretar 2 + 3"),
    pytest.param("interpretar decimal 0.5", lambda: vm.interpretar_expressao("0.5"), sp.Rational(1, 2), id="interpretar decimal 0.5"),
])
def test_entradas_validas(name, call, expected):
    assert_legacy_equal(name, call(), expected)


@pytest.mark.parametrize("name,entrada", [
    pytest.param("rejeitar código arbitrário", "__import__('os')", id="rejeitar código arbitrário"),
    pytest.param("rejeitar booleano", "True + 1", id="rejeitar booleano"),
    pytest.param("rejeitar número complexo", "1.5j", id="rejeitar número complexo"),
    pytest.param("rejeitar variável com 2 letras", "xy + 1", id="rejeitar variável com 2 letras"),
    pytest.param("rejeitar expoente > 100", "2**101", id="rejeitar expoente > 100"),
    pytest.param("rejeitar divisão por zero", "1/0", id="rejeitar divisão por zero"),
    pytest.param("rejeitar zero com expoente negativo", "0**(-1)", id="rejeitar zero com expoente negativo"),
    pytest.param("rejeitar raiz de negativo", "sqrt(-4)", id="rejeitar raiz de negativo"),
    pytest.param("rejeitar expoente não inteiro", "2**x", id="rejeitar expoente não inteiro"),
    pytest.param("rejeitar inteiro grande demais", "1000000000000000000", id="rejeitar inteiro grande demais"),
    pytest.param("rejeitar entrada longa demais", "x" + "+x" * 200, id="rejeitar entrada longa demais"),
    pytest.param("rejeitar entrada não textual", 5, id="rejeitar entrada não textual"),
])
def test_entradas_rejeitadas(name, entrada):
    assert_legacy_error(name, lambda: vm.interpretar_expressao(entrada))


@pytest.mark.parametrize("name,entrada,expected", [
    pytest.param("normalização: multiplicação implícita", "2x + 1", 2*x + 1, id="normalização: multiplicação implícita"),
    pytest.param("normalização: número e parênteses", "2(x + 3)", 2*(x + 3), id="normalização: número e parênteses"),
    pytest.param("normalização: variável e parênteses", "x(x + 1)", x*(x + 1), id="normalização: variável e parênteses"),
    pytest.param("normalização: parênteses adjacentes", "(x + 1)(x - 2)", (x + 1)*(x - 2), id="normalização: parênteses adjacentes"),
    pytest.param("normalização: potência com ^", "x^2", x**2, id="normalização: potência com ^"),
    pytest.param("normalização: potência com ²", "x²", x**2, id="normalização: potência com ²"),
    pytest.param("normalização: potência com ⁻¹", "x⁻¹", 1/x, id="normalização: potência com ⁻¹"),
    pytest.param("normalização: ² com coeficiente", "2x² + 1", 2*x**2 + 1, id="normalização: ² com coeficiente"),
    pytest.param("normalização: vírgula decimal", "0,5", sp.Rational(1, 2), id="normalização: vírgula decimal"),
    pytest.param("normalização: vírgula com variável", "1,5x", sp.Rational(3, 2)*x, id="normalização: vírgula com variável"),
    pytest.param("normalização: notação científica", "1e-3", sp.Rational(1, 1000), id="normalização: notação científica"),
    pytest.param("normalização: símbolos ×, ·, ÷, −", "6 ÷ 3 + 2 × 2 − 1", 5, id="normalização: símbolos ×, ·, ÷, −"),
    pytest.param("normalização: ponto médio", "3 · x", 3*x, id="normalização: ponto médio"),
    pytest.param("normalização: função com coeficiente", "2sqrt(x)", 2*sp.sqrt(x), id="normalização: função com coeficiente"),
    pytest.param("normalização: agrupamento antes de variável", "(1/2)x", x/2, id="normalização: agrupamento antes de variável"),
    pytest.param("normalização: divisão explícita", "1/(2x)", 1/(2*x), id="normalização: divisão explícita"),
    pytest.param("normalização: (x²)^50 é aceito", "(x**2)**50", x**100, id="normalização: (x²)^50 é aceito"),
])
def test_normalizacao_aceita(name, entrada, expected):
    assert_legacy_equal(name, vm.interpretar_expressao(entrada), expected)


@pytest.mark.parametrize("name,entrada", [
    pytest.param("normalização rejeita: ambígua 1/2x", "1/2x", id="normalização rejeita: ambígua 1/2x"),
    pytest.param("normalização rejeita: ambígua x/2(x+1)", "x/2(x + 1)", id="normalização rejeita: ambígua x/2(x+1)"),
    pytest.param("normalização rejeita: número complexo 1.5j", "1.5j", id="normalização rejeita: número complexo 1.5j"),
    pytest.param("normalização rejeita: número complexo 2j", "2j", id="normalização rejeita: número complexo 2j"),
    pytest.param("normalização rejeita: variável de 2 letras após coeficiente", "2xy", id="normalização rejeita: variável de 2 letras após coeficiente"),
    pytest.param("normalização rejeita: dois números separados", "2 3", id="normalização rejeita: dois números separados"),
    pytest.param("normalização rejeita: vírgula como separador", "x,y", id="normalização rejeita: vírgula como separador"),
    pytest.param("normalização rejeita: potência numérica aninhada", "((9**100)**100)**100", id="normalização rejeita: potência numérica aninhada"),
    pytest.param("normalização rejeita: potência simbólica aninhada", "((x + 1)**2)**51", id="normalização rejeita: potência simbólica aninhada"),
])
def test_normalizacao_rejeita(name, entrada):
    assert_legacy_error(name, lambda: vm.interpretar_expressao(entrada))
