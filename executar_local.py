"""Inicia o servidor e a fila em processos distintos no ambiente local."""

from pathlib import Path
import os
from signal import SIGTERM, signal
from subprocess import Popen, TimeoutExpired
import sys
from time import sleep


def encerrar(_sinal, _quadro):
    raise SystemExit(0)


def executar(*, render=False):
    raiz = Path(__file__).resolve().parent
    processos = []
    try:
        web = (
            ["-m", "gunicorn", "--bind", f"0.0.0.0:{os.getenv('PORT', '10000')}", "app:app"]
            if render else [str(raiz / "app.py")]
        )
        for comando in ([str(raiz / "worker_correcao_discursiva.py")], web):
            processos.append(Popen([sys.executable, *comando], cwd=raiz))
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
    signal(SIGTERM, encerrar)
    raise SystemExit(executar(render=sys.argv[1:] == ["--render"]))
