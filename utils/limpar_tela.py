import os

def limpar_tela():
    if os.name == "nt":      # Windows
        os.system("cls")
    else:                    # Linux e macOS
        os.system("clear")