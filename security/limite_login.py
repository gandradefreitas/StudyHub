from datetime import timedelta

from database.conexao import conectar


LIMITE_TENTATIVAS = 5
JANELA_TENTATIVAS = timedelta(minutes=10)
TEMPO_BLOQUEIO = timedelta(minutes=10)


def reservar_tentativa(chave):
    """Reserva uma verificação de senha sem exceder o limite em paralelo."""
    with conectar() as conexao:
        registro = conexao.execute("""
            INSERT INTO tentativas_login (chave, tentativas, primeira_tentativa)
            VALUES (%(chave)s, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (chave) DO UPDATE SET
                tentativas = CASE
                    WHEN CURRENT_TIMESTAMP - tentativas_login.primeira_tentativa >= %(janela)s
                    THEN 1 ELSE tentativas_login.tentativas + 1 END,
                primeira_tentativa = CASE
                    WHEN CURRENT_TIMESTAMP - tentativas_login.primeira_tentativa >= %(janela)s
                    THEN CURRENT_TIMESTAMP ELSE tentativas_login.primeira_tentativa END,
                bloqueado_ate = CASE
                    WHEN CURRENT_TIMESTAMP - tentativas_login.primeira_tentativa < %(janela)s
                         AND tentativas_login.tentativas + 1 >= %(limite)s
                    THEN CURRENT_TIMESTAMP + %(bloqueio)s END
            WHERE tentativas_login.bloqueado_ate IS NULL
                OR tentativas_login.bloqueado_ate <= CURRENT_TIMESTAMP
            RETURNING chave
        """, {
            "chave": chave,
            "janela": JANELA_TENTATIVAS,
            "limite": LIMITE_TENTATIVAS,
            "bloqueio": TEMPO_BLOQUEIO,
        }).fetchone()
    return registro is not None


def limpar_tentativas(chave):
    with conectar() as conexao:
        conexao.execute("DELETE FROM tentativas_login WHERE chave = %s", (chave,))
