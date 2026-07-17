# StudyHub

Sistema de gerenciamento de tarefas desenvolvido em Python utilizando arquitetura em camadas, SQLite e criptografia de senhas.

## Funcionalidades

- Cadastro de usuários
- Login com autenticação
- Criptografia de senhas (bcrypt)
- Validação de nome, e-mail e senha
- Gerenciamento de tarefas
    - Adicionar
    - Editar
    - Concluir/Reabrir
    - Excluir
- Persistência de dados com SQLite
- Logout

## Tecnologias

- Python 3
- SQLite
- Rich
- bcrypt

## Estrutura do projeto

```
studyhub/
│
├── controllers/
├── database/
├── interface/
├── models/
├── navigation/
├── security/
├── services/
├── utils/
│
├── config.py
├── main.py
└── README.md
```

## Como executar

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/studyhub.git
```

Entre na pasta:

```bash
cd studyhub
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python main.py
```

## Arquitetura

O projeto segue uma arquitetura em camadas:

- Controllers
- Services
- Repository (SQLite)
- Interface
- Utils

Essa separação facilita manutenção, reutilização e futuras expansões.

## Próximos objetivos

- Interface Web com Flask
- API REST
- Interface gráfica
- Testes automatizados