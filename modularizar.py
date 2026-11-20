"""
Divide verificador_matematico.py em um pacote de módulos.

Uso (na pasta onde está verificador_matematico.py):

    python modularizar.py

O que o script faz:

  1. Lê o arquivo atual e separa cada definição de nível superior.
  2. Distribui as definições pelos módulos da pasta motor_matematico/.
  3. Gera automaticamente as importações de cada módulo.
  4. Recria verificador_matematico.py como fachada: reexporta toda a
     API e mantém o bloco de testes (__main__) exatamente como estava.
  5. Verifica que não há importações circulares e que todos os
     módulos importam sem erro.

Nada é apagado: o arquivo original é guardado em
verificador_matematico.original.bak. Para desfazer, apague a pasta
motor_matematico/ e copie o .bak de volta para verificador_matematico.py.

O script não altera a lógica matemática. A única alteração de código
é no módulo tempo.py: o processo filho passa a localizar a função
pelo módulo (importlib) em vez de procurá-la no próprio arquivo.
"""

import ast
import importlib
import shutil
import sys
import traceback
from pathlib import Path

ARQUIVO = Path("verificador_matematico.py")
BACKUP = Path("verificador_matematico.original.bak")
NOME_PACOTE = "motor_matematico"
PACOTE = Path(NOME_PACOTE)

# ----------------------------------------------------------------
# Distribuição das definições pelos módulos
# ----------------------------------------------------------------

