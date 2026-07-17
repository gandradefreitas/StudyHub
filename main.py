from studyhub.database.criar_banco import criar_tabelas
from studyhub.navigation.menu_inicial import menu_inicial
from studyhub.navigation.menu_usuario import menu_usuario

def main():
    criar_tabelas()

    while True:
        usuario = menu_inicial()

        if usuario:
            menu_usuario(usuario)


if __name__ == "__main__":
    main()