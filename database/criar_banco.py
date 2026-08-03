from database.conexao import conectar

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
        CREATE TABLE IF NOT EXISTS tarefas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            concluida INTEGER DEFAULT 0,
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
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

    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_tabelas()