MODULOS = {
    "normalizacao": [
        "_SUPERESCRITOS", "_SUBSTITUICOES", "_REGEX_TOKEN",
        "normalizar_entrada", "_analisar_sintaxe",
    ],
    "interpretador": [
        "_LIMITE_BITS", "_validar_tamanho_numerico",
        "interpretar_expressao",
    ],
    "dominio": [
        "obter_variaveis_equacao", "identificar_variaveis",
        "inspecionar_variaveis_denominadores",
        "identificar_denominadores", "obter_condicoes_denominadores",
        "identificar_restricoes", "identificar_radicandos",
        "obter_condicoes_raizes", "identificar_restricoes_raizes",
        "combinar_restricoes_raizes", "obter_dominio_raizes",
        "obter_dominio", "obter_condicoes_dominio_expressao",
        "verificar_condicoes_dominio", "_normalizar_condicoes_dominio",
        "_existe_ponto_separador", "_comparar_conjuntos_reais",
        "comparar_dominios_expressoes",
    ],
    "equacoes": [
        "interpretar_equacao", "obter_condicoes_dominio",
    ],
    "equivalencia": [
        "_comparar_simbolicamente", "verificar_operacao",
        "analisar_equivalencia_expressoes", "verificar_equivalencia",
        "verificar_equivalencia_equacoes",
        "verificar_ponto_contraexemplo", "comparar_condicoes_dominio",
        "_existe_ponto_separador_equacoes",
        "verificar_equivalencia_multivariavel",
        "verificar_coeficientes_nulos",
        "verificar_proporcionalidade_vetores",
        "obter_condicoes_anulacao", "verificar_condicoes_anulacao",
        "analisar_equivalencia_vetores",
    ],
    "sistemas": [
        "construir_matriz_sistema", "classificar_sistema",
        "analisar_postos_sistema", "analisar_postos_possiveis",
        "obter_condicoes_igualdade_espacos_linhas",
        "analisar_equivalencia_sistemas_parametricos",
        "classificar_sistemas_possiveis",
        "verificar_equivalencia_sistemas_numericos",
        "verificar_equivalencia_sistemas_teste",
        "identificar_parametros_sistema",
        "verificar_equivalencia_com_parametros",
        "obter_condicoes_degeneracao_sistema",
        "substituir_parametros_sistema", "obter_determinantes_menores",
        "simplificar_condicao_parametrica",
        "normalizar_condicao_algebrica",
    ],
    "contrato": [
        "STATUS_CORRETO", "STATUS_INCORRETO", "STATUS_CONDICIONAL",
        "STATUS_INDETERMINADO", "STATUS_INVALIDO", "_ERROS_DE_ENTRADA",
        "montar_resultado", "_resultado_invalido",
        "_formatar_condicao", "_formatar_condicoes",
    ],
    "tempo": [
        "_configuracao_de_tempo", "_EM_PROCESSO_ISOLADO",
        "configurar_limite_de_tempo", "_limite_efetivo",
        "_resultado_erro_interno", "_resultado_tempo_excedido",
        "_executar_protegido", "_LIMITE_DE_PARTIDA", "_receber",
        "_executar_no_filho", "_executar_com_limite",
        "_interface_protegida",
    ],
    "avaliacao": [
        "avaliar_equivalencia_expressoes",
        "avaliar_equivalencia_equacoes",
        "avaliar_equivalencia_sistemas", "analisar_dominio_expressao",
    ],
    "resolucao": [
        "_conjunto_resolvido", "_ordenar_reais",
        "obter_conjunto_solucao_equacao", "resolver_equacao",
        "verificar_solucao_equacao",
    ],
    "transformacoes": [
        "_eh_equacao", "_listar_conjunto", "_procurar_contraexemplo",
        "_contraexemplo_expressoes", "_verificar_transformacao_expressao",
        "_verificar_transformacao_equacao", "verificar_transformacao",
    ],
    "diagnostico": [
        "_termo_em_texto", "_diagnostico", "_diagnostico_generico",
        "_diagnosticar_expressoes", "_diagnosticar_equacoes",
        "_diagnosticar", "diagnosticar_transformacao",
    ],
    "procedimentos": [
        "_MAX_ETAPAS", "_erro_de_leitura", "analisar_procedimento",
    ],
    "numerico": [
        "_PRECISAO_AVALIACAO", "_PRECISAO_DECIMAL",
        "_MODOS_DE_ARREDONDAMENTO", "_REGEX_DECIMAL",
        "_CONDICAO_DE_PRECISAO", "_como_texto", "_literal_decimal",
        "_valor_numerico", "_validar_regra_de_precisao",
        "_iguais_exatamente", "_decimal_do_valor", "_casas",
        "_quantizar", "_modos_compativeis",
        "comparar_resultado_numerico",
    ],
    "auxiliares_de_teste": [
        "_auxiliar_lento_para_teste", "_auxiliar_com_erro_para_teste",
        "_auxiliar_que_derruba_o_processo",
    ],
}

DESCRICOES = {
    "normalizacao": "Normalização da notação do estudante (², ^, vírgula "
                    "decimal, multiplicação implícita).",
    "interpretador": "Interpretador seguro de expressões matemáticas.",
    "dominio": "Variáveis, restrições e domínio de validade.",
    "equacoes": "Interpretação de equações.",
    "equivalencia": "Equivalência de expressões, equações e vetores de "
                    "coeficientes.",
    "sistemas": "Sistemas lineares: matrizes, postos, classificação e "
                "equivalência.",
    "contrato": "Formato único de retorno das funções públicas.",
    "tempo": "Controle de tempo: execução da interface pública em "
             "processo isolado.",
    "avaliacao": "Interface pública: equivalência de expressões, "
                 "equações, sistemas e domínio.",
    "resolucao": "Resolução de equações reais de uma variável.",
    "transformacoes": "Verificação de transformações algébricas.",
    "diagnostico": "Diagnóstico de erros em transformações.",
    "procedimentos": "Análise de procedimentos com várias etapas.",
    "numerico": "Verificação numérica (exata, aproximada, com regra de "
                "precisão).",
    "auxiliares_de_teste": "Auxiliares dos testes de controle de tempo. "
                           "Precisam estar em um módulo importável pelo "
                           "processo filho.",
    "pendentes": "Definições que o mapa do script não conhecia. Mova-as "
                 "para o módulo adequado.",
}

