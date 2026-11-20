"""Interpretação de equações."""

import sympy as sp

from .dominio import (
    identificar_restricoes,
    identificar_restricoes_raizes,
    obter_condicoes_denominadores,
    obter_condicoes_raizes,
    obter_variaveis_equacao,
)
from .interpretador import interpretar_expressao


def interpretar_equacao(equacao):
    if not isinstance(equacao, str) or len(equacao) > 400:
        raise ValueError("Equação inválida.")

    if equacao.count("=") != 1:
        raise ValueError(
            "A equação deve conter exatamente um sinal de igualdade."
        )

    esquerda, direita = equacao.split("=")

    esquerda = esquerda.strip()
    direita = direita.strip()

    membro_esquerdo = interpretar_expressao(esquerda)
    membro_direito = interpretar_expressao(direita)

    variaveis_equacao = (
        obter_variaveis_equacao(equacao)
    )

    if len(variaveis_equacao) <= 1:
        restricoes_esquerda = identificar_restricoes(esquerda)
        restricoes_direita = identificar_restricoes(direita)
    else:
        restricoes_esquerda = []
        restricoes_direita = []

    if len(variaveis_equacao) <= 1:
        restricoes_raizes_esquerda = identificar_restricoes_raizes(esquerda)
        restricoes_raizes_direita = identificar_restricoes_raizes(direita)
    else:
        restricoes_raizes_esquerda = []
        restricoes_raizes_direita = []

    condicoes_denominadores_esquerda = obter_condicoes_denominadores(esquerda)
    condicoes_denominadores_direita = obter_condicoes_denominadores(direita)

    condicoes_raizes_esquerda = obter_condicoes_raizes(esquerda)
    condicoes_raizes_direita = obter_condicoes_raizes(direita)

    if (
            restricoes_esquerda is None
            or restricoes_direita is None
            or restricoes_raizes_esquerda is None
            or restricoes_raizes_direita is None
            or condicoes_denominadores_esquerda is None
            or condicoes_denominadores_direita is None
            or condicoes_raizes_esquerda is None
            or condicoes_raizes_direita is None
    ):
        raise ValueError("Não foi possível determinar o domínio da equação.")

    return {
        "esquerda": membro_esquerdo,
        "direita": membro_direito,
        "diferenca": sp.simplify(
            membro_esquerdo - membro_direito
        ),
        "restricoes_esquerda": restricoes_esquerda,
        "restricoes_direita": restricoes_direita,
        "restricoes_raizes_esquerda": restricoes_raizes_esquerda,
        "restricoes_raizes_direita": restricoes_raizes_direita,
        "condicoes_denominadores_esquerda": obter_condicoes_denominadores(esquerda),
        "condicoes_denominadores_direita": obter_condicoes_denominadores(direita),
        "condicoes_raizes_esquerda": condicoes_raizes_esquerda,
        "condicoes_raizes_direita": condicoes_raizes_direita,
    }


def obter_condicoes_dominio(dados_equacao):

    condicoes = []

    condicoes.extend(
        dados_equacao["condicoes_denominadores_esquerda"]
    )

    condicoes.extend(
        dados_equacao["condicoes_denominadores_direita"]
    )

    condicoes.extend(
        dados_equacao["condicoes_raizes_esquerda"]
    )

    condicoes.extend(
        dados_equacao["condicoes_raizes_direita"]
    )

    return condicoes
