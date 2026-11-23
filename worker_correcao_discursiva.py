"""Worker persistente de correções do StudyHub. Veja docs/fila-correcoes.md."""

import argparse
import json
import logging
import os
from pathlib import Path
import sys
from time import monotonic, sleep

from psycopg.conninfo import conninfo_to_dict

# Alguns módulos do corretor também importam studyhub como pacote.
raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from database.conexao import conectar
from database.fila_redacoes_repository import (
    MAX_TENTATIVAS, PRAZOS_RETRY, encerrar_redacao, recuperar_redacoes_esgotadas,
    reivindicar_redacao,
)
from database.respostas_discursivas_repository import (
    obter_respostas, recuperar_discursivas_esgotadas,
    reivindicar_correcao_discursiva, salvar_resultado_correcao_discursiva,
)
from gemini_client import enviar_mensagem
from services.correcao_por_resposta_final import corrigir_tentativa_resposta_final
from services.redacoes_service import estimar_notas, estimar_notas_ita

INTERVALO_VERIFICACAO = 10
INTERVALO_METRICAS = 300


def processar_discursiva(tentativa):
    tentativa_id = tentativa["id"]
    prazo = None
    try:
        pacote = corrigir_tentativa_resposta_final(
            tentativa_id, obter_respostas(tentativa_id), disciplina=tentativa["disciplina"],
        )
    except Exception as erro:
        numero = tentativa["tentativas_correcao"]
        terminou = numero >= MAX_TENTATIVAS
        pacote = {
            "status": "falha_definitiva" if terminou else "indisponivel",
            "mensagem": "O serviço de correção está temporariamente indisponível.",
        }
        if not terminou:
            prazo = PRAZOS_RETRY[numero - 1]
        logging.warning("Discursiva %s, tentativa %s: %s.", tentativa_id, numero, type(erro).__name__)
    salvo = salvar_resultado_correcao_discursiva(
        tentativa_id, tentativa["usuario_id"], pacote,
        "corrigida" if pacote["status"] == "corrigida" else "finalizada",
        pacote.get("nota"), pacote.get("nota_maxima"),
        reivindicada_ate=tentativa["correcao_reivindicada_ate"], tentar_em=prazo,
    )
    logging.info("Discursiva %s: %s.", tentativa_id, pacote["status"] if salvo else "reserva expirada")


def processar_redacao(envio):
    try:
        if envio["instituicao"] == "ITA":
            notas = estimar_notas_ita(enviar_mensagem, envio["tema"], envio["titulo"], envio["texto"])
        else:
            notas = estimar_notas(enviar_mensagem, envio["tema"], envio["texto"])
    except (RuntimeError, ValueError) as erro:
        notas = None
        logging.warning("Redação %s, tentativa %s: %s.",
                        envio["id"], envio["correcao_tentativas"], type(erro).__name__)

    salvo = encerrar_redacao(envio, notas)
    if salvo:
        logging.info("Redação %s: %s.", envio["id"], "corrigida" if notas is not None else "falha")
    else:
        logging.info("Redação %s: reserva expirada.", envio["id"])


def processar_pendencias():
    recuperar_discursivas_esgotadas()
    recuperar_redacoes_esgotadas()
    # Busque a segunda fila somente após concluir o trabalho da primeira.
    # Assim uma reserva nunca expira enquanto aguarda processamento local.
    movimentou = False
    for reivindicar, processar in (
        (reivindicar_correcao_discursiva, processar_discursiva),
        (reivindicar_redacao, processar_redacao),
    ):
        item = reivindicar()
        if item:
            movimentou = True
            processar(item)
    return movimentou