# nome -> (módulo, item, apelido)
IMPORTS_EXTERNOS = {
    "ast": ("ast", None, None),
    "functools": ("functools", None, None),
    "importlib": ("importlib", None, None),
    "itertools": ("itertools", None, None),
    "math": ("math", None, None),
    "multiprocessing": ("multiprocessing", None, None),
    "re": ("re", None, None),
    "sys": ("sys", None, None),
    "sp": ("sympy", None, "sp"),
    "Decimal": ("decimal", "Decimal", None),
    "ROUND_DOWN": ("decimal", "ROUND_DOWN", None),
    "ROUND_HALF_UP": ("decimal", "ROUND_HALF_UP", None),
    "localcontext": ("decimal", "localcontext", None),
    "Fraction": ("fractions", "Fraction", None),
}

# Importações que o código usa mas a análise de nomes não enxerga
# (porque são introduzidas pelos remendos abaixo).
EXTRAS_DE_IMPORT = {"tempo": ["importlib"]}

# O processo filho passa a localizar a função pelo módulo.
REMENDOS = {
    "tempo": [
        (
            "def _executar_no_filho(nome, args, kwargs, conexao):",
            "def _executar_no_filho(modulo, nome, args, kwargs, conexao):",
        ),
        (
            "funcao = globals()[nome].__wrapped__",
            "funcao = getattr(importlib.import_module(modulo), nome)"
            ".__wrapped__",
        ),
        (
            "args=(funcao.__name__, args, kwargs, envia),",
            "args=(funcao.__module__, funcao.__name__, args, kwargs, "
            "envia),",
        ),
    ],
}


class ErroDeModularizacao(Exception):
    pass


# ----------------------------------------------------------------
# Leitura do arquivo
# ----------------------------------------------------------------

def nomes_definidos(no):
    if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [no.name]

    if isinstance(no, ast.Assign):
        return [a.id for a in no.targets if isinstance(a, ast.Name)]

    if isinstance(no, ast.AnnAssign) and isinstance(no.target, ast.Name):
        return [no.target.id]

    return []


def e_bloco_main(no):
    return (
        isinstance(no, ast.If)
        and isinstance(no.test, ast.Compare)
        and isinstance(no.test.left, ast.Name)
        and no.test.left.id == "__name__"
    )


def nomes_usados(no):
    """
    Nomes globais lidos por um nó de nível superior, descontando
    os que são locais da função (parâmetros e atribuições).
    """

    carregados = set()
    locais = set()

    for sub in ast.walk(no):
        if isinstance(sub, ast.Name):
            if isinstance(sub.ctx, ast.Load):
                carregados.add(sub.id)
            else:
                locais.add(sub.id)

        elif isinstance(sub, ast.arg):
            locais.add(sub.arg)

        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if sub is not no:
                locais.add(sub.name)

        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            locais.add(sub.name)

        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for alias in sub.names:
                locais.add((alias.asname or alias.name).split(".")[0])

    if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return carregados - locais

    return carregados


def ler_definicoes(codigo):
    linhas = codigo.splitlines()
    arvore = ast.parse(codigo)

    definicoes = []
    bloco_main = None
    fim_anterior = 0

    for no in arvore.body:
        inicio = no.lineno

        decoradores = getattr(no, "decorator_list", [])

        if decoradores:
            inicio = min([inicio] + [d.lineno for d in decoradores])

        fim = no.end_lineno

        e_import = isinstance(no, (ast.Import, ast.ImportFrom))
        e_docstring = (
            isinstance(no, ast.Expr)
            and isinstance(no.value, ast.Constant)
            and isinstance(no.value.value, str)
        )

        if e_import or e_docstring:
            fim_anterior = fim
            continue

        comentarios = [
            linha
            for linha in linhas[fim_anterior:inicio - 1]
            if linha.strip().startswith("#")
        ]

        texto = "\n".join(comentarios + linhas[inicio - 1:fim]).rstrip()

        fim_anterior = fim

        if e_bloco_main(no):
            bloco_main = (texto, no)
            continue

        nomes = nomes_definidos(no)

        if not nomes:
            raise ErroDeModularizacao(
                f"Instrução de nível superior não suportada na linha "
                f"{no.lineno}: {type(no).__name__}."
            )

        definicoes.append({
            "nome": nomes[0],
            "nomes": nomes,
            "texto": texto,
            "usados": nomes_usados(no),
        })

    return definicoes, bloco_main


