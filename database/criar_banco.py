"""Migrações explícitas do StudyHub. Execute com python -m database.criar_banco."""

import os
import re

from psycopg.conninfo import conninfo_to_dict
from pathlib import Path

from database.conexao import conectar


def _migracao_inicial(cursor):
    # =========================
    # USUÁRIOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT,
            tema TEXT DEFAULT 'sistema',
            google_id TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras_idiomas (
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            texto_id TEXT NOT NULL,
            palavras INTEGER NOT NULL CHECK (palavras > 0),
            acertos INTEGER NOT NULL CHECK (acertos BETWEEN 0 AND 10),
            concluido_em DATE NOT NULL DEFAULT ((CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::date),
            PRIMARY KEY (usuario_id, texto_id)
        )
    """)

    # =========================
    # REDAÇÕES
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redacoes (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tema TEXT NOT NULL,
            ano INTEGER NOT NULL,
            texto TEXT NOT NULL CHECK (char_length(texto) BETWEEN 1 AND 6000),
            notas JSONB,
            nota INTEGER CHECK (nota BETWEEN 0 AND 1000),
            criado_em TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')
        )
    """)
    cursor.execute("""
        ALTER TABLE redacoes
            ADD COLUMN IF NOT EXISTS instituicao TEXT NOT NULL DEFAULT 'ENEM',
            ADD COLUMN IF NOT EXISTS titulo TEXT NOT NULL DEFAULT '',
            ADD COLUMN IF NOT EXISTS tempo_segundos INTEGER CHECK (tempo_segundos >= 0)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_redacoes_usuario
        ON redacoes (usuario_id, criado_em DESC, id DESC)
    """)

    # =========================
    # RASCUNHOS DE REDAÇÕES SURPRESA
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redacoes_surpresa (
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            instituicao TEXT NOT NULL CHECK (instituicao IN ('ENEM', 'ITA')),
            rodada BIGINT NOT NULL DEFAULT 0,
            segundos DOUBLE PRECISION NOT NULL DEFAULT 0,
            ativo_desde DOUBLE PRECISION,
            texto TEXT NOT NULL DEFAULT '',
            titulo TEXT NOT NULL DEFAULT '',
            chave TEXT,
            revisao INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (usuario_id, instituicao)
        )
    """)

    # =========================
    # CONFIGURAÇÕES DO USUÁRIO
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_usuario(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL UNIQUE,

            tema TEXT DEFAULT 'sistema',

            meta_estudo INTEGER DEFAULT 60
                CHECK (meta_estudo >= 1),

            meta_questoes INTEGER DEFAULT 20
                CHECK (meta_questoes >= 1),

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)
            ON DELETE CASCADE

        )
    """)

    # =========================
    # TAREFAS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefas(
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            descricao TEXT NOT NULL,
            concluida INTEGER DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            data_conclusao TEXT,
            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)
        )
    """)

    # =========================
    # ESTUDOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudos(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            inicio TIMESTAMP NOT NULL,

            fim TIMESTAMP,

            duracao INTEGER DEFAULT 0,

            ativa INTEGER DEFAULT 1,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)

        )
    """)

    # =========================
    # ANOTAÇÕES
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anotacoes(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            data TEXT NOT NULL,

            texto TEXT NOT NULL,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id),

            UNIQUE(usuario_id, data)

        )
    """)

    # =========================
    # RESULTADOS DAS PROVAS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados_provas(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            prova_id INTEGER NOT NULL,

            acertos INTEGER NOT NULL,

            erros INTEGER NOT NULL,

            tempo_gasto TEXT,

            nao_respondidas INTEGER NOT NULL,

            total INTEGER NOT NULL,

            porcentagem REAL NOT NULL,

            data_realizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)

        )
    """)

    # =========================
    # RESPOSTAS DAS PROVAS
    # =========================

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS respostas_provas(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            prova_id INTEGER NOT NULL,

            resultado_id INTEGER,

            questao_numero INTEGER NOT NULL,

            resposta INTEGER,

            correta INTEGER NOT NULL,

            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id),

            FOREIGN KEY(resultado_id)
            REFERENCES resultados_provas(id)
            ON DELETE CASCADE

        )

    """)

    # =========================
    # RESPOSTAS DAS QUESTÕES
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas_questoes(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            questao_numero INTEGER NOT NULL,

            resposta TEXT NOT NULL,

            correta INTEGER NOT NULL,

            tentativa INTEGER NOT NULL DEFAULT 1,

            intervalo_revisao INTEGER NOT NULL DEFAULT 3,

            data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            proxima_tentativa TIMESTAMP,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)
            ON DELETE CASCADE

        )
    """)

    # =========================
    # RESULTADOS DAS QUESTÕES
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados_questoes(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            questao_numero INTEGER NOT NULL,

            resposta_usuario TEXT NOT NULL,

            resposta_correta TEXT NOT NULL,

            correta INTEGER NOT NULL,

            data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            proxima_tentativa TIMESTAMP NOT NULL,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)
            ON DELETE CASCADE

        )
    """)

    # =========================
    # TENTATIVAS DE LOGIN
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tentativas_login(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            chave TEXT NOT NULL UNIQUE,

            tentativas INTEGER NOT NULL DEFAULT 0,

            primeira_tentativa TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

            bloqueado_ate TIMESTAMPTZ

        )
    """)

    # =========================
    # TENTATIVAS DE PROVAS DISCURSIVAS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tentativas_provas_discursivas(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            usuario_id INTEGER NOT NULL,

            instituicao TEXT NOT NULL,

            ano INTEGER NOT NULL,

            fase TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'em_andamento'
                CHECK (
                    status IN (
                        'em_andamento',
                        'finalizada',
                        'corrigida'
                    )
                ),

            nota_total REAL,

            nota_maxima REAL,

            data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            data_finalizacao TIMESTAMP,

            data_correcao TIMESTAMP,

            FOREIGN KEY(usuario_id)
                REFERENCES usuarios(id)
                ON DELETE CASCADE,

            CHECK (
                nota_total IS NULL
                OR nota_total >= 0
            ),

            CHECK (
                nota_maxima IS NULL
                OR nota_maxima >= 0
            ),

            CHECK (
                nota_total IS NULL
                OR nota_maxima IS NULL
                OR nota_total <= nota_maxima
            )

        )
    """)

    cursor.execute("""
        ALTER TABLE tentativas_provas_discursivas
        ADD COLUMN IF NOT EXISTS disciplina TEXT
    """)

    cursor.execute("""
        ALTER TABLE tentativas_provas_discursivas
        ADD COLUMN IF NOT EXISTS resultado_correcao JSONB
    """)

    cursor.execute("""
        ALTER TABLE tentativas_provas_discursivas
        ADD COLUMN IF NOT EXISTS tentativas_correcao INTEGER NOT NULL DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE tentativas_provas_discursivas
        ADD COLUMN IF NOT EXISTS proxima_tentativa_correcao TIMESTAMPTZ
    """)

    cursor.execute("""
        ALTER TABLE tentativas_provas_discursivas
        ADD COLUMN IF NOT EXISTS correcao_reivindicada_ate TIMESTAMPTZ
    """)

    # =========================
    # RESPOSTAS DAS PROVAS DISCURSIVAS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas_discursivas(

            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

            tentativa_id INTEGER NOT NULL,

            questao_numero INTEGER NOT NULL,

            item_letra TEXT,

            resposta TEXT NOT NULL DEFAULT '',

            data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            data_atualizacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(tentativa_id)
                REFERENCES tentativas_provas_discursivas(id)
                ON DELETE CASCADE,

            UNIQUE(tentativa_id, questao_numero, item_letra)

        )
    """)


