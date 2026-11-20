import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


x, y = sp.symbols("x y", real=True)
a = sp.Symbol("a", real=True)


def _sistema(equacoes, variaveis=(x, y)):
    return vm.construir_matriz_sistema(list(equacoes), list(variaveis))


_PARAM = _sistema([a*x + y - 1, x + a*y - 1])
_DOBRO = _sistema([2*(a*x + y - 1), x + a*y - 1])
_OUTRO = _sistema([a*x + y - 1, x + a*y - 2])


def _avaliar(condicao, valores):
    resultado = condicao.subs(valores)
    if resultado is sp.true:
        return True
    if resultado is sp.false:
        return False
    return None


def test_parametros_identificados():
    assert_legacy_equal("parâmetros identificados", vm.identificar_parametros_sistema(_PARAM), {a})


def test_numerico_recusa_parametros():
    actual = vm.verificar_equivalencia_sistemas_numericos(_PARAM, _PARAM)
    assert_legacy_equal("numérico recusa parâmetros", actual, None)


@pytest.mark.parametrize("valor,classe,nome,expected", [
    pytest.param(2, "SPD", "classificação paramétrica a=2 é SPD?", True, id="classificação paramétrica a=2 é SPD?"),
    pytest.param(2, "SPI", "classificação paramétrica a=2 é SPI?", False, id="classificação paramétrica a=2 é SPI?"),
    pytest.param(2, "SI", "classificação paramétrica a=2 é SI?", False, id="classificação paramétrica a=2 é SI?"),
    pytest.param(1, "SPD", "classificação paramétrica a=1 é SPD?", False, id="classificação paramétrica a=1 é SPD?"),
    pytest.param(1, "SPI", "classificação paramétrica a=1 é SPI?", True, id="classificação paramétrica a=1 é SPI?"),
    pytest.param(1, "SI", "classificação paramétrica a=1 é SI?", False, id="classificação paramétrica a=1 é SI?"),
    pytest.param(-1, "SPD", "classificação paramétrica a=-1 é SPD?", False, id="classificação paramétrica a=-1 é SPD?"),
    pytest.param(-1, "SPI", "classificação paramétrica a=-1 é SPI?", False, id="classificação paramétrica a=-1 é SPI?"),
    pytest.param(-1, "SI", "classificação paramétrica a=-1 é SI?", True, id="classificação paramétrica a=-1 é SI?"),
])
def test_classificacao_parametrica(valor, classe, nome, expected):
    condicao = vm.classificar_sistemas_possiveis(_PARAM)["condicoes_classificacao"][classe]
    assert_legacy_equal(nome, _avaliar(condicao, {a: valor}), expected)


@pytest.mark.parametrize("valor", [2, 1, -1, 0], ids=["a=2", "a=1", "a=-1", "a=0"])
def test_equacao_multiplicada(valor):
    name = f"sistema com 1ª equação x2, a={valor}"
    condicao = vm.analisar_equivalencia_sistemas_parametricos(_PARAM, _DOBRO)["equivalentes"]
    assert_legacy_equal(name, _avaliar(condicao, {a: valor}), True)


@pytest.mark.parametrize("valor,expected", [(2, False), (1, False), (-1, True)], ids=["a=2", "a=1", "a=-1"])
def test_termo_independente_alterado(valor, expected):
    name = f"sistema com termo independente alterado, a={valor}"
    condicao = vm.analisar_equivalencia_sistemas_parametricos(_PARAM, _OUTRO)["equivalentes"]
    assert_legacy_equal(name, _avaliar(condicao, {a: valor}), expected)