# ----------------------------------------------------------------
# Geração
# ----------------------------------------------------------------

def linhas_de_importacao_externa(externos):
    simples = []
    de = {}
    terceiros = []

    for nome in sorted(externos):
        modulo, item, apelido = IMPORTS_EXTERNOS[nome]

        if modulo == "sympy":
            terceiros.append(f"import sympy as {apelido}")
        elif item is None:
            simples.append(f"import {modulo}")
        else:
            de.setdefault(modulo, []).append(item)

    biblioteca_padrao = simples + [
        f"from {modulo} import {', '.join(sorted(itens))}"
        for modulo, itens in sorted(de.items())
    ]

    blocos = []

    if biblioteca_padrao:
        blocos.append("\n".join(biblioteca_padrao))

    if terceiros:
        blocos.append("\n".join(terceiros))

    return blocos


def linha_de_importacao_local(prefixo, modulo, nomes):
    nomes = sorted(nomes)

    if len(nomes) == 1:
        return f"from {prefixo}{modulo} import {nomes[0]}"

    corpo = "".join(f"    {nome},\n" for nome in nomes)

    return f"from {prefixo}{modulo} import (\n{corpo})"


def classificar_usos(usados, proprios, modulo_de):
    externos = set()
    locais = {}

    for nome in usados:
        if nome in proprios:
            continue

        if nome in modulo_de:
            locais.setdefault(modulo_de[nome], set()).add(nome)

        elif nome in IMPORTS_EXTERNOS:
            externos.add(nome)

    return externos, locais


def detectar_ciclo(dependencias):
    """Retorna uma lista de módulos que forma um ciclo, ou None."""

    estado = {}
    caminho = []

    def visitar(modulo):
        estado[modulo] = "visitando"
        caminho.append(modulo)

        for destino in sorted(dependencias.get(modulo, ())):
            if estado.get(destino) == "visitando":
                return caminho[caminho.index(destino):] + [destino]

            if destino not in estado:
                ciclo = visitar(destino)

                if ciclo:
                    return ciclo

        caminho.pop()
        estado[modulo] = "visitado"

        return None

    for modulo in sorted(dependencias):
        if modulo not in estado:
            ciclo = visitar(modulo)

            if ciclo:
                return ciclo

    return None


def ordem_topologica(dependencias):
    ordem = []
    visitados = set()

    def visitar(modulo):
        if modulo in visitados:
            return

        visitados.add(modulo)

        for destino in sorted(dependencias.get(modulo, ())):
            visitar(destino)

        ordem.append(modulo)

    for modulo in sorted(dependencias):
        visitar(modulo)

    return ordem


def aplicar_remendos(modulo, texto):
    for antigo, novo in REMENDOS.get(modulo, []):
        ocorrencias = texto.count(antigo)

        if ocorrencias != 1:
            raise ErroDeModularizacao(
                f"O trecho esperado no módulo '{modulo}' apareceu "
                f"{ocorrencias} vez(es) em vez de 1:\n    {antigo}"
            )

        texto = texto.replace(antigo, novo)

    return texto


