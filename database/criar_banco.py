from studyhub.database.conexao import conectar

def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        PRAGMA table_info(usuarios)
    """)

    colunas_usuarios = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    if "tema" not in colunas_usuarios:
        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN tema TEXT DEFAULT 'sistema'
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_usuario(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL UNIQUE,

            tema TEXT DEFAULT 'sistema',

            meta_estudo INTEGER DEFAULT 60,

            meta_questoes INTEGER DEFAULT 20,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)
            ON DELETE CASCADE

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            concluida INTEGER DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            data_conclusao TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        PRAGMA table_info(tarefas)
    """)

    colunas_tarefas = [
        coluna[1]
        for coluna in cursor.fetchall()
    ]

    if "data_conclusao" not in colunas_tarefas:
        cursor.execute("""
            ALTER TABLE tarefas
            ADD COLUMN data_conclusao TEXT
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estudos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL,

            inicio DATETIME NOT NULL,

            fim DATETIME,

            duracao INTEGER DEFAULT 0,
            
            ativa INTEGER DEFAULT 1,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anotacoes(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL,

            data TEXT NOT NULL,

            texto TEXT NOT NULL,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id),

            UNIQUE(usuario_id, data)

        )
    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS resultados_provas (

        id INTEGER PRIMARY KEY AUTOINCREMENT,
    
        usuario_id INTEGER NOT NULL,
    
        prova_id INTEGER NOT NULL,
    
        acertos INTEGER NOT NULL,
    
        erros INTEGER NOT NULL,
        
        tempo_gasto TEXT,
    
        nao_respondidas INTEGER NOT NULL,
    
        total INTEGER NOT NULL,
    
        porcentagem REAL NOT NULL,
    
        data_realizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    
    )

    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas_provas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            usuario_id INTEGER NOT NULL,

            prova_id INTEGER NOT NULL,

            questao_numero INTEGER NOT NULL,

            resposta INTEGER,

            correta INTEGER NOT NULL,

            data DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(usuario_id)
            REFERENCES usuarios(id)

        )
    """)


    cursor.execute("""

    CREATE TABLE IF NOT EXISTS respostas_questoes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario_id INTEGER NOT NULL,

        questao_numero INTEGER NOT NULL,

        resposta TEXT NOT NULL,

        correta INTEGER NOT NULL,

        data_resposta DATETIME DEFAULT CURRENT_TIMESTAMP,

        proxima_tentativa DATETIME,

        FOREIGN KEY(usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE

    )

    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS resultados_questoes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario_id INTEGER NOT NULL,

        questao_numero INTEGER NOT NULL,

        resposta_usuario TEXT NOT NULL,

        resposta_correta TEXT NOT NULL,

        correta INTEGER NOT NULL,

        data_resposta DATETIME DEFAULT CURRENT_TIMESTAMP,

        proxima_tentativa DATETIME NOT NULL,

        FOREIGN KEY(usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE

    )

    """)

    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_tabelas()