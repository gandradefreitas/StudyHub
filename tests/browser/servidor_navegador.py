import json
import os
import sys
from datetime import date
from threading import Event, Thread
from uuid import uuid4

from psycopg.conninfo import conninfo_to_dict
from werkzeug.serving import make_server


def main():
    params = conninfo_to_dict(os.environ["DATABASE_URL"])
    if (
        params.get("dbname") != "studyhub_test"
        or params.get("host") not in {"127.0.0.1", "localhost", "::1"}
        or params.get("hostaddr", "") not in {"", "127.0.0.1", "::1"}
        or "service" in params
    ):
        raise SystemExit("O navegador de teste exige o banco local studyhub_test.")
    os.environ["SECRET_KEY"] = uuid4().hex
    from database.conexao import conectar
    from database.criar_banco import criar_tabelas
    from database.usuario_repository import excluir_usuario

    with conectar() as conexao:
        if conexao.execute("SELECT current_database() AS nome").fetchone()["nome"] != "studyhub_test":
            raise SystemExit("Banco inesperado.")
    criar_tabelas()
    from app import app

    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    with conectar() as conexao:
        usuario = conexao.execute("""
            INSERT INTO usuarios (nome, email, tema)
            VALUES ('Navegador de teste', %s, 'sistema') RETURNING id
        """, (f"{uuid4().hex}@example.invalid",)).fetchone()["id"]

    try:
        with conectar() as conexao:
            conexao.execute("""
                INSERT INTO leituras_idiomas (usuario_id, texto_id, palavras, acertos, concluido_em)
                VALUES (%s, 'teste', 135, 8, %s)
            """, (usuario, date.today()))
            conexao.execute("""
                INSERT INTO resultados_provas
                    (usuario_id, prova_id, acertos, erros, tempo_gasto, nao_respondidas, total, porcentagem)
                VALUES (%s, 3, 13, 35, '00:02:33', 0, 48, 27.08)
            """, (usuario,))

        servidor = make_server("127.0.0.1", 0, app)
        servidor.timeout = 0.25
        fechar = Event()

        def observar_encerramento():
            sys.stdin.read()
            fechar.set()

        Thread(target=observar_encerramento, daemon=True).start()
        sessao = app.session_interface.get_signing_serializer(app).dumps(
            {"usuario_id": usuario, "nome": "Navegador de teste"},
        )
        print(json.dumps({"porta": servidor.server_port, "sessao": sessao}), flush=True)
        try:
            while not fechar.is_set():
                servidor.handle_request()
        finally:
            servidor.server_close()
    finally:
        if not excluir_usuario(usuario):
            raise RuntimeError("Não foi possível limpar o usuário descartável do navegador.")


if __name__ == "__main__":
    main()
