"""Inicia o servidor e a fila em processos distintos no ambiente local."""

from pathlib import Path
from subprocess import Popen, TimeoutExpired
import sys
from time import sleep


def executar():
    raiz = Path(__file__).resolve().parent
    processos = []
    try:
        for arquivo in ("worker_correcao_discursiva.py", "app.py"):
            processos.append(Popen([sys.executable, str(raiz / arquivo)], cwd=raiz))
        while True:
            for processo in processos:
                codigo = processo.poll()
                if codigo is not None:
                    return codigo
            sleep(0.25)
    except KeyboardInterrupt:
        return 0
    finally:
        for processo in processos:
            if processo.poll() is None:
                processo.terminate()
        for processo in processos:
            try:
                processo.wait(timeout=5)
            except TimeoutExpired:
                processo.kill()
                processo.wait()


if __name__ == "__main__":
    raise SystemExit(executar())
