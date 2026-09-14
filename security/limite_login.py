from datetime import datetime, timedelta, timezone

from database.conexao import conectar


LIMITE_TENTATIVAS = 5
JANELA_TENTATIVAS = timedelta(minutes=10)
TEMPO_BLOQUEIO = timedelta(minutes=10)


def verificar_bloqueio(chave):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT tentativas, primeira_tentativa, bloqueado_ate
        FROM tentativas_login
        WHERE chave = %s
    """, (chave,))

    registro = cursor.fetchone()

    if registro is None:
        cursor.close()
        conexao.close()
        return False

    agora = datetime.now(timezone.utc)

    bloqueado_ate = registro["bloqueado_ate"]

    if bloqueado_ate is not None:

        if bloqueado_ate.tzinfo is None:
            bloqueado_ate = bloqueado_ate.replace(
                tzinfo=timezone.utc
            )

        if agora < bloqueado_ate:
            cursor.close()
            conexao.close()
            return True

    primeira_tentativa = registro["primeira_tentativa"]

    if primeira_tentativa.tzinfo is None:
        primeira_tentativa = primeira_tentativa.replace(
            tzinfo=timezone.utc
        )

    if agora - primeira_tentativa >= JANELA_TENTATIVAS:

        cursor.execute("""
            DELETE FROM tentativas_login
            WHERE chave = %s
        """, (chave,))

        conexao.commit()

    cursor.close()
    conexao.close()

    return False


def registrar_tentativa_falha(chave):
    conexao = conectar()
    cursor = conexao.cursor()

    agora = datetime.now(timezone.utc)

    cursor.execute("""
        SELECT tentativas, primeira_tentativa
        FROM tentativas_login
        WHERE chave = %s
    """, (chave,))

    registro = cursor.fetchone()

    if registro is None:

        cursor.execute("""
            INSERT INTO tentativas_login
            (
                chave,
                tentativas,
                primeira_tentativa
            )
            VALUES (%s, 1, %s)
        """, (
            chave,
            agora
        ))

    else:

        primeira_tentativa = registro["primeira_tentativa"]

        if primeira_tentativa.tzinfo is None:
            primeira_tentativa = primeira_tentativa.replace(
                tzinfo=timezone.utc
            )

        if agora - primeira_tentativa >= JANELA_TENTATIVAS:

            cursor.execute("""
                UPDATE tentativas_login
                SET
                    tentativas = 1,
                    primeira_tentativa = %s,
                    bloqueado_ate = NULL
                WHERE chave = %s
            """, (
                agora,
                chave
            ))

        else:

            novas_tentativas = registro["tentativas"] + 1

            if novas_tentativas >= LIMITE_TENTATIVAS:

                bloqueado_ate = agora + TEMPO_BLOQUEIO

                cursor.execute("""
                    UPDATE tentativas_login
                    SET
                        tentativas = %s,
                        bloqueado_ate = %s
                    WHERE chave = %s
                """, (
                    novas_tentativas,
                    bloqueado_ate,
                    chave
                ))

            else:

                cursor.execute("""
                    UPDATE tentativas_login
                    SET tentativas = %s
                    WHERE chave = %s
                """, (
                    novas_tentativas,
                    chave
                ))

    conexao.commit()

    cursor.close()
    conexao.close()


def limpar_tentativas(chave):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        DELETE FROM tentativas_login
        WHERE chave = %s
    """, (chave,))

    conexao.commit()

    cursor.close()
    conexao.close()