"""Sistemas lineares: matrizes, postos, classificação e equivalência."""

import sympy as sp


def construir_matriz_sistema(equacoes, variaveis):
    """
    Converte um sistema linear em uma matriz de coeficientes
    e um vetor de termos independentes.
    """

    try:
        if not isinstance(equacoes, (list, tuple)):
            return None

        if not equacoes:
            return None

        variaveis = sorted(set(variaveis), key=str)

        if not variaveis:
            return None

        matriz, termos = sp.linear_eq_to_matrix(
            equacoes,
            variaveis
        )

        return {
            "matriz": matriz,
            "termos": termos,
            "variaveis": variaveis
        }

    except (
        TypeError,
        ValueError,
        sp.PolynomialError,
        NotImplementedError
    ):
        return None


def classificar_sistema(dados_postos):
    """
    Classifica um sistema linear como SPD, SPI ou SI.
    """

    try:
        if not isinstance(dados_postos, dict):
            return None

        posto = dados_postos["posto_coeficientes"]
        posto_aumentado = dados_postos["posto_aumentado"]
        numero_variaveis = dados_postos["numero_variaveis"]

        if posto != posto_aumentado:
            return "SI"

        if posto == numero_variaveis:
            return "SPD"

        if posto < numero_variaveis:
            return "SPI"

        return None

    except (TypeError, KeyError, ValueError):
        return None


def analisar_postos_sistema(dados_sistema):
    """
    Calcula os postos da matriz dos coeficientes
    e da matriz aumentada de um sistema linear.
    """

    try:
        if not isinstance(dados_sistema, dict):
            return None

        matriz = dados_sistema["matriz"]
        termos = dados_sistema["termos"]

        matriz_aumentada = matriz.row_join(termos)

        posto_coeficientes = matriz.rank()
        posto_aumentado = matriz_aumentada.rank()

        return {
            "posto_coeficientes": posto_coeficientes,
            "posto_aumentado": posto_aumentado,
            "numero_variaveis": matriz.cols
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        NotImplementedError
    ):
        return None