def planejar(definicoes):
    nomes_vistos = {}

    for definicao in definicoes:
        for nome in definicao["nomes"]:
            nomes_vistos[nome] = nomes_vistos.get(nome, 0) + 1

    repetidos = sorted(n for n, qtd in nomes_vistos.items() if qtd > 1)

    if repetidos:
        raise ErroDeModularizacao(
            "Há nomes definidos mais de uma vez no arquivo (apenas a "
            "última definição vale em Python). Resolva antes de "
            "modularizar:\n    " + "\n    ".join(repetidos)
        )

    modulo_de = {}

    for modulo, nomes in MODULOS.items():
        for nome in nomes:
            if nome in modulo_de:
                raise ErroDeModularizacao(
                    f"O nome '{nome}' está no mapa de dois módulos."
                )

            modulo_de[nome] = modulo

    ausentes = sorted(
        nome for nome in modulo_de if nome not in nomes_vistos
    )

    pendentes = []

    for definicao in definicoes:
        for nome in definicao["nomes"]:
            if nome not in modulo_de:
                modulo_de[nome] = "pendentes"
                pendentes.append(nome)

    por_modulo = {}

    for definicao in definicoes:
        modulo = modulo_de[definicao["nome"]]
        por_modulo.setdefault(modulo, []).append(definicao)

    return modulo_de, por_modulo, ausentes, pendentes


def gerar_modulo(modulo, definicoes, modulo_de):
    proprios = {n for d in definicoes for n in d["nomes"]}
    usados = set().union(*(d["usados"] for d in definicoes))

    externos, locais = classificar_usos(usados, proprios, modulo_de)
    externos |= set(EXTRAS_DE_IMPORT.get(modulo, []))

    blocos = [f'"""{DESCRICOES.get(modulo, modulo)}"""']

    blocos += linhas_de_importacao_externa(externos)

    if locais:
        blocos.append("\n".join(
            linha_de_importacao_local(".", origem, nomes)
            for origem, nomes in sorted(locais.items())
        ))

    corpo = "\n\n\n".join(d["texto"] for d in definicoes)
    corpo = aplicar_remendos(modulo, corpo)

    texto = "\n\n".join(blocos) + "\n\n\n" + corpo + "\n"

    return texto, set(locais)


def gerar_fachada(por_modulo, ordem, bloco_main, modulo_de):
    externos = set()

    if bloco_main is not None:
        texto_main, no_main = bloco_main

        externos = {
            nome for nome in nomes_usados(no_main)
            if nome in IMPORTS_EXTERNOS and nome not in modulo_de
        }

    blocos = [
        '"""\n'
        "Motor de verificação matemática do StudyHub.\n\n"
        "Este arquivo é a fachada pública: reexporta a API dos módulos "
        f"da pasta {NOME_PACOTE}/\ne mantém o bloco de testes "
        "(execute este arquivo para rodar a bateria de regressão).\n"
        '"""'
    ]

    blocos += linhas_de_importacao_externa(externos)

    importacoes = []

    for modulo in ordem:
        nomes = [
            n for d in por_modulo.get(modulo, []) for n in d["nomes"]
        ]

        if nomes:
            importacoes.append(
                linha_de_importacao_local(f"{NOME_PACOTE}.", modulo, nomes)
            )

    blocos.append("\n".join(importacoes))

    publicos = sorted(
        n
        for definicoes in por_modulo.values()
        for d in definicoes
        for n in d["nomes"]
        if not n.startswith("_")
    )

    lista = "".join(f'    "{nome}",\n' for nome in publicos)
    blocos.append(f"__all__ = [\n{lista}]")

    if bloco_main is not None:
        blocos.append(bloco_main[0])

    return "\n\n\n".join(blocos) + "\n"


# ----------------------------------------------------------------
# Execução
# ----------------------------------------------------------------

