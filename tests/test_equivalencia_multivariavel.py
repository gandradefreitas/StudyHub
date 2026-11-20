import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


x, y = sp.symbols("x y", real=True)
a = sp.Symbol("a", real=True)


@pytest.mark.parametrize("name,diferenca1,diferenca2,variaveis,expected", [
    pytest.param("multivar: múltiplo por constante", x + y - 1, 2*(x + y - 1), [x, y], True, id="multivar: múltiplo por constante"),
    pytest.param("multivar: retas distintas", x + y - 1, x - y, [x, y], False, id="multivar: retas distintas"),
    pytest.param("multivar: 0 = 0", sp.Integer(0), sp.Integer(0), [x, y], True, id="multivar: 0 = 0"),
])
def test_multivariavel_basica(name, diferenca1, diferenca2, variaveis, expected):
    actual = vm.verificar_equivalencia_multivariavel(diferenca1, diferenca2, variaveis)
    assert_legacy_equal(name, actual, expected)


@pytest.mark.parametrize("name,diferenca1,diferenca2,variaveis,expected", [
    pytest.param("multivariável: x²+y²=0 vs x²+2y²=0 (mesma solução real)", x**2 + y**2, x**2 + 2*y**2, [x, y], None, id="multivariável: x²+y²=0 vs x²+2y²=0 (mesma solução real)"),
    pytest.param("multivariável: x²+1=0 vs x²+2=0 (ambas sem solução real)", x**2 + 1, x**2 + 2, [x], None, id="multivariável: x²+1=0 vs x²+2=0 (ambas sem solução real)"),
    pytest.param("multivariável: x²=4 vs x=2 (perde solução)", x**2 - 4, x - 2, [x], False, id="multivariável: x²=4 vs x=2 (perde solução)"),
    pytest.param("multivariável: x²=4 vs (x-2)(x+2)=0", x**2 - 4, (x - 2)*(x + 2), [x], True, id="multivariável: x²=4 vs (x-2)(x+2)=0"),
    pytest.param("multivariável: retas distintas", x + y - 1, x - y, [x, y], False, id="multivariável: retas distintas"),
    pytest.param("multivariável: circunferências distintas", x**2 + y**2 - 1, x**2 + y**2 - 4, [x, y], False, id="multivariável: circunferências distintas"),
    pytest.param("multivariável: x*y=0 vs x=0", x*y, x, [x, y], False, id="multivariável: x*y=0 vs x=0"),
    pytest.param("multivariável: equação vs identidade", x + y - 1, sp.Integer(0), [x, y], False, id="multivariável: equação vs identidade"),
    pytest.param("multivariável: múltiplo por constante", x + y - 1, 3*(x + y - 1), [x, y], True, id="multivariável: múltiplo por constante"),
    pytest.param("multivariável: parâmetro pode anular (a=0)", a*x - a, x - 1, [x], None, id="multivariável: parâmetro pode anular (a=0)"),
])
def test_multivariavel_regressoes(name, diferenca1, diferenca2, variaveis, expected):
    actual = vm.verificar_equivalencia_multivariavel(diferenca1, diferenca2, variaveis)
    assert_legacy_equal(name, actual, expected)
