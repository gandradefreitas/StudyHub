from database.conexao import conectar


def criar_tabelas():

    conexao = conectar()
    cursor = conexao.cursor()

    # =========================
    # USUÁRIOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tema TEXT DEFAULT 'sistema'
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

            meta_estudo INTEGER DEFAULT 60,

            meta_questoes INTEGER DEFAULT 20,

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

            inicio TIMESTAMP WITH TIME ZONE NOT NULL,

            fim TIMESTAMP WITH TIME ZONE,

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

            questao_numero INTEGER NOT NULL,

            resposta INTEGER,

            correta INTEGER NOT NULL,

            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)

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

    conexao.commit()

    cursor.close()
    conexao.close()


if __name__ == "__main__":
    criar_tabelas()

