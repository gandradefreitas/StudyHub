"""Auxiliares dos testes de controle de tempo. Precisam estar em um módulo importável pelo processo filho."""

from .contrato import (
    STATUS_CORRETO,
    montar_resultado,
)
from .tempo import _interface_protegida


# ----------------------------------------------------------------
# Auxiliares dos testes de controle de tempo
# Precisam estar no nível do módulo: o processo filho (método
# "spawn") reimporta o módulo e não executa o bloco __main__.
# ----------------------------------------------------------------
@_interface_protegida
def _auxiliar_lento_para_teste(segundos):
    import time

    time.sleep(segundos)

    return montar_resultado(STATUS_CORRETO, "concluída")


@_interface_protegida
def _auxiliar_com_erro_para_teste():
    return 1 / 0


@_interface_protegida
def _auxiliar_que_derruba_o_processo():
    import os

    os._exit(1)
