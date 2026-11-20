"""Reprocessa correções discursivas indisponíveis, usando a fila no PostgreSQL.

Execute em um processo separado da aplicação Flask e mantenha-o ativo.
"""

import logging
import os
from pathlib import Path
import sys
import time
from logging.handlers import RotatingFileHandler

# O worker é executado como arquivo dentro de studyhub/, mas alguns serviços
# também importam módulos pelo nome do pacote studyhub. Inclua a raiz do
# projeto sem remover studyhub/ do caminho usado pelos imports existentes.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from database.conexao import conectar
from database.criar_banco import criar_tabelas
from database.respostas_discursivas_repository import (
    buscar_correcao_discursiva_pendente,
    obter_respostas,
    reivindicar_correcao_discursiva,
    salvar_resultado_correcao_discursiva,
)
from services.correcao_por_resposta_final import corrigir_tentativa_resposta_final


INTERVALO_VERIFICACAO_SEGUNDOS = 30
CHAVE_LOCK_WORKER = 731905214
BANCOS_PERMITIDOS = {"studyhub", "studyhub_test"}


def _configurar_logging():
    formato = "%(asctime)s %(levelname)s %(message)s"
    handlers = [logging.StreamHandler()]

    pasta_local = os.environ.get("LOCALAPPDATA")
    if pasta_local:
        diretorio_logs = Path(pasta_local) / "StudyHub"
        diretorio_logs.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                diretorio_logs / "worker_correcao_discursiva.log",
                maxBytes=2_000_000,
                backupCount=3,
                encoding="utf-8",
            )
        )

    logging.basicConfig(level=logging.INFO, format=formato, handlers=handlers)


def _processar(tentativa_id, usuario_id, disciplina):
    try:
        pacote = corrigir_tentativa_resposta_final(
            tentativa_id, obter_respostas(tentativa_id), disciplina=disciplina
        )
        status_banco = (
            "corrigida" if pacote["status"] == "corrigida" else "finalizada"
        )
        salvo = salvar_resultado_correcao_discursiva(
            tentativa_id,
            usuario_id,
            pacote,
            status_banco,
            pacote["nota"],
            pacote["nota_maxima"],
        )
        if salvo:
            logging.info(
                "Tentativa %s processada; status do parecer: %s",
                tentativa_id,
                pacote["status"],
            )
        else:
            logging.warning(
                "Tentativa %s não foi atualizada; pode ter mudado de estado.",
                tentativa_id,
            )
    except Exception:
        logging.exception(
            "Falha temporária ao processar tentativa %s; será reagendada.",
            tentativa_id,
        )
        pacote = {
            "status": "indisponivel",
            "mensagem": (
                "O serviço de correção está temporariamente indisponível. "
                "Uma nova tentativa automática foi programada."
            ),
        }
        try:
            salvar_resultado_correcao_discursiva(
                tentativa_id,
                usuario_id,
                pacote,
                "finalizada",
            )
        except Exception:
            logging.exception(
                "Não foi possível reagendar a tentativa %s no banco.",
                tentativa_id,
            )


def _executar_worker_ate_falha():
    conexao_verificacao = conectar()
    try:
        banco = conexao_verificacao.execute(
            "SELECT current_database() AS nome"
        ).fetchone()["nome"]
    finally:
        conexao_verificacao.close()

    # Limita o worker aos bancos conhecidos para evitar processar por engano
    # uma base diferente da usada pelo StudyHub.
    if banco not in BANCOS_PERMITIDOS:
        logging.error(
            "Worker cancelado: DATABASE_URL aponta para '%s'; bancos permitidos: %s.",
            banco,
            ", ".join(sorted(BANCOS_PERMITIDOS)),
        )
        return False

    logging.info("Banco ativo: %s", banco)
    # O worker é separado de app.py e aplica as migrações idempotentes antes
    # de consultar a fila.
    criar_tabelas()
    conexao_lock = conectar()
    cursor_lock = conexao_lock.cursor()
    cursor_lock.execute(
        "SELECT pg_try_advisory_lock(%s) AS adquirido",
        (CHAVE_LOCK_WORKER,),
    )
    if not cursor_lock.fetchone()["adquirido"]:
        logging.warning(
            "Outro worker já possui o lock deste banco; nova verificação em %s segundos.",
            INTERVALO_VERIFICACAO_SEGUNDOS,
        )
        conexao_lock.close()
        return True

    logging.info("Worker de correção discursiva iniciado.")
    try:
        ciclos_sem_pendente = 0
        while True:
            try:
                pendente = buscar_correcao_discursiva_pendente()
            except Exception:
                logging.exception(
                    "Falha ao consultar a fila; nova tentativa em %s segundos.",
                    INTERVALO_VERIFICACAO_SEGUNDOS,
                )
                time.sleep(INTERVALO_VERIFICACAO_SEGUNDOS)
                continue

            if pendente is None:
                ciclos_sem_pendente += 1
                if ciclos_sem_pendente % 10 == 0:
                    logging.info(
                        "Worker ativo; nenhuma correção vencida na fila."
                    )
                time.sleep(INTERVALO_VERIFICACAO_SEGUNDOS)
                continue

            ciclos_sem_pendente = 0
            tentativa_id = pendente["id"]
            usuario_id = pendente["usuario_id"]
            disciplina = pendente["disciplina"]
            try:
                reivindicada = reivindicar_correcao_discursiva(
                    tentativa_id, usuario_id
                )
            except Exception:
                logging.exception(
                    "Falha ao reivindicar tentativa %s; nova tentativa em %s segundos.",
                    tentativa_id,
                    INTERVALO_VERIFICACAO_SEGUNDOS,
                )
                time.sleep(INTERVALO_VERIFICACAO_SEGUNDOS)
                continue

            if not reivindicada:
                logging.info(
                    "Tentativa %s não pôde ser reivindicada; verificando novamente.",
                    tentativa_id,
                )
                time.sleep(INTERVALO_VERIFICACAO_SEGUNDOS)
                continue
            _processar(tentativa_id, usuario_id, disciplina)
    except KeyboardInterrupt:
        logging.info("Worker encerrado pelo operador.")
    finally:
        cursor_lock.execute(
            "SELECT pg_advisory_unlock(%s)",
            (CHAVE_LOCK_WORKER,),
        )
        conexao_lock.close()


def executar_worker():
    _configurar_logging()
    while True:
        try:
            continuar = _executar_worker_ate_falha()
            if not continuar:
                return
        except KeyboardInterrupt:
            logging.info("Worker encerrado pelo operador.")
            return
        except Exception:
            logging.exception(
                "Falha ao iniciar ou manter o worker; nova tentativa em %s segundos.",
                INTERVALO_VERIFICACAO_SEGUNDOS,
            )
        time.sleep(INTERVALO_VERIFICACAO_SEGUNDOS)


if __name__ == "__main__":
    executar_worker()
