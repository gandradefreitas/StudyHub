from database.conexao import conectar
from services.experiencia_service import calcular_progresso
from services.molduras_service import MOLDURAS, proxima_moldura


def registrar_experiencia(conexao, usuario_id, origem, referencia, exp_decimos):
    if exp_decimos <= 0:
        return
    conexao.execute("""
        INSERT INTO experiencia_atividades (usuario_id, origem, referencia, exp_decimos)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (usuario_id, origem, referencia) DO NOTHING
    """, (usuario_id, origem, str(referencia), exp_decimos))


def obter_nivel(usuario_id, *, notificar=False):
    with conectar() as conexao:
        registro = consultar_experiencia(conexao, usuario_id)
        progresso = calcular_progresso(registro["total"])
        nivel = progresso["nivel"]
        progresso["celebrar"] = False
        progresso["moldura_equipada"] = registro["equipada"]
        progresso["proxima_moldura"] = proxima_moldura(nivel)
        progresso["molduras_conquistadas"] = []

        if notificar and nivel > registro["notificado"]:
            # Serialize apenas as comemorações novas da mesma conta, inclusive entre abas.
            conexao.execute("SELECT id FROM usuarios WHERE id = %s FOR NO KEY UPDATE", (usuario_id,))
            anterior = conexao.execute("""
                SELECT nivel FROM niveis_notificados WHERE usuario_id = %s
            """, (usuario_id,)).fetchone()
            nivel_anterior = anterior["nivel"] if anterior else 0
            if nivel > nivel_anterior:
                conexao.execute("""
                    INSERT INTO niveis_notificados (usuario_id, nivel) VALUES (%s, %s)
                    ON CONFLICT (usuario_id) DO UPDATE SET nivel = EXCLUDED.nivel
                """, (usuario_id, nivel))
                progresso["celebrar"] = True
                progresso["molduras_conquistadas"] = [
                    {"nivel": marco, "nome": nome}
                    for marco, nome in MOLDURAS.items() if nivel_anterior < marco <= nivel
                ]
    return progresso


def consultar_experiencia(conexao, usuario_id):
    return conexao.execute("""
        SELECT
            (SELECT COALESCE(SUM(exp_decimos), 0)
             FROM experiencia_atividades WHERE usuario_id = %(id)s) AS total,
            COALESCE((SELECT nivel FROM molduras_equipadas WHERE usuario_id = %(id)s), 0) AS equipada,
            COALESCE((SELECT nivel FROM niveis_notificados WHERE usuario_id = %(id)s), 0) AS notificado
    """, {"id": usuario_id}).fetchone()


def equipar_moldura(usuario_id, marco):
    if type(marco) is not int or (marco != 0 and marco not in MOLDURAS):
        return False
    with conectar() as conexao:
        if marco == 0:
            conexao.execute("DELETE FROM molduras_equipadas WHERE usuario_id = %s", (usuario_id,))
            return True

        total = consultar_experiencia(conexao, usuario_id)["total"]
        if calcular_progresso(total)["nivel"] < marco:
            return False
        conexao.execute("""
            INSERT INTO molduras_equipadas (usuario_id, nivel) VALUES (%s, %s)
            ON CONFLICT (usuario_id) DO UPDATE SET nivel = EXCLUDED.nivel
        """, (usuario_id, marco))
    return True