def analisar_postos_possiveis(dados_sistema):
    """
    Identifica as condições necessárias para que uma
    matriz assuma cada posto possível.

    Retorna as condições simbólicas, sem resolver
    individualmente os parâmetros.
    """
    try:
        if not isinstance(dados_sistema, dict):
            return None

        matriz = dados_sistema["matriz"]

        if not isinstance(matriz, sp.MatrixBase):
            return None

        if matriz.rows == 0 or matriz.cols == 0:
            return None

        limite = min(matriz.rows, matriz.cols)

        menores_por_ordem = {}

        # Calcula os determinantes dos menores
        # separadamente por ordem.
        for tamanho in range(1, limite + 1):

            determinantes = []

            for linhas in sp.utilities.iterables.subsets(
                range(matriz.rows),
                tamanho
            ):
                for colunas in sp.utilities.iterables.subsets(
                    range(matriz.cols),
                    tamanho
                ):
                    menor = matriz.extract(linhas, colunas)

                    determinante = sp.factor(menor.det())

                    if determinante != 0:
                        if determinante not in determinantes:
                            determinantes.append(determinante)

            menores_por_ordem[tamanho] = determinantes

        condicoes_por_posto = {}

        # Analisa cada posto possível, incluindo zero.
        for posto in range(limite + 1):

            condicoes = []

            # Para ter posto r, todos os menores
            # de ordem r+1 precisam ser nulos.
            if posto < limite:

                menores_maiores = menores_por_ordem[posto + 1]

                condicoes.extend(
                    sp.Eq(determinante, 0)
                    for determinante in menores_maiores
                )

            # Para ter posto r > 0, pelo menos um
            # menor de ordem r precisa ser não nulo.
            if posto > 0:

                menores_atuais = menores_por_ordem[posto]

                condicao_nao_nulos = sp.Or(
                    *[
                        sp.Ne(determinante, 0)
                        for determinante in menores_atuais
                    ]
                )

                condicoes.append(condicao_nao_nulos)

            condicao_final = sp.simplify(
                sp.And(*condicoes)
            )

            condicoes_por_posto[posto] = condicao_final

        return {
            "posto_maximo": limite,
            "condicoes_por_posto": condicoes_por_posto
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def obter_condicoes_igualdade_espacos_linhas(
        matriz_1,
        matriz_2
):
    """
    Identifica as condições paramétricas necessárias
    para que duas matrizes tenham o mesmo espaço gerado
    pelas linhas.

    Utiliza a igualdade entre os postos das duas matrizes
    e da matriz formada pelo empilhamento de suas linhas.

    Retorna:
        Expressão booleana simbólica.
        None: quando não for possível determinar.
    """

    try:
        if not isinstance(matriz_1, sp.MatrixBase):
            return None

        if not isinstance(matriz_2, sp.MatrixBase):
            return None

        if matriz_1.rows == 0 or matriz_2.rows == 0:
            return None

        if matriz_1.cols == 0 or matriz_2.cols == 0:
            return None

        if matriz_1.cols != matriz_2.cols:
            return None

        # Empilha as linhas das duas matrizes.
        matriz_combinada = matriz_1.col_join(matriz_2)

        # Analisa os postos possíveis.
        analise_1 = analisar_postos_possiveis({
            "matriz": matriz_1
        })

        analise_2 = analisar_postos_possiveis({
            "matriz": matriz_2
        })

        analise_combinada = analisar_postos_possiveis({
            "matriz": matriz_combinada
        })

        if (
            analise_1 is None
            or analise_2 is None
            or analise_combinada is None
        ):
            return None

        condicoes_1 = analise_1["condicoes_por_posto"]
        condicoes_2 = analise_2["condicoes_por_posto"]

        condicoes_combinadas = analise_combinada[
            "condicoes_por_posto"
        ]

        condicoes_equivalencia = []

        # Os três postos precisam ser iguais.
        for posto in condicoes_1:

            if posto not in condicoes_2:
                continue

            if posto not in condicoes_combinadas:
                continue

            condicao = sp.simplify(
                sp.And(
                    condicoes_1[posto],
                    condicoes_2[posto],
                    condicoes_combinadas[posto]
                )
            )

            if condicao is sp.false:
                continue

            condicoes_equivalencia.append(condicao)

        return sp.simplify(
            sp.Or(*condicoes_equivalencia)
        )

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def analisar_equivalencia_sistemas_parametricos(
        sistema_1,
        sistema_2
):
    """
    Identifica simbolicamente as condições em que dois
    sistemas lineares paramétricos possuem o mesmo
    conjunto de soluções.

    Retorna:
        equivalentes: condição de equivalência.
        nao_equivalentes: negação da equivalência.
        parametros: parâmetros envolvidos.

        None: quando não for possível determinar.
    """

    try:
        if not isinstance(sistema_1, dict):
            return None

        if not isinstance(sistema_2, dict):
            return None

        matriz_1 = sistema_1["matriz"]
        termos_1 = sistema_1["termos"]

        matriz_2 = sistema_2["matriz"]
        termos_2 = sistema_2["termos"]

        variaveis_1 = sistema_1["variaveis"]
        variaveis_2 = sistema_2["variaveis"]

        if variaveis_1 != variaveis_2:
            return None

        if matriz_1.cols != matriz_2.cols:
            return None

        if matriz_1.rows != termos_1.rows:
            return None

        if matriz_2.rows != termos_2.rows:
            return None

        # Identifica os parâmetros dos sistemas.
        parametros_1 = identificar_parametros_sistema(
            sistema_1
        )

        parametros_2 = identificar_parametros_sistema(
            sistema_2
        )

        if parametros_1 is None or parametros_2 is None:
            return None

        parametros = parametros_1 | parametros_2

        # Classifica os dois sistemas simbolicamente.
        classificacao_1 = classificar_sistemas_possiveis(
            sistema_1
        )

        classificacao_2 = classificar_sistemas_possiveis(
            sistema_2
        )

        if classificacao_1 is None or classificacao_2 is None:
            return None

        condicoes_1 = classificacao_1["condicoes_classificacao"]
        condicoes_2 = classificacao_2["condicoes_classificacao"]

        # Condições de consistência.
        consistente_1 = sp.Or(
            condicoes_1["SPD"],
            condicoes_1["SPI"]
        )

        consistente_2 = sp.Or(
            condicoes_2["SPD"],
            condicoes_2["SPI"]
        )

        # Condições de inconsistência.
        inconsistente_1 = condicoes_1["SI"]
        inconsistente_2 = condicoes_2["SI"]

        # Matrizes aumentadas.
        aumentada_1 = matriz_1.row_join(-termos_1)
        aumentada_2 = matriz_2.row_join(-termos_2)

        # Compara os espaços gerados pelas linhas.
        igualdade_espacos = obter_condicoes_igualdade_espacos_linhas(
            aumentada_1,
            aumentada_2
        )

        if igualdade_espacos is None:
            return None

        # Dois sistemas consistentes são equivalentes
        # quando seus espaços de linhas são iguais.
        equivalencia_consistentes = sp.And(
            consistente_1,
            consistente_2,
            igualdade_espacos
        )

        # Dois sistemas impossíveis também são equivalentes.
        equivalencia_impossiveis = sp.And(
            inconsistente_1,
            inconsistente_2
        )

        equivalentes = simplificar_condicao_parametrica(
            sp.Or(
                equivalencia_consistentes,
                equivalencia_impossiveis
            )
        )

        if equivalentes is None:
            return None

        nao_equivalentes = simplificar_condicao_parametrica(
            sp.Not(equivalentes)
        )

        if nao_equivalentes is None:
            return None

        return {
            "equivalentes": equivalentes,
            "nao_equivalentes": nao_equivalentes,
            "parametros": parametros
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def classificar_sistemas_possiveis(dados_sistema):
    """
    Identifica as condições dos parâmetros para que um
    sistema linear seja SPD, SPI ou SI.
    """
    try:
        if not isinstance(dados_sistema, dict):
            return None

        matriz = dados_sistema["matriz"]
        termos = dados_sistema["termos"]

        if not isinstance(matriz, sp.MatrixBase):
            return None

        if not isinstance(termos, sp.MatrixBase):
            return None

        if matriz.rows != termos.rows:
            return None

        numero_variaveis = matriz.cols

        if numero_variaveis == 0:
            return None

        matriz_aumentada = matriz.row_join(termos)

        postos_coeficientes = analisar_postos_possiveis({
            "matriz": matriz
        })

        postos_aumentados = analisar_postos_possiveis({
            "matriz": matriz_aumentada
        })

        if postos_coeficientes is None or postos_aumentados is None:
            return None

        condicoes = {
            "SPD": [],
            "SPI": [],
            "SI": []
        }

        combinacoes = []

        for posto_a, condicao_a in postos_coeficientes[
            "condicoes_por_posto"
        ].items():

            for posto_ampliado, condicao_ampliada in postos_aumentados[
                "condicoes_por_posto"
            ].items():

                if posto_a > posto_ampliado:
                    continue

                condicao = sp.simplify(
                    sp.And(condicao_a, condicao_ampliada)
                )

                if condicao is sp.false:
                    continue

                if posto_a != posto_ampliado:
                    classificacao = "SI"

                elif posto_a == numero_variaveis:
                    classificacao = "SPD"

                else:
                    classificacao = "SPI"

                condicoes[classificacao].append(condicao)

                combinacoes.append({
                    "posto_coeficientes": posto_a,
                    "posto_aumentado": posto_ampliado,
                    "classificacao": classificacao,
                    "condicao": condicao
                })

        resultado = {}

        for classificacao, lista in condicoes.items():
            resultado[classificacao] = sp.simplify(
                sp.Or(*lista)
            )

        return {
            "condicoes_classificacao": resultado,
            "combinacoes_postos": combinacoes
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def verificar_equivalencia_sistemas_numericos(
        dados_sistema_1,
        dados_sistema_2
):
    """
    Verifica se dois sistemas lineares numéricos possuem
    exatamente o mesmo conjunto de soluções.

    Utiliza as formas escalonadas reduzidas das matrizes
    aumentadas.
    """
    try:
        if not isinstance(dados_sistema_1, dict):
            return None

        if not isinstance(dados_sistema_2, dict):
            return None

        matriz_1 = dados_sistema_1["matriz"]
        termos_1 = dados_sistema_1["termos"]

        matriz_2 = dados_sistema_2["matriz"]
        termos_2 = dados_sistema_2["termos"]

        variaveis_1 = dados_sistema_1["variaveis"]
        variaveis_2 = dados_sistema_2["variaveis"]

        if variaveis_1 != variaveis_2:
            return None

        if matriz_1.cols != matriz_2.cols:
            return None

        if matriz_1.rows != termos_1.rows:
            return None

        if matriz_2.rows != termos_2.rows:
            return None

        if (
            matriz_1.free_symbols
            | termos_1.free_symbols
            | matriz_2.free_symbols
            | termos_2.free_symbols
        ):
            return None

        # Constrói as matrizes aumentadas.
        aumentada_1 = matriz_1.row_join(termos_1)
        aumentada_2 = matriz_2.row_join(termos_2)

        # Verifica se cada sistema é possível.
        possivel_1 = matriz_1.rank() == aumentada_1.rank()
        possivel_2 = matriz_2.rank() == aumentada_2.rank()

        # Dois sistemas impossíveis possuem o mesmo
        # conjunto de soluções: o conjunto vazio.
        if not possivel_1 and not possivel_2:
            return True

        if possivel_1 != possivel_2:
            return False

        # Calcula as formas escalonadas reduzidas.
        rref_1, _ = aumentada_1.rref()
        rref_2, _ = aumentada_2.rref()

        # Remove as linhas nulas para permitir a comparação
        # de sistemas com quantidades diferentes de equações.
        linhas_1 = [
            linha
            for linha in rref_1.tolist()
            if any(valor != 0 for valor in linha)
        ]

        linhas_2 = [
            linha
            for linha in rref_2.tolist()
            if any(valor != 0 for valor in linha)
        ]

        return linhas_1 == linhas_2

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError,
        ZeroDivisionError
    ):
        return None


def verificar_equivalencia_sistemas_teste(
        sistema_1,
        sistema_2,
        variaveis
):
    try:
        solucoes_1 = sp.solve(
            sistema_1,
            variaveis,
            dict=True
        )

        solucoes_2 = sp.solve(
            sistema_2,
            variaveis,
            dict=True
        )

        if solucoes_1 == solucoes_2:
            return True

        return False

    except (
        TypeError,
        ValueError,
        NotImplementedError
    ):
        return None


def identificar_parametros_sistema(dados_sistema):
    """
    Identifica os parâmetros presentes nas matrizes
    de um sistema, excluindo as incógnitas.
    """

    try:
        matriz = dados_sistema["matriz"]
        termos = dados_sistema["termos"]
        variaveis = set(dados_sistema["variaveis"])

        simbolos = matriz.free_symbols | termos.free_symbols

        parametros = simbolos - variaveis

        return parametros

    except (TypeError, KeyError, AttributeError):
        return None


def verificar_equivalencia_com_parametros(
        sistema_1,
        sistema_2,
        valores
):
    """
    Verifica a equivalência de dois sistemas após
    substituir os parâmetros por valores numéricos.
    """
    try:
        if not isinstance(valores, dict):
            return None

        parametros_1 = identificar_parametros_sistema(sistema_1)
        parametros_2 = identificar_parametros_sistema(sistema_2)

        if parametros_1 is None or parametros_2 is None:
            return None

        parametros_totais = parametros_1 | parametros_2

        # Exige exatamente os parâmetros necessários.
        if set(valores.keys()) != parametros_totais:
            return None

        # Filtra os valores de cada sistema.
        valores_1 = {
            parametro: valores[parametro]
            for parametro in parametros_1
        }

        valores_2 = {
            parametro: valores[parametro]
            for parametro in parametros_2
        }

        sistema_1_substituido = substituir_parametros_sistema(
            sistema_1,
            valores_1
        )

        sistema_2_substituido = substituir_parametros_sistema(
            sistema_2,
            valores_2
        )

        if sistema_1_substituido is None:
            return None

        if sistema_2_substituido is None:
            return None

        return verificar_equivalencia_sistemas_numericos(
            sistema_1_substituido,
            sistema_2_substituido
        )

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError
    ):
        return None


def obter_condicoes_degeneracao_sistema(dados_sistema):
    """
    Identifica as condições que provocam a redução
    do posto genérico da matriz dos coeficientes e
    da matriz aumentada de um sistema linear.
    """
    try:
        if not isinstance(dados_sistema, dict):
            return None

        matriz = dados_sistema["matriz"]
        termos = dados_sistema["termos"]

        if not isinstance(matriz, sp.MatrixBase):
            return None

        if not isinstance(termos, sp.MatrixBase):
            return None

        if matriz.rows != termos.rows:
            return None

        matriz_aumentada = matriz.row_join(termos)

        analise_coeficientes = analisar_postos_possiveis({
            "matriz": matriz
        })

        analise_aumentada = analisar_postos_possiveis({
            "matriz": matriz_aumentada
        })

        if analise_coeficientes is None or analise_aumentada is None:
            return None

        def extrair_degeneracoes(matriz_analisada, analise):

            condicoes_por_posto = analise["condicoes_por_posto"]

            postos_possiveis = [
                posto
                for posto, condicao in condicoes_por_posto.items()
                if condicao is not sp.false
            ]

            if not postos_possiveis:
                return None

            posto_generico = max(postos_possiveis)

            if posto_generico == 0:
                return {
                    "posto_generico": 0,
                    "degeneracoes": []
                }

            determinantes = []

            # Calcula somente os menores da ordem do
            # posto genérico.
            for linhas in sp.utilities.iterables.subsets(
                range(matriz_analisada.rows),
                posto_generico
            ):
                for colunas in sp.utilities.iterables.subsets(
                    range(matriz_analisada.cols),
                    posto_generico
                ):
                    menor = matriz_analisada.extract(
                        linhas,
                        colunas
                    )

                    determinante = sp.factor(menor.det())

                    if determinante != 0:
                        if determinante not in determinantes:
                            determinantes.append(determinante)

            if not determinantes:
                return None

            # O posto será inferior ao genérico quando
            # todos os menores dessa ordem forem nulos.
            condicao_degeneracao = sp.simplify(
                sp.And(*[
                    sp.Eq(determinante, 0)
                    for determinante in determinantes
                ])
            )

            if condicao_degeneracao is sp.false:
                degeneracoes = []

            elif condicao_degeneracao is sp.true:
                return None

            else:
                degeneracoes = [{
                    "posto_maximo": posto_generico - 1,
                    "condicao": condicao_degeneracao
                }]

            return {
                "posto_generico": posto_generico,
                "degeneracoes": degeneracoes
            }

        resultado_coeficientes = extrair_degeneracoes(
            matriz,
            analise_coeficientes
        )

        resultado_aumentado = extrair_degeneracoes(
            matriz_aumentada,
            analise_aumentada
        )

        if resultado_coeficientes is None or resultado_aumentado is None:
            return None

        return {
            "coeficientes": resultado_coeficientes,
            "aumentada": resultado_aumentado
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError
    ):
        return None


def substituir_parametros_sistema(dados_sistema, valores):
    """
    Substitui todos os parâmetros de um sistema por
    valores numéricos reais.

    Retorna uma nova estrutura com matriz e termos
    independentes já substituídos.
    """
    try:
        if not isinstance(dados_sistema, dict):
            return None

        if not isinstance(valores, dict):
            return None

        matriz = dados_sistema["matriz"]
        termos = dados_sistema["termos"]
        variaveis = dados_sistema["variaveis"]

        parametros = identificar_parametros_sistema(dados_sistema)

        if parametros is None:
            return None

        # Exige que todos os parâmetros sejam informados.
        if set(valores.keys()) != parametros:
            return None

        substituicoes = {}

        for parametro, valor in valores.items():

            valor = sp.sympify(valor)

            if not valor.is_number or valor.is_real is not True:
                return None

            if valor.is_finite is False:
                return None

            substituicoes[parametro] = valor

        nova_matriz = matriz.subs(substituicoes).applyfunc(
            sp.simplify
        )

        novos_termos = termos.subs(substituicoes).applyfunc(
            sp.simplify
        )

        # Não pode restar nenhum parâmetro.
        if nova_matriz.free_symbols or novos_termos.free_symbols:
            return None

        return {
            "matriz": nova_matriz,
            "termos": novos_termos,
            "variaveis": variaveis
        }

    except (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        NotImplementedError
    ):
        return None


def obter_determinantes_menores(matriz):
    """
    Calcula os determinantes de todos os menores quadrados
    de uma matriz.
    """

    try:
        if not isinstance(matriz, sp.MatrixBase):
            return None

        determinantes = []

        limite = min(matriz.rows, matriz.cols)

        for tamanho in range(1, limite + 1):

            for linhas in sp.utilities.iterables.subsets(
                range(matriz.rows),
                tamanho
            ):

                for colunas in sp.utilities.iterables.subsets(
                    range(matriz.cols),
                    tamanho
                ):

                    menor = matriz.extract(
                        linhas,
                        colunas
                    )

                    determinante = sp.factor(menor.det())

                    if determinante != 0:
                        determinantes.append(determinante)

        return list(dict.fromkeys(determinantes))

    except (
        TypeError,
        ValueError,
        NotImplementedError
    ):
        return None


def simplificar_condicao_parametrica(condicao):
    """
    Simplifica condições paramétricas combinando
    normalização algébrica e simplificação lógica.
    """

    try:
        if condicao is sp.true or condicao is sp.false:
            return condicao

        if not isinstance(condicao, sp.logic.boolalg.Boolean):
            return None

        # Primeiro normaliza as relações algébricas.
        normalizada = normalizar_condicao_algebrica(
            condicao
        )

        if normalizada is None:
            return None

        # Depois simplifica a estrutura lógica.
        simplificada = sp.simplify_logic(
            normalizada,
            force=False
        )

        # Simplificação simbólica complementar.
        simplificada = sp.simplify(
            simplificada
        )

        return simplificada

    except (
        TypeError,
        ValueError,
        NotImplementedError,
        AttributeError
    ):
        return None


def normalizar_condicao_algebrica(condicao):
    """
    Normaliza condições algébricas envolvendo igualdade
    ou desigualdade com zero.

    Exemplos:
        Ne(2*a*b, 0) -> Ne(a*b, 0)
        Eq(3*a*b, 0) -> Eq(a*b, 0)
    """

    try:
        if isinstance(condicao, sp.And):
            partes = [
                normalizar_condicao_algebrica(parte)
                for parte in condicao.args
            ]

            if any(parte is None for parte in partes):
                return None

            return sp.And(*partes)

        if isinstance(condicao, sp.Or):
            partes = [
                normalizar_condicao_algebrica(parte)
                for parte in condicao.args
            ]

            if any(parte is None for parte in partes):
                return None

            return sp.Or(*partes)

        if isinstance(condicao, sp.Not):
            parte = normalizar_condicao_algebrica(
                condicao.args[0]
            )

            if parte is None:
                return None

            return sp.Not(parte)

        if not isinstance(condicao, (
            sp.Equality,
            sp.Unequality
        )):
            return condicao

        esquerda = condicao.lhs
        direita = condicao.rhs

        if direita != 0:
            return condicao

        esquerda = sp.factor(esquerda)

        coeficiente, fator = esquerda.as_coeff_Mul()

        if coeficiente.is_number and coeficiente != 0:
            esquerda = fator

        return condicao.func(esquerda, 0)

    except (
        TypeError,
        ValueError,
        AttributeError,
        NotImplementedError
    ):
        return None
