from uuid import uuid4

from database.conexao import conectar


class TentativaObjetivaEncerrada(ValueError):
    """A tentativa objetiva não está mais aberta para esta conta."""


def obter_ou_criar_tentativa_objetiva(usuario_id, prova_id):
    with conectar() as conexao:
        return conexao.execute("""
            INSERT INTO tentativas_provas_objetivas (id, usuario_id, prova_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (usuario_id, prova_id) WHERE resultado_id IS NULL
                DO UPDATE SET prova_id = EXCLUDED.prova_id
            RETURNING id, inicio
        """, (uuid4(), usuario_id, prova_id)).fetchone()


def obter_inicio_tentativa_objetiva(usuario_id, prova_id, tentativa_id):
    with conectar() as conexao:
        registro = conexao.execute("""
            SELECT inicio FROM tentativas_provas_objetivas
            WHERE usuario_id = %s AND prova_id = %s AND id = %s AND resultado_id IS NULL
        """, (usuario_id, prova_id, tentativa_id)).fetchone()
    return registro["inicio"] if registro else None
