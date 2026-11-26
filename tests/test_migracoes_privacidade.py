from uuid import uuid4

import pytest
from psycopg import errors, sql

from controllers.web import autenticacao_controller
from database.conexao import conectar
from database.criar_banco import aplicar_migracoes, verificar_esquema_web
from tests.app_de_teste import modulo


def test_migra_esquema_anterior_sem_apagar_redacoes():
    with conectar() as conexao:
        esquema = sql.Identifier(f"migracao_{uuid4().hex}")
        conexao.execute(sql.SQL("CREATE SCHEMA {}").format(esquema))
        conexao.execute(sql.SQL("SET LOCAL search_path TO {}").format(esquema))
        conexao.execute("""
            CREATE TABLE usuarios(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha TEXT, tema TEXT, google_id TEXT UNIQUE
            );
            CREATE TABLE redacoes(
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                tema TEXT NOT NULL, ano INTEGER NOT NULL, texto TEXT NOT NULL,
                notas JSONB, nota INTEGER, criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE estudos (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                inicio TIMESTAMP NOT NULL, fim TIMESTAMP, duracao INTEGER DEFAULT 0, ativa INTEGER DEFAULT 1
            );
            INSERT INTO usuarios (nome, email) VALUES ('Legado', 'legado@example.invalid');
            INSERT INTO redacoes (usuario_id, tema, ano, texto, nota)
            VALUES (1, 'Tema legado', 2025, 'Texto preservado', 640);
        """)
        conexao.execute("CREATE TABLE tentativas_provas_objetivas (usuario_id INTEGER)")
        with pytest.raises(errors.UndefinedColumn), conexao.transaction():
            verificar_esquema_web(conexao)
        conexao.execute("DROP TABLE tentativas_provas_objetivas")
        aplicar_migracoes(conexao)
        aplicar_migracoes(conexao)
        assert verificar_esquema_web(conexao)
        assert conexao.execute("SELECT texto, nota, instituicao FROM redacoes").fetchone() == {
            "texto": "Texto preservado", "nota": 640, "instituicao": "ENEM",
        }
        assert conexao.execute("SELECT to_regclass('tentativas_provas_objetivas') AS tabela").fetchone()["tabela"]
        versoes = conexao.execute("SELECT versao FROM studyhub_migracoes ORDER BY versao").fetchall()
        assert {1, 2, 3, 4} <= {linha["versao"] for linha in versoes}
        registro = conexao.execute("""
            INSERT INTO estudos (usuario_id, inicio, inicio_segmento, ultima_atividade)
            VALUES (1, LOCALTIMESTAMP, LOCALTIMESTAMP, LOCALTIMESTAMP)
            RETURNING inicio_segmento, ultima_atividade
        """).fetchone()
        assert registro["inicio_segmento"] is not None
        assert registro["inicio_segmento"] == registro["ultima_atividade"]
        conexao.rollback()


def test_limpeza_apaga_atividades_e_preserva_conquistas(dados_discursivos, monkeypatch):
    app = modulo.app
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    usuario, outro = dados_discursivos["usuarios"]
    try:
        with conectar() as conexao:
            conexao.execute("""
                INSERT INTO leituras_idiomas (usuario_id, texto_id, palavras, acertos)
                VALUES (%s, 'texto', 120, 8), (%s, 'texto', 120, 8)
            """, (usuario, outro))
            conexao.execute("""
                INSERT INTO tarefas (usuario_id, descricao, concluida)
                VALUES (%s, 'Pendente', 0), (%s, 'Concluída', 1), (%s, 'Pendente de outro', 0)
            """, (usuario, usuario, outro))
            conexao.execute("""
                INSERT INTO experiencia_atividades (usuario_id, origem, referencia, exp_decimos)
                VALUES (%s, 'idiomas', 'texto', 1000)
            """, (usuario,))
        with app.test_client() as cliente:
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = usuario
            assert cliente.post("/nivel/progresso").json["celebrar"] is True
            assert cliente.post("/nivel/moldura", json={"nivel": 1}).status_code == 200
            for _ in range(2):
                assert cliente.post("/configuracoes/dados/limpar").status_code == 302
            progresso = cliente.post("/nivel/progresso").json
            assert progresso["nivel"] == 1
            assert progresso["moldura_equipada"] == 1
            assert progresso["celebrar"] is False

        with conectar() as conexao:
            for tabela in (sql.Identifier("leituras_idiomas"), sql.Identifier("tarefas")):
                assert conexao.execute(
                    sql.SQL("SELECT usuario_id FROM {} WHERE usuario_id = ANY(%s)").format(tabela),
                    ([usuario, outro],),
                ).fetchall() == [{"usuario_id": outro}]
    finally:
        with conectar() as conexao:
            conexao.execute("DELETE FROM tarefas WHERE usuario_id = ANY(%s)", ([usuario, outro],))



def test_exclusao_conta_google_exige_identidade_vinculada(dados_discursivos, monkeypatch):
    app = modulo.app
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    usuario, outro = dados_discursivos["usuarios"]
    google_id = uuid4().hex
    with conectar() as conexao:
        conexao.execute("UPDATE usuarios SET senha = NULL, google_id = %s WHERE id = %s", (google_id, usuario))

    def iniciar(redirect_uri, *, state, prompt):
        assert redirect_uri.endswith("/login/google/callback")
        assert prompt == "select_account"
        return modulo.redirect(f"/login/google/callback?state={state}")

    monkeypatch.setattr(autenticacao_controller.google, "authorize_redirect", iniciar)
    info = {"sub": "outra-identidade", "email": "teste@example.invalid", "email_verified": True}
    monkeypatch.setattr(autenticacao_controller.google, "authorize_access_token", lambda: {"userinfo": info})

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        caminho = "/configuracoes/excluir-conta/google"
        callback = cliente.post(caminho).location
        assert cliente.get(callback).location.endswith("/configuracoes")
        callback = cliente.post(caminho).location
        info["sub"] = google_id
        assert cliente.get(callback).location.endswith("/login")
    with conectar() as conexao:
        assert conexao.execute("SELECT id FROM usuarios WHERE id = ANY(%s)", ([usuario, outro],)).fetchall() == [
            {"id": outro}
        ]


def test_health_sinaliza_esquema_invalido(monkeypatch):
    with modulo.app.test_client() as cliente:
        assert cliente.get("/health").status_code == 200

        def coluna_ausente(_):
            raise errors.UndefinedColumn("coluna correcao_falhou não existe")

        monkeypatch.setattr(modulo, "verificar_esquema_web", coluna_ausente)
        resposta = cliente.get("/health")
        assert resposta.status_code == 503
        assert b"correcao_falhou" not in resposta.data


def test_inicializacao_local_nao_migra_banco_remoto(monkeypatch):
    from database import criar_banco

    chamadas = []
    monkeypatch.delenv("PGHOSTADDR", raising=False)
    monkeypatch.setattr(criar_banco, "aplicar_migracoes", lambda conexao: chamadas.append(True))
    criar_banco.migrar_banco_local()
    assert chamadas == [True]

    monkeypatch.setenv("DATABASE_URL", "postgresql://remoto.example/studyhub_test")
    criar_banco.migrar_banco_local()
    assert chamadas == [True]
