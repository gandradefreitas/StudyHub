import os
os.environ.setdefault("SECRET_KEY", "studyhub-test")

# Importar o aplicativo não acessa nem migra o banco.
import app as modulo

app = modulo.app