def status_filas():
    with conectar() as conexao:
        return conexao.execute("""
            WITH trabalhos AS (
                SELECT 'discursivas' AS fila,
                    data_finalizacao AT TIME ZONE current_setting('TimeZone') AS criado_em,
                    correcao_reivindicada_ate AS reserva,
                    proxima_tentativa_correcao AS disponivel_em,
                    COALESCE(resultado_correcao->>'status' = 'falha_definitiva', FALSE) AS falhou
                FROM tentativas_provas_discursivas
                WHERE status = 'finalizada' AND disciplina IN ('Matemática', 'Física', 'Química')
                    AND (resultado_correcao IS NULL OR resultado_correcao->>'status'
                         IN ('indisponivel', 'falha_definitiva'))
                UNION ALL
                SELECT 'redacoes', criado_em AT TIME ZONE 'America/Sao_Paulo',
                    correcao_reivindicada_ate, correcao_tentar_apos, correcao_falhou
                FROM redacoes WHERE nota IS NULL
            )
            SELECT catalogo.fila,
                COUNT(*) FILTER (WHERE NOT falhou AND reserva > CURRENT_TIMESTAMP) AS processando,
                COUNT(*) FILTER (WHERE NOT falhou AND (reserva IS NULL OR reserva <= CURRENT_TIMESTAMP)
                       AND disponivel_em > CURRENT_TIMESTAMP) AS reagendadas,
                COUNT(*) FILTER (WHERE NOT falhou AND (reserva IS NULL OR reserva <= CURRENT_TIMESTAMP)
                       AND (disponivel_em IS NULL OR disponivel_em <= CURRENT_TIMESTAMP)) AS pendentes,
                COUNT(*) FILTER (WHERE falhou) AS falhas,
                EXTRACT(EPOCH FROM CURRENT_TIMESTAMP - MIN(criado_em) FILTER (WHERE NOT falhou))::bigint
                    AS idade_mais_antiga_segundos
            FROM (VALUES ('discursivas'), ('redacoes')) AS catalogo(fila)
            LEFT JOIN trabalhos USING (fila)
            GROUP BY catalogo.fila ORDER BY catalogo.fila
        """).fetchall()


def verificar_banco():
    esperado = os.environ.get("STUDYHUB_BANCO_WORKER")
    if not esperado:
        esperado = conninfo_to_dict(os.environ["DATABASE_URL"]).get("dbname")
        if esperado not in {"studyhub", "studyhub_test"}:
            raise SystemExit("Configure STUDYHUB_BANCO_WORKER com o nome esperado do banco.")
    with conectar() as conexao:
        atual = conexao.execute("SELECT current_database() AS nome").fetchone()["nome"]
    if atual != esperado:
        raise SystemExit("O banco configurado difere de STUDYHUB_BANCO_WORKER.")
    logging.info("Worker conectado ao banco %s.", atual)


def executar_worker():
    parser = argparse.ArgumentParser(description=__doc__)
    opcoes = parser.add_mutually_exclusive_group()
    opcoes.add_argument("--status", action="store_true", help="mostra totais e idade da fila em JSON")
    opcoes.add_argument("--uma-vez", action="store_true", help="processa até uma tarefa por fila e termina")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.status or args.uma_vez:
        verificar_banco()
        if args.status:
            print(json.dumps(status_filas(), ensure_ascii=False))
        else:
            processar_pendencias()
        return

    banco_verificado = False
    ultima_medicao = None
    while True:
        try:
            if not banco_verificado:
                verificar_banco()
                banco_verificado = True
            agora = monotonic()
            if ultima_medicao is None or agora - ultima_medicao >= INTERVALO_METRICAS:
                logging.info("Estado das filas: %s", json.dumps(status_filas(), ensure_ascii=False))
                ultima_medicao = agora
            if processar_pendencias():
                continue
        except Exception as erro:
            banco_verificado = False
            logging.error("Erro ao processar as filas: %s. Nova verificação em %s segundos.",
                          type(erro).__name__, INTERVALO_VERIFICACAO)
        sleep(INTERVALO_VERIFICACAO)


if __name__ == "__main__":
    try:
        executar_worker()
    except KeyboardInterrupt:
        logging.info("Worker encerrado pelo operador.")
