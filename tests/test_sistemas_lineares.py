import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


x, y = sp.symbols("x y", real=True)


def _sistema(equacoes, variaveis=(x, y)):
    return vm.construir_matriz_sistema(list(equacoes), list(variaveis))


def _classificar(equacoes):
    dados = _sistema(equacoes)
    return vm.classificar_sistema(vm.analisar_postos_sistema(dados))


@pytest.mark.parametrize("name,equacoes,expected", [
    pytest.param("classificação SPD", [x + y - 3, x - y - 1], "SPD", id="classificação SPD"),
    pytest.param("classificação SPI", [x + y - 2, 2*x + 2*y - 4], "SPI", id="classificação SPI"),
    pytest.param("classificação SI", [x + y - 1, x + y - 2], "SI", id="classificação SI"),
])
def test_classificacao(name, equacoes, expected):
    assert_legacy_equal(name, _classificar(equacoes), expected)


_BASE = [x + y - 3, x - y - 1]
@pytest.mark.parametrize("name,outro,expected", [
    pytest.param("sistema numérico: mesma solução, outra forma", [2*x - 4, y - 1], True, id="sistema numérico: mesma solução, outra forma"),
    pytest.param("sistema numérico: equação redundante", [x + y - 3, x - y - 1, 2*x - 4], True, id="sistema numérico: equação redundante"),
    pytest.param("sistema numérico: solução diferente", [x + y - 3, x - y - 2], False, id="sistema numérico: solução diferente"),
    pytest.param("sistema numérico: possível vs impossível", [x + y - 1, x + y - 2], False, id="sistema numérico: possível vs impossível"),
])
def test_equivalencia_sistemas_numericos(name, outro, expected):
    actual = vm.verificar_equivalencia_sistemas_numericos(_sistema(_BASE), _sistema(outro))
    assert_legacy_equal(name, actual, expected)


def test_sistemas_impossiveis_equivalentes():
    actual = vm.verificar_equivalencia_sistemas_numericos(
        _sistema([x + y - 1, x + y - 2]),
        _sistema([x - 1, x - 2]),
    )
    assert_legacy_equal("sistemas impossíveis equivalentes", actual, True)