def main():
    if not ARQUIVO.exists():
        raise ErroDeModularizacao(
            f"{ARQUIVO} não encontrado. Rode o script na pasta do arquivo."
        )

    if PACOTE.exists():
        raise ErroDeModularizacao(
            f"A pasta {PACOTE}/ já existe. Para refazer, apague-a e "
            f"restaure o arquivo original a partir de {BACKUP}."
        )

    if BACKUP.exists():
        raise ErroDeModularizacao(
            f"{BACKUP} já existe, o que indica que o script já rodou. "
            f"Restaure o original antes de rodar de novo."
        )

    codigo = ARQUIVO.read_text(encoding="utf-8")

    definicoes, bloco_main = ler_definicoes(codigo)
    modulo_de, por_modulo, ausentes, pendentes = planejar(definicoes)

    modulos_gerados = {}
    dependencias = {}

    for modulo, itens in por_modulo.items():
        texto, deps = gerar_modulo(modulo, itens, modulo_de)

        modulos_gerados[modulo] = texto
        dependencias[modulo] = deps

    ciclo = detectar_ciclo(dependencias)

    if ciclo:
        raise ErroDeModularizacao(
            "Importação circular entre módulos: "
            + " -> ".join(ciclo)
            + "\nNenhum arquivo foi alterado. Ajuste o mapa MODULOS."
        )

    ordem = ordem_topologica(dependencias)

    fachada = gerar_fachada(por_modulo, ordem, bloco_main, modulo_de)

    # Valida a sintaxe de tudo antes de escrever.
    for modulo, texto in modulos_gerados.items():
        compile(texto, f"{modulo}.py", "exec")

    compile(fachada, str(ARQUIVO), "exec")

    # Escrita.
    shutil.copy2(ARQUIVO, BACKUP)
    PACOTE.mkdir()

    (PACOTE / "__init__.py").write_text(
        '"""Núcleo do motor de verificação matemática."""\n',
        encoding="utf-8"
    )

    for modulo, texto in modulos_gerados.items():
        (PACOTE / f"{modulo}.py").write_text(texto, encoding="utf-8")

    ARQUIVO.write_text(fachada, encoding="utf-8")

    # Relatório.
    print("Módulos gerados:")

    for modulo in ordem:
        qtd = len(por_modulo[modulo])
        linhas = modulos_gerados[modulo].count("\n")
        deps = ", ".join(sorted(dependencias[modulo])) or "-"

        print(f"  {modulo:<22} {qtd:>3} definições {linhas:>5} linhas"
              f"   depende de: {deps}")

    if pendentes:
        print("\nATENÇÃO: definições sem módulo no mapa (foram para "
              "pendentes.py):")

        for nome in pendentes:
            print(f"  {nome}")

    if ausentes:
        print("\nAviso: nomes do mapa que não existem neste arquivo:")

        for nome in ausentes:
            print(f"  {nome}")

    # Verificação final: tudo precisa importar.
    sys.path.insert(0, str(Path.cwd()))

    falhas = []

    for modulo in ordem:
        try:
            importlib.import_module(f"{NOME_PACOTE}.{modulo}")
        except Exception:
            falhas.append((modulo, traceback.format_exc()))

    try:
        importlib.import_module(ARQUIVO.stem)
    except Exception:
        falhas.append((ARQUIVO.stem, traceback.format_exc()))

    if falhas:
        print("\nFALHA ao importar:")

        for modulo, erro in falhas:
            print(f"--- {modulo}\n{erro}")

        print(f"Para desfazer: apague {PACOTE}/ e copie {BACKUP} de volta "
              f"para {ARQUIVO}.")

        sys.exit(1)

    print("\nTodos os módulos importam sem erro.")
    print(f"Original guardado em {BACKUP}.")
    print(f"Próximo passo: python {ARQUIVO}  (a bateria de testes deve "
          f"dar o mesmo resultado de antes).")


if __name__ == "__main__":
    try:
        main()
    except ErroDeModularizacao as erro:
        print(f"\nERRO: {erro}")
        sys.exit(1)