def aplicar_migracoes(conexao):
    """Aplica as versões em uma transação, preservando esquemas legados."""
    pasta = Path(__file__).with_name("migrations")
    arquivos = []
    for arquivo in sorted(pasta.glob("*.sql")):
        versao = re.fullmatch(r"(\d{4})_.+\.sql", arquivo.name)
        if not versao:
            raise ValueError(f"Nome inválido para migração: {arquivo.name}")
        arquivos.append((int(versao[1]), arquivo))
    if [versao for versao, _ in arquivos] != list(range(2, len(arquivos) + 2)):
        raise ValueError("As versões das migrações precisam ser consecutivas.")

    with conexao.transaction(), conexao.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(52731, hashtext(current_schema()))")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS studyhub_migracoes (
                versao INTEGER PRIMARY KEY,
                aplicada_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SELECT versao FROM studyhub_migracoes")
        aplicadas = {linha["versao"] for linha in cursor.fetchall()}
        if 1 not in aplicadas:
            _migracao_inicial(cursor)
            cursor.execute("INSERT INTO studyhub_migracoes (versao) VALUES (1)")
        for versao, arquivo in arquivos:
            if versao not in aplicadas:
                cursor.execute(arquivo.read_text(encoding="utf-8"))
                cursor.execute("INSERT INTO studyhub_migracoes (versao) VALUES (%s)", (versao,))


def verificar_esquema_web(conexao):
    """Confere o esquema sem gravar dados nem executar migrações."""
    conexao.execute("""
        SELECT r.correcao_falhou, r.correcao_tentativas, r.correcao_reivindicada_ate,
               r.correcao_tentar_apos, r.chave_envio, t.usuario_id
        FROM redacoes AS r
        CROSS JOIN tentativas_provas_objetivas AS t
        CROSS JOIN estudos AS e
        WHERE e.inicio_segmento IS NOT DISTINCT FROM e.ultima_atividade
        LIMIT 0
    """)
    encontradas = conexao.execute("SELECT versao FROM studyhub_migracoes").fetchall()
    pasta = Path(__file__).with_name("migrations")
    esperadas = {1, *(int(arquivo.name[:4]) for arquivo in pasta.glob("*.sql"))}
    return esperadas <= {linha["versao"] for linha in encontradas}


def criar_tabelas():
    with conectar() as conexao:
        aplicar_migracoes(conexao)


def migrar_banco_local():
    dados = conninfo_to_dict(os.environ["DATABASE_URL"])
    locais = {"localhost", "127.0.0.1", "::1"}
    if (
        dados.get("dbname") not in {"studyhub", "studyhub_test"}
        or dados.get("host") not in locais
        or dados.get("hostaddr", "") not in locais | {""}
        or "service" in dados
        or os.getenv("PGHOSTADDR")
    ):
        return
    with conectar() as conexao:
        banco = conexao.execute("SELECT current_database() AS nome").fetchone()["nome"]
        if banco == dados["dbname"]:
            aplicar_migracoes(conexao)


if __name__ == "__main__":
    criar_tabelas()
