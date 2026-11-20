import pytest
import sympy as sp

import verificador_matematico as vm
from tests.math_test_support import assert_legacy_equal, assert_legacy_error


@pytest.fixture(autouse=True)
def verificar_banco_de_testes():
    return None


x = sp.Symbol("x", real=True)


def _sinalizar_esperado(e1, e2):
    return vm.verificar_equivalencia_equacoes(e1, e2)


@pytest.mark.parametrize("name,equacao1,equacao2,expected", [
    pytest.param("equação: x²=4 vs fatorada", "x**2 = 4", "(x - 2)*(x + 2) = 0", True, id="equação: x²=4 vs fatorada"),
    pytest.param("equação: x²=4 vs x=2 (perde solução)", "x**2 = 4", "x = 2", False, id="equação: x²=4 vs x=2 (perde solução)"),
    pytest.param("equação: x²=9 vs x=3", "x**2 = 9", "x = 3", False, id="equação: x²=9 vs x=3"),
    pytest.param("equação: lados trocados", "x = 2", "2 = x", True, id="equação: lados trocados"),
    pytest.param("equação: simplificação com domínio", "(x**2 - 1)/(x - 1) = 0", "x + 1 = 0", True, id="equação: simplificação com domínio"),
    pytest.param("equação: raiz extra pelo domínio", "(x**2 - 1)/(x - 1) = 2", "x + 1 = 2", False, id="equação: raiz extra pelo domínio"),
    pytest.param("equação: equação com raiz", "sqrt(x) = 2", "x = 4", True, id="equação: equação com raiz"),
    pytest.param("equação: duas variáveis (não suportado)", "x + y = 1", "y = 1 - x", None, id="equação: duas variáveis (não suportado)"),
    pytest.param("equação: dois sinais de igualdade", "x = 1", "x = 1 = 2", None, id="equação: dois sinais de igualdade"),
])
def test_equivalencia_equacoes(name, equacao1, equacao2, expected):
    assert_legacy_equal(name, _sinalizar_esperado(equacao1, equacao2), expected)


def test_interpretar_equacao_diferenca():
    name = "interpretar_equacao: diferença"
    assert_legacy_equal(name, vm.interpretar_equacao("x = 2")["diferenca"], x - 2)


def test_interpretar_equacao_sem_igualdade():
    assert_legacy_error("interpretar_equacao sem '='", lambda: vm.interpretar_equacao("x + 1"))


@pytest.mark.parametrize("name,equacao1,equacao2,expected", [
    pytest.param("equação com notação do estudante", "x² = 4", "(x - 2)(x + 2) = 0", True, id="equação com notação do estudante"),
    pytest.param("equação linear com notação do estudante", "2x + 6 = 10", "x = 2", True, id="equação linear com notação do estudante"),
])
def test_equacoes_notacao_estudante(name, equacao1, equacao2, expected):
    assert_legacy_equal(name, _sinalizar_esperado(equacao1, equacao2), expected)
