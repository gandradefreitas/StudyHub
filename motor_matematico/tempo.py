"""Controle de tempo: execução da interface pública em processo isolado."""

import functools
import importlib
import math
import multiprocessing
import sys

from .contrato import (
    STATUS_INDETERMINADO,
    montar_resultado,
)


# Controle de tempo -----------------------------------------------
_configuracao_de_tempo = {"limite": 10.0, "metodo": None}


# Verdadeiro apenas dentro do processo filho.
_EM_PROCESSO_ISOLADO = False


def configurar_limite_de_tempo(segundos=10.0, metodo=None):
    """
    Define o tempo máximo de cada chamada da interface pública.

    segundos: limite em segundos; None desativa o isolamento
        (a execução acontece no próprio processo, sem limite).
    metodo: método de início de processos do multiprocessing
        ("fork", "spawn" ou "forkserver"). Com None, usa "fork"
        quando disponível e "spawn" caso contrário.
    """

    if segundos is not None:
        if (
            isinstance(segundos, bool)
            or not isinstance(segundos, (int, float))
            or not math.isfinite(segundos)
            or segundos <= 0
        ):
            raise ValueError(
                "O limite de tempo deve ser um número positivo ou None."
            )

    _configuracao_de_tempo["limite"] = segundos
    _configuracao_de_tempo["metodo"] = metodo


def _limite_efetivo(fator=1):
    limite = _configuracao_de_tempo["limite"]

    if limite is None:
        return None

    return limite * fator


def _resultado_erro_interno(nome_do_erro, mensagem=None):
    detalhes = {"erro_interno": nome_do_erro}

    if mensagem:
        detalhes["mensagem_do_erro"] = mensagem[:200]

    return montar_resultado(
        STATUS_INDETERMINADO,
        "Não foi possível concluir a verificação.",
        detalhes=detalhes
    )


def _resultado_tempo_excedido(segundos):
    return montar_resultado(
        STATUS_INDETERMINADO,
        "A verificação excedeu o tempo limite e foi interrompida.",
        detalhes={
            "motivo": "tempo_excedido",
            "limite_segundos": segundos
        }
    )


def _executar_protegido(funcao, args, kwargs):
    try:
        return funcao(*args, **kwargs)

    except Exception as erro:
        return _resultado_erro_interno(type(erro).__name__, str(erro))


# Tempo máximo para o processo filho iniciar (importações). Não
# conta no limite de execução.
_LIMITE_DE_PARTIDA = 60.0


def _receber(recebe):
    """Lê uma mensagem do filho, traduzindo falhas em erro."""

    try:
        return recebe.recv()

    except (EOFError, OSError):
        return "erro", "ProcessoEncerrado"

    except Exception:
        return "erro", "RespostaInvalida"


def _executar_no_filho(modulo, nome, args, kwargs, conexao):
    """Roda no processo filho e devolve o resultado pelo pipe."""

    global _EM_PROCESSO_ISOLADO

    _EM_PROCESSO_ISOLADO = True

    try:
        funcao = getattr(importlib.import_module(modulo), nome).__wrapped__

        # A partida (importações) terminou: o pai começa a contar.
        conexao.send(("pronto", None))
        conexao.send(("ok", _executar_protegido(funcao, args, kwargs)))

    except Exception as erro:
        try:
            conexao.send(("erro", type(erro).__name__))
        except Exception:
            pass

    finally:
        conexao.close()


def _executar_com_limite(funcao, args, kwargs, segundos):
    """
    Executa a função em um processo separado, que é encerrado se
    passar do limite de tempo. O tempo de partida do processo não
    conta no limite.
    """

    metodo = _configuracao_de_tempo["metodo"]

    if metodo is None:
        metodo = (
            "fork"
            if "fork" in multiprocessing.get_all_start_methods()
            else "spawn"
        )

    recebe = envia = None
    try:
        contexto = multiprocessing.get_context(metodo)
        recebe, envia = contexto.Pipe(duplex=False)

        # Evita que o filho duplique saída ainda não descarregada.
        for fluxo in (sys.stdout, sys.stderr):
            try:
                fluxo.flush()
            except Exception:
                pass

        processo = contexto.Process(
            target=_executar_no_filho,
            args=(funcao.__module__, funcao.__name__, args, kwargs, envia),
            daemon=True
        )

        processo.start()

    except (AssertionError, OSError, ValueError, RuntimeError) as erro:
        if recebe is not None:
            recebe.close()
        if envia is not None:
            envia.close()
        return _resultado_erro_interno("FalhaNoIsolamento", type(erro).__name__)

    envia.close()

    # Fase 1: partida do processo.
    if recebe.poll(_LIMITE_DE_PARTIDA):
        tipo, valor = _receber(recebe)
    else:
        tipo, valor = "erro", "FalhaNaPartida"

    # Fase 2: execução, esta sim sujeita ao limite.
    if tipo == "pronto":
        if recebe.poll(segundos):
            tipo, valor = _receber(recebe)
        else:
            tipo, valor = "tempo", None

    if tipo != "ok":
        processo.terminate()

    processo.join(1)

    if processo.is_alive():
        processo.kill()
        processo.join()

    recebe.close()

    if tipo == "ok":
        return valor

    if tipo == "tempo":
        return _resultado_tempo_excedido(segundos)

    return _resultado_erro_interno(valor)


def _interface_protegida(funcao=None, *, fator=1):
    """
    Decorador das funções públicas.

    Garante que nenhuma exceção interrompa a correção e aplica o
    limite de tempo, multiplicado por 'fator'. Pode ser usado como
    @_interface_protegida ou @_interface_protegida(fator=4).
    """

    def decorador(f):

        @functools.wraps(f)
        def protegida(*args, **kwargs):
            segundos = _limite_efetivo(fator)

            if _EM_PROCESSO_ISOLADO or segundos is None:
                return _executar_protegido(f, args, kwargs)

            return _executar_com_limite(f, args, kwargs, segundos)

        return protegida

    if funcao is None:
        return decorador

    return decorador(funcao)
