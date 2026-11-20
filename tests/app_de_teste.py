import os
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "studyhub-test")

# O conftest verifica o nome do banco antes de aplicar o esquema.
with patch("database.criar_banco.criar_tabelas"):
    import app as modulo

app = modulo.app
