from threading import Lock, Thread
from time import sleep

from database.respostas_discursivas_repository import (
    buscar_correcao_discursiva_pendente,
    reivindicar_correcao_discursiva,
)
from worker_correcao_discursiva import _processar

_lock = Lock()
_worker = None


def iniciar_correcao_em_segundo_plano(app):
    global _worker
    with _lock:
        if _worker is not None and _worker.is_alive():
            return
        _worker = Thread(target=_executar, args=(app,), daemon=True)
        _worker.start()


def _executar(app):
    while True:
        try:
            tentativa = buscar_correcao_discursiva_pendente()
            if tentativa:
                tentativa_id = tentativa["id"]
                usuario_id = tentativa["usuario_id"]
                if reivindicar_correcao_discursiva(tentativa_id, usuario_id):
                    _processar(tentativa_id, usuario_id, tentativa["disciplina"])
                    continue
        except Exception:
            app.logger.exception("Falha ao processar a fila de correções discursivas")
        sleep(10)
