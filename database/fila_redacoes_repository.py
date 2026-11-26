from database.conexao import conectar
from database.experiencia_repository import registrar_experiencia
from services.experiencia_service import exp_redacao
from psycopg.types.json import Jsonb

MAX_TENTATIVAS = 4
PRAZOS_RETRY = (30, 120, 300)


def registrar_envio(conexao, usuario_id, tema, ano, texto, instituicao, titulo,
                    *, chave_envio, tempo_segundos=None):
    registro = conexao.execute("""
        INSERT INTO redacoes
            (usuario_id, tema, ano, texto, instituicao, titulo, chave_envio, tempo_segundos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (usuario_id, chave_envio) WHERE chave_envio IS NOT NULL DO NOTHING
        RETURNING id
    """, (usuario_id, tema, ano, texto, instituicao, titulo, chave_envio, tempo_segundos)).fetchone()
    if registro is None:
        registro = conexao.execute("""
            SELECT id FROM redacoes WHERE usuario_id = %s AND chave_envio = %s
        """, (usuario_id, chave_envio)).fetchone()
    return registro["id"]


def obter_envio_repetido(conexao, usuario_id, chave_envio):
    return conexao.execute("""
        SELECT id FROM redacoes WHERE usuario_id = %s AND chave_envio = %s
    """, (usuario_id, chave_envio)).fetchone()


def reivindicar_redacao(envio_id=None):
    with conectar() as conexao:
        return conexao.execute("""
            WITH candidata AS (
                SELECT id FROM redacoes
                WHERE nota IS NULL AND NOT correcao_falhou
                  AND correcao_tentativas < %s
                  AND id = COALESCE(%s::integer, id)
                  AND (correcao_tentar_apos IS NULL OR correcao_tentar_apos <= CURRENT_TIMESTAMP)
                  AND (correcao_reivindicada_ate IS NULL OR correcao_reivindicada_ate <= CURRENT_TIMESTAMP)
                ORDER BY criado_em, id
                LIMIT 1 FOR UPDATE SKIP LOCKED
            )
            UPDATE redacoes AS r
            SET correcao_reivindicada_ate = CURRENT_TIMESTAMP + INTERVAL '5 minutes',
                correcao_tentativas = correcao_tentativas + 1
            FROM candidata WHERE r.id = candidata.id
            RETURNING r.id, r.tema, r.texto, r.instituicao, r.titulo,
                      r.correcao_reivindicada_ate, r.correcao_tentativas
        """, (MAX_TENTATIVAS, envio_id)).fetchone()


def encerrar_redacao(envio, notas):
    tentativas = envio["correcao_tentativas"]
    falhou = notas is None and tentativas >= MAX_TENTATIVAS
    intervalo = PRAZOS_RETRY[tentativas - 1] if notas is None and not falhou else None
    with conectar() as conexao:
        registro = conexao.execute("""
            UPDATE redacoes
            SET notas = %s, nota = %s, correcao_falhou = %s,
                correcao_tentar_apos = CURRENT_TIMESTAMP + %s * INTERVAL '1 second',
                correcao_reivindicada_ate = NULL
            WHERE id = %s AND nota IS NULL AND correcao_reivindicada_ate = %s
              AND correcao_reivindicada_ate > CURRENT_TIMESTAMP
            RETURNING usuario_id, instituicao, nota
        """, (Jsonb(notas) if notas is not None else None,
              sum(notas) if notas is not None else None, falhou, intervalo,
              envio["id"], envio["correcao_reivindicada_ate"])).fetchone()
        if registro is not None and registro["nota"] is not None:
            registrar_experiencia(
                conexao, registro["usuario_id"], "redacao", envio["id"],
                exp_redacao(registro["nota"], registro["instituicao"]),
            )
        return registro is not None


def reagendar_redacao(envio_id, usuario_id):
    with conectar() as conexao:
        return conexao.execute("""
            UPDATE redacoes
            SET correcao_falhou = FALSE, correcao_tentativas = 0, correcao_tentar_apos = NULL
            WHERE id = %s AND usuario_id = %s AND nota IS NULL AND correcao_falhou
        """, (envio_id, usuario_id)).rowcount == 1


def recuperar_redacoes_esgotadas():
    with conectar() as conexao:
        conexao.execute("""
            UPDATE redacoes
            SET correcao_falhou = TRUE, correcao_reivindicada_ate = NULL,
                correcao_tentar_apos = NULL
            WHERE nota IS NULL AND NOT correcao_falhou AND correcao_tentativas >= %s
              AND (correcao_reivindicada_ate IS NULL OR correcao_reivindicada_ate <= CURRENT_TIMESTAMP)
        """, (MAX_TENTATIVAS,))
