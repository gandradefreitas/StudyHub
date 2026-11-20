"""
Motor de verificação matemática do StudyHub.

Este arquivo é a fachada pública: reexporta a API dos módulos da pasta motor_matematico/
e mantém o bloco de testes (execute este arquivo para rodar a bateria de regressão).
"""


import multiprocessing


import sympy as sp


from motor_matematico.contrato import (
    STATUS_CONDICIONAL,
    STATUS_CORRETO,
    STATUS_INCORRETO,
    STATUS_INDETERMINADO,
    STATUS_INVALIDO,
    _ERROS_DE_ENTRADA,
    _formatar_condicao,
    _formatar_condicoes,
    _resultado_invalido,
    montar_resultado,
)
from motor_matematico.tempo import (
    _EM_PROCESSO_ISOLADO,
    _LIMITE_DE_PARTIDA,
    _configuracao_de_tempo,
    _executar_com_limite,
    _executar_no_filho,
    _executar_protegido,
    _interface_protegida,
    _limite_efetivo,
    _receber,
    _resultado_erro_interno,
    _resultado_tempo_excedido,
    configurar_limite_de_tempo,
)
from motor_matematico.auxiliares_de_teste import (
    _auxiliar_com_erro_para_teste,
    _auxiliar_lento_para_teste,
    _auxiliar_que_derruba_o_processo,
)
from motor_matematico.normalizacao import (
    _REGEX_TOKEN,
    _SUBSTITUICOES,
    _SUPERESCRITOS,
    _analisar_sintaxe,
    normalizar_entrada,
)
from motor_matematico.interpretador import (
    _LIMITE_BITS,
    _validar_tamanho_numerico,
    interpretar_expressao,
)
from motor_matematico.dominio import (
    _comparar_conjuntos_reais,
    _existe_ponto_separador,
    _normalizar_condicoes_dominio,
    combinar_restricoes_raizes,
    comparar_dominios_expressoes,
    identificar_denominadores,
    identificar_radicandos,
    identificar_restricoes,
    identificar_restricoes_raizes,
    identificar_variaveis,
    inspecionar_variaveis_denominadores,
    obter_condicoes_denominadores,
    obter_condicoes_dominio_expressao,
    obter_condicoes_raizes,
    obter_dominio,
    obter_dominio_raizes,
    obter_variaveis_equacao,
    verificar_condicoes_dominio,
)
from motor_matematico.equacoes import (
    interpretar_equacao,
    obter_condicoes_dominio,
)
from motor_matematico.equivalencia import (
    _comparar_simbolicamente,
    _existe_ponto_separador_equacoes,
    analisar_equivalencia_expressoes,
    analisar_equivalencia_vetores,
    comparar_condicoes_dominio,
    obter_condicoes_anulacao,
    verificar_coeficientes_nulos,
    verificar_condicoes_anulacao,
    verificar_equivalencia,
    verificar_equivalencia_equacoes,
    verificar_equivalencia_multivariavel,
    verificar_operacao,
    verificar_ponto_contraexemplo,
    verificar_proporcionalidade_vetores,
)
from motor_matematico.sistemas import (
    analisar_equivalencia_sistemas_parametricos,
    analisar_postos_possiveis,
    analisar_postos_sistema,
    classificar_sistema,
    classificar_sistemas_possiveis,
    construir_matriz_sistema,
    identificar_parametros_sistema,
    normalizar_condicao_algebrica,
    obter_condicoes_degeneracao_sistema,
    obter_condicoes_igualdade_espacos_linhas,
    obter_determinantes_menores,
    simplificar_condicao_parametrica,
    substituir_parametros_sistema,
    verificar_equivalencia_com_parametros,
    verificar_equivalencia_sistemas_numericos,
    verificar_equivalencia_sistemas_teste,
)
from motor_matematico.avaliacao import (
    analisar_dominio_expressao,
    avaliar_equivalencia_equacoes,
    avaliar_equivalencia_expressoes,
    avaliar_equivalencia_sistemas,
)
from motor_matematico.resolucao import (
    _conjunto_resolvido,
    _ordenar_reais,
    obter_conjunto_solucao_equacao,
    resolver_equacao,
    verificar_solucao_equacao,
)
from motor_matematico.transformacoes import (
    _contraexemplo_expressoes,
    _eh_equacao,
    _listar_conjunto,
    _procurar_contraexemplo,
    _verificar_transformacao_equacao,
    _verificar_transformacao_expressao,
    verificar_transformacao,
)
from motor_matematico.diagnostico import (
    _diagnosticar,
    _diagnosticar_equacoes,
    _diagnosticar_expressoes,
    _diagnostico,
    _diagnostico_generico,
    _termo_em_texto,
    diagnosticar_transformacao,
)
from motor_matematico.numerico import (
    _CONDICAO_DE_PRECISAO,
    _MODOS_DE_ARREDONDAMENTO,
    _PRECISAO_AVALIACAO,
    _PRECISAO_DECIMAL,
    _REGEX_DECIMAL,
    _casas,
    _como_texto,
    _decimal_do_valor,
    _iguais_exatamente,
    _literal_decimal,
    _modos_compativeis,
    _quantizar,
    _validar_regra_de_precisao,
    _valor_numerico,
    comparar_resultado_numerico,
)
from motor_matematico.procedimentos import (
    _MAX_ETAPAS,
    _erro_de_leitura,
    analisar_procedimento,
)


__all__ = [
    "STATUS_CONDICIONAL",
    "STATUS_CORRETO",
    "STATUS_INCORRETO",
    "STATUS_INDETERMINADO",
    "STATUS_INVALIDO",
    "analisar_dominio_expressao",
    "analisar_equivalencia_expressoes",
    "analisar_equivalencia_sistemas_parametricos",
    "analisar_equivalencia_vetores",
    "analisar_postos_possiveis",
    "analisar_postos_sistema",
    "analisar_procedimento",
    "avaliar_equivalencia_equacoes",
    "avaliar_equivalencia_expressoes",
    "avaliar_equivalencia_sistemas",
    "classificar_sistema",
    "classificar_sistemas_possiveis",
    "combinar_restricoes_raizes",
    "comparar_condicoes_dominio",
    "comparar_dominios_expressoes",
    "comparar_resultado_numerico",
    "configurar_limite_de_tempo",
    "construir_matriz_sistema",
    "diagnosticar_transformacao",
    "identificar_denominadores",
    "identificar_parametros_sistema",
    "identificar_radicandos",
    "identificar_restricoes",
    "identificar_restricoes_raizes",
    "identificar_variaveis",
    "inspecionar_variaveis_denominadores",
    "interpretar_equacao",
    "interpretar_expressao",
    "montar_resultado",
    "normalizar_condicao_algebrica",
    "normalizar_entrada",
    "obter_condicoes_anulacao",
    "obter_condicoes_degeneracao_sistema",
    "obter_condicoes_denominadores",
    "obter_condicoes_dominio",
    "obter_condicoes_dominio_expressao",
    "obter_condicoes_igualdade_espacos_linhas",
    "obter_condicoes_raizes",
    "obter_conjunto_solucao_equacao",
    "obter_determinantes_menores",
    "obter_dominio",
    "obter_dominio_raizes",
    "obter_variaveis_equacao",
    "resolver_equacao",
    "simplificar_condicao_parametrica",
    "substituir_parametros_sistema",
    "verificar_coeficientes_nulos",
    "verificar_condicoes_anulacao",
    "verificar_condicoes_dominio",
    "verificar_equivalencia",
    "verificar_equivalencia_com_parametros",
    "verificar_equivalencia_equacoes",
    "verificar_equivalencia_multivariavel",
    "verificar_equivalencia_sistemas_numericos",
    "verificar_equivalencia_sistemas_teste",
    "verificar_operacao",
    "verificar_ponto_contraexemplo",
    "verificar_proporcionalidade_vetores",
    "verificar_solucao_equacao",
    "verificar_transformacao",
]


if __name__ == "__main__":

    x, y = sp.symbols("x y", real=True)
    a = sp.Symbol("a", real=True)

    contagem = {"total": 0}
    falhas = []
    pendencias = []

    def testar(nome, funcao, esperado):
        contagem["total"] += 1

        try:
            obtido = funcao()
        except Exception as erro:
            falhas.append(f"{nome}: exceção {type(erro).__name__}: {erro}")
            return

        if isinstance(esperado, bool) or esperado is None:
            passou = obtido is esperado
        else:
            passou = obtido == esperado

        if not passou:
            falhas.append(
                f"{nome}: esperado {esperado!r}, obtido {obtido!r}"
            )

    def testar_erro(nome, funcao):
        """A entrada deve ser rejeitada com ValueError/SyntaxError."""
        contagem["total"] += 1

        try:
            funcao()
        except (ValueError, SyntaxError):
            return
        except Exception as erro:
            falhas.append(
                f"{nome}: exceção inesperada "
                f"{type(erro).__name__}: {erro}"
            )
            return

        falhas.append(f"{nome}: deveria ter sido rejeitada")

    def pendente(descricao, funcao, resolvido):
        try:
            ok = bool(resolvido(funcao()))
        except Exception:
            ok = False

        pendencias.append((descricao, ok))

    def avaliar(condicao, valores):
        resultado = condicao.subs(valores)

        if resultado is sp.true:
            return True

        if resultado is sp.false:
            return False

        return None

    def sistema(equacoes, variaveis=(x, y)):
        return construir_matriz_sistema(list(equacoes), list(variaveis))

    # ------------------------------------------------------------
    # Interpretador: entradas válidas
    # ------------------------------------------------------------
    testar("interpretar 2 + 3", lambda: interpretar_expressao("2 + 3"), 5)
    testar(
        "interpretar decimal 0.5",
        lambda: interpretar_expressao("0.5"),
        sp.Rational(1, 2)
    )

    # ------------------------------------------------------------
    # Interpretador: entradas que devem ser rejeitadas
    # ------------------------------------------------------------
    for nome, entrada in [
        ("código arbitrário", "__import__('os')"),
        ("booleano", "True + 1"),
        ("número complexo", "1.5j"),
        ("variável com 2 letras", "xy + 1"),
        ("expoente > 100", "2**101"),
        ("divisão por zero", "1/0"),
        ("zero com expoente negativo", "0**(-1)"),
        ("raiz de negativo", "sqrt(-4)"),
        ("expoente não inteiro", "2**x"),
        ("inteiro grande demais", "1000000000000000000"),
        ("entrada longa demais", "x" + "+x" * 200),
        ("entrada não textual", 5),
    ]:
        testar_erro(
            f"rejeitar {nome}",
            lambda e=entrada: interpretar_expressao(e)
        )

    # ------------------------------------------------------------
    # Equivalência de expressões
    # ------------------------------------------------------------
    for nome, e1, e2, esperado in [
        ("quadrado da soma", "x**2 + 2*x + 1", "(x + 1)**2", True),
        ("expansão", "(x + 2)*(x + 3)", "x**2 + 5*x + 6", True),
        ("fatoração", "x**2 - 9", "(x - 3)*(x + 3)", True),
        ("simplificação", "(2*x + 4)/2", "x + 2", True),
        ("sqrt(x²) = |x|", "sqrt(x**2)", "abs(x)", True),
        ("x²+1 ≠ (x+1)²", "x**2 + 1", "(x + 1)**2", False),
        ("x ≠ 2x", "x", "2*x", False),
        ("sqrt(x²) ≠ x", "sqrt(x**2)", "x", False),
        ("1/x ≠ 2/x", "1/x", "2/x", False),
        ("entrada inválida", "2 +", "2", None),
    ]:
        testar(
            f"equivalência: {nome}",
            lambda p=e1, q=e2: verificar_equivalencia(p, q),
            esperado
        )

    # ------------------------------------------------------------
    # Verificação de operação
    # ------------------------------------------------------------
    testar("operação 2+3=5",
           lambda: verificar_operacao("2 + 3", "5")["correta"], True)
    testar("operação 2+3=6",
           lambda: verificar_operacao("2 + 3", "6")["correta"], False)
    testar("operação distributiva",
           lambda: verificar_operacao("2*(x + 3)", "2*x + 6")["correta"],
           True)
    testar("operação inválida (1/0)",
           lambda: verificar_operacao("1/0", "1")["correta"], None)

    # ------------------------------------------------------------
    # Domínio
    # ------------------------------------------------------------
    testar("restrição 1/(x-3)",
           lambda: identificar_restricoes("1/(x - 3)"), [3])
    testar("restrição 1/(x²-4)",
           lambda: identificar_restricoes("1/(x**2 - 4)"), [-2, 2])
    testar("restrição de dois denominadores",
           lambda: identificar_restricoes("1/x + 1/(x - 1)"), [0, 1])
    testar("sem denominadores",
           lambda: identificar_restricoes("x + 1"), [])
    testar("denominador sem raiz real",
           lambda: identificar_restricoes("1/(x**2 + 1)"), [])
    testar("denominador multivariável",
           lambda: identificar_restricoes("1/(x + y)"), None)
    testar("condição de denominador (qtd)",
           lambda: len(obter_condicoes_denominadores("1/(x - 2)")), 1)
    testar("condição de denominador (lhs)",
           lambda: obter_condicoes_denominadores("1/(x - 2)")[0].lhs,
           x - 2)
    testar("denominador constante",
           lambda: obter_condicoes_denominadores("1/2"), [])
    testar("condição de raiz (lhs)",
           lambda: obter_condicoes_raizes("sqrt(x - 2)")[0].lhs, x - 2)
    testar("domínio sqrt(x-2)",
           lambda: obter_dominio("sqrt(x - 2)"), sp.Interval(2, sp.oo))
    testar("domínio 1/(x-3)",
           lambda: obter_dominio("1/(x - 3)"),
           sp.Union(sp.Interval.open(-sp.oo, 3),
                    sp.Interval.open(3, sp.oo)))
    testar("domínio sqrt((x-1)/(x+2))",
           lambda: obter_dominio("sqrt((x - 1)/(x + 2))"),
           sp.Union(sp.Interval.open(-sp.oo, -2),
                    sp.Interval(1, sp.oo)))

    # ------------------------------------------------------------
    # Equações
    # ------------------------------------------------------------
    testar("interpretar_equacao: diferença",
           lambda: interpretar_equacao("x = 2")["diferenca"], x - 2)
    testar_erro("interpretar_equacao sem '='",
                lambda: interpretar_equacao("x + 1"))

    for nome, e1, e2, esperado in [
        ("x²=4 vs fatorada", "x**2 = 4", "(x - 2)*(x + 2) = 0", True),
        ("x²=4 vs x=2 (perde solução)", "x**2 = 4", "x = 2", False),
        ("x²=9 vs x=3", "x**2 = 9", "x = 3", False),
        ("lados trocados", "x = 2", "2 = x", True),
        ("simplificação com domínio",
         "(x**2 - 1)/(x - 1) = 0", "x + 1 = 0", True),
        ("raiz extra pelo domínio",
         "(x**2 - 1)/(x - 1) = 2", "x + 1 = 2", False),
        ("equação com raiz", "sqrt(x) = 2", "x = 4", True),
        ("duas variáveis (não suportado)",
         "x + y = 1", "y = 1 - x", None),
        ("dois sinais de igualdade", "x = 1", "x = 1 = 2", None),
    ]:
        testar(
            f"equação: {nome}",
            lambda p=e1, q=e2: verificar_equivalencia_equacoes(p, q),
            esperado
        )

    # ------------------------------------------------------------
    # Equivalência multivariável (diferenças já em forma f = 0)
    # ------------------------------------------------------------
    testar("multivar: múltiplo por constante",
           lambda: verificar_equivalencia_multivariavel(
               x + y - 1, 2*(x + y - 1), [x, y]), True)
    testar("multivar: retas distintas",
           lambda: verificar_equivalencia_multivariavel(
               x + y - 1, x - y, [x, y]), False)
    testar("multivar: 0 = 0",
           lambda: verificar_equivalencia_multivariavel(
               sp.Integer(0), sp.Integer(0), [x, y]), True)

    # ------------------------------------------------------------
    # Sistemas lineares numéricos
    # ------------------------------------------------------------
    def classificar(equacoes):
        dados = sistema(equacoes)
        return classificar_sistema(analisar_postos_sistema(dados))

    testar("classificação SPD",
           lambda: classificar([x + y - 3, x - y - 1]), "SPD")
    testar("classificação SPI",
           lambda: classificar([x + y - 2, 2*x + 2*y - 4]), "SPI")
    testar("classificação SI",
           lambda: classificar([x + y - 1, x + y - 2]), "SI")

    s_base = [x + y - 3, x - y - 1]

    for nome, outro, esperado in [
        ("mesma solução, outra forma", [2*x - 4, y - 1], True),
        ("equação redundante", [x + y - 3, x - y - 1, 2*x - 4], True),
        ("solução diferente", [x + y - 3, x - y - 2], False),
        ("possível vs impossível", [x + y - 1, x + y - 2], False),
    ]:
        testar(
            f"sistema numérico: {nome}",
            lambda o=outro: verificar_equivalencia_sistemas_numericos(
                sistema(s_base), sistema(o)),
            esperado
        )

    testar("sistemas impossíveis equivalentes",
           lambda: verificar_equivalencia_sistemas_numericos(
               sistema([x + y - 1, x + y - 2]),
               sistema([x - 1, x - 2])), True)

    # ------------------------------------------------------------
    # Sistemas paramétricos
    # ------------------------------------------------------------
    s_param = sistema([a*x + y - 1, x + a*y - 1])
    s_dobro = sistema([2*(a*x + y - 1), x + a*y - 1])
    s_outro = sistema([a*x + y - 1, x + a*y - 2])

    testar("parâmetros identificados",
           lambda: identificar_parametros_sistema(s_param), {a})
    testar("numérico recusa parâmetros",
           lambda: verificar_equivalencia_sistemas_numericos(
               s_param, s_param), None)

    def condicao_classe(nome_classe):
        return classificar_sistemas_possiveis(s_param)[
            "condicoes_classificacao"][nome_classe]

    for valor, classe in [(2, "SPD"), (1, "SPI"), (-1, "SI")]:
        for nome_classe in ("SPD", "SPI", "SI"):
            testar(
                f"classificação paramétrica a={valor} é {nome_classe}?",
                lambda n=nome_classe, v=valor: avaliar(
                    condicao_classe(n), {a: v}),
                nome_classe == classe
            )

    def condicao_equivalencia(outro):
        return analisar_equivalencia_sistemas_parametricos(
            s_param, outro)["equivalentes"]

    for valor in (2, 1, -1, 0):
        testar(
            f"sistema com 1ª equação x2, a={valor}",
            lambda v=valor: avaliar(
                condicao_equivalencia(s_dobro), {a: v}),
            True
        )

    for valor, esperado in [(2, False), (1, False), (-1, True)]:
        testar(
            f"sistema com termo independente alterado, a={valor}",
            lambda v=valor: avaliar(
                condicao_equivalencia(s_outro), {a: v}),
            esperado
        )

    # ------------------------------------------------------------
    # Etapa 2: normalização de entrada
    # ------------------------------------------------------------
    for nome, entrada, esperado in [
        ("multiplicação implícita", "2x + 1", 2*x + 1),
        ("número e parênteses", "2(x + 3)", 2*(x + 3)),
        ("variável e parênteses", "x(x + 1)", x*(x + 1)),
        ("parênteses adjacentes", "(x + 1)(x - 2)", (x + 1)*(x - 2)),
        ("potência com ^", "x^2", x**2),
        ("potência com ²", "x²", x**2),
        ("potência com ⁻¹", "x⁻¹", 1/x),
        ("² com coeficiente", "2x² + 1", 2*x**2 + 1),
        ("vírgula decimal", "0,5", sp.Rational(1, 2)),
        ("vírgula com variável", "1,5x", sp.Rational(3, 2)*x),
        ("notação científica", "1e-3", sp.Rational(1, 1000)),
        ("símbolos ×, ·, ÷, −", "6 ÷ 3 + 2 × 2 − 1", 5),
        ("ponto médio", "3 · x", 3*x),
        ("função com coeficiente", "2sqrt(x)", 2*sp.sqrt(x)),
        ("agrupamento antes de variável", "(1/2)x", x/2),
        ("divisão explícita", "1/(2x)", 1/(2*x)),
        ("(x²)^50 é aceito", "(x**2)**50", x**100),
    ]:
        testar(
            f"normalização: {nome}",
            lambda e=entrada: interpretar_expressao(e),
            esperado
        )

    for nome, entrada in [
        ("ambígua 1/2x", "1/2x"),
        ("ambígua x/2(x+1)", "x/2(x + 1)"),
        ("número complexo 1.5j", "1.5j"),
        ("número complexo 2j", "2j"),
        ("variável de 2 letras após coeficiente", "2xy"),
        ("dois números separados", "2 3"),
        ("vírgula como separador", "x,y"),
        ("potência numérica aninhada", "((9**100)**100)**100"),
        ("potência simbólica aninhada", "((x + 1)**2)**51"),
    ]:
        testar_erro(
            f"normalização rejeita: {nome}",
            lambda e=entrada: interpretar_expressao(e)
        )

    testar("equivalência com notação do estudante",
           lambda: verificar_equivalencia("(x + 1)(x - 2)", "x² - x - 2"),
           True)
    testar("restrição com notação do estudante",
           lambda: identificar_restricoes("1/(2x - 6)"), [3])
    testar("raiz com notação do estudante",
           lambda: obter_dominio("sqrt(2x - 4)"),
           sp.Interval(2, sp.oo))
    testar("equação com notação do estudante",
           lambda: verificar_equivalencia_equacoes(
               "x² = 4", "(x - 2)(x + 2) = 0"), True)
    testar("equação linear com notação do estudante",
           lambda: verificar_equivalencia_equacoes(
               "2x + 6 = 10", "x = 2"), True)

    # ------------------------------------------------------------
    # Etapa 3: domínio na equivalência de expressões
    # ------------------------------------------------------------
    for nome, entrada, esperado in [
        ("1/x**2", "1/x**2", [0]),
        ("x**(-2)", "x**(-2)", [0]),
        ("x**(-1)", "x**(-1)", [0]),
        ("x⁻¹", "x⁻¹", [0]),
        ("2**(-1) é constante", "2**(-1)", []),
    ]:
        testar(
            f"restrição: {nome}",
            lambda e=entrada: identificar_restricoes(e),
            esperado
        )

    testar("condição de x**(-1)",
           lambda: obter_condicoes_denominadores("x**(-1)")[0].lhs, x)

    for nome, e1, e2, esperado in [
        ("x/x vs 1", "x/x", "1", "condicional"),
        ("(x²-1)/(x-1) vs x+1", "(x² - 1)/(x - 1)", "x + 1", "condicional"),
        ("domínios distintos, mesma função",
         "x/x", "(x + 1)/(x + 1)", "condicional"),
        ("sqrt(x)² vs x", "sqrt(x)**2", "x", "condicional"),
        ("1/x vs x**(-1)", "1/x", "x**(-1)", "equivalentes"),
        ("denominador em outra forma",
         "1/(x*(x - 1))", "1/(x**2 - x)", "equivalentes"),
        ("sqrt(x²) vs |x|", "sqrt(x**2)", "abs(x)", "equivalentes"),
        ("expansão sem restrições",
         "(x + 1)(x - 2)", "x² - x - 2", "equivalentes"),
        ("x²+1 vs (x+1)²", "x**2 + 1", "(x + 1)**2", "diferentes"),
        ("1/x vs 2/x", "1/x", "2/x", "diferentes"),
        ("multivar: x*y/x vs y", "x*y/x", "y", "condicional"),
        ("multivar: (x+y)/(x+y) vs 1", "(x + y)/(x + y)", "1",
         "condicional"),
        ("multivar: 1/(x*y) vs 1/x/y", "1/(x*y)", "1/x/y", "equivalentes"),
        ("entrada inválida", "2 +", "2", "invalido"),
    ]:
        testar(
            f"análise de equivalência: {nome}",
            lambda p=e1, q=e2: analisar_equivalencia_expressoes(
                p, q)["resultado"],
            esperado
        )

    for nome, e1, e2, esperado in [
        ("1/x vs x**(-1)", "1/x", "x**(-1)", True),
        ("x/x vs 1", "x/x", "1", False),
        ("sqrt(x²) vs |x|", "sqrt(x**2)", "abs(x)", True),
        ("sqrt(x) vs x", "sqrt(x)", "x", False),
        ("multivar: x*y/x vs y", "x*y/x", "y", False),
        ("multivar: 1/(x*y) vs 1/x/y", "1/(x*y)", "1/x/y", True),
        ("multivar: (x+y)/(x+y) vs 1", "(x + y)/(x + y)", "1", False),
        ("multivar: 1/(x*y) vs 1/(x+y)", "1/(x*y)", "1/(x + y)", False),
    ]:
        testar(
            f"domínios: {nome}",
            lambda p=e1, q=e2: comparar_dominios_expressoes(p, q),
            esperado
        )

    testar("verificar_equivalencia: x/x vs 1 é falso (domínio)",
           lambda: verificar_equivalencia("x/x", "1"), False)
    testar("verificar_equivalencia: 1/x vs x**(-1)",
           lambda: verificar_equivalencia("1/x", "x**(-1)"), True)

    # ------------------------------------------------------------
    # Etapa 4: equivalência multivariável sem False indevido
    # ------------------------------------------------------------
    for nome, d1, d2, vars_, esperado in [
        ("x²+y²=0 vs x²+2y²=0 (mesma solução real)",
         x**2 + y**2, x**2 + 2*y**2, [x, y], None),
        ("x²+1=0 vs x²+2=0 (ambas sem solução real)",
         x**2 + 1, x**2 + 2, [x], None),
        ("x²=4 vs x=2 (perde solução)",
         x**2 - 4, x - 2, [x], False),
        ("x²=4 vs (x-2)(x+2)=0",
         x**2 - 4, (x - 2)*(x + 2), [x], True),
        ("retas distintas",
         x + y - 1, x - y, [x, y], False),
        ("circunferências distintas",
         x**2 + y**2 - 1, x**2 + y**2 - 4, [x, y], False),
        ("x*y=0 vs x=0",
         x*y, x, [x, y], False),
        ("equação vs identidade",
         x + y - 1, sp.Integer(0), [x, y], False),
        ("múltiplo por constante",
         x + y - 1, 3*(x + y - 1), [x, y], True),
        ("parâmetro pode anular (a=0)",
         a*x - a, x - 1, [x], None),
    ]:
        testar(
            f"multivariável: {nome}",
            lambda p=d1, q=d2, v=vars_: verificar_equivalencia_multivariavel(
                p, q, v),
            esperado
        )

    # ------------------------------------------------------------
    # Etapa 5: interface pública
    # ------------------------------------------------------------
    import json

    def status_de(funcao, *args, **kwargs):
        return lambda: funcao(*args, **kwargs)["status"]

    for nome, e1, e2, esperado in [
        ("equivalentes", "(x + 1)^2", "x² + 2x + 1", "correct"),
        ("condicional x/x vs 1", "x/x", "1", "conditional"),
        ("incorreto", "x² + 1", "(x + 1)²", "incorrect"),
        ("domínios diferentes e funções diferentes", "1/x", "2/x",
         "incorrect"),
        ("entrada inválida", "2 +", "2", "invalid"),
    ]:
        testar(
            f"interface expressões: {nome}",
            status_de(avaliar_equivalencia_expressoes, e1, e2),
            esperado
        )

    testar("interface expressões: condições do caso condicional",
           lambda: avaliar_equivalencia_expressoes("x/x", "1")["condicoes"],
           ["x != 0"])
    testar("interface expressões: restrições",
           lambda: avaliar_equivalencia_expressoes(
               "1/x", "2/x")["restricoes"], ["x != 0"])
    testar("interface expressões: resultado booleano em correct",
           lambda: avaliar_equivalencia_expressoes(
               "x + x", "2x")["resultado"], True)
    testar("interface expressões: resultado nulo em conditional",
           lambda: avaliar_equivalencia_expressoes(
               "x/x", "1")["resultado"], None)
    testar("interface expressões: entrada não textual",
           status_de(avaliar_equivalencia_expressoes, None, None),
           "invalid")

    for nome, e1, e2, esperado in [
        ("x²=4 vs fatorada", "x² = 4", "(x - 2)(x + 2) = 0", "correct"),
        ("perde solução", "x² = 4", "x = 2", "incorrect"),
        ("com domínio", "(x² - 1)/(x - 1) = 0", "x + 1 = 0", "correct"),
        ("duas variáveis equivalentes", "x + y = 1", "y = 1 - x",
         "correct"),
        ("duas variáveis diferentes", "x + y = 1", "x - y = 0",
         "incorrect"),
        ("sem variáveis", "1 = 1", "2 = 2", "indeterminate"),
        ("sem sinal de igualdade", "x + 1", "x = 1", "invalid"),
    ]:
        testar(
            f"interface equações: {nome}",
            status_de(avaliar_equivalencia_equacoes, e1, e2),
            esperado
        )

    testar("interface equações: restrições",
           lambda: avaliar_equivalencia_equacoes(
               "(x² - 1)/(x - 1) = 0", "x + 1 = 0")["restricoes"],
           ["x - 1 != 0"])

    for nome, s1, s2, esperado in [
        ("mesma solução", ["x + y = 3", "x - y = 1"], ["2x = 4", "y = 1"],
         "correct"),
        ("solução diferente", ["x + y = 3", "x - y = 1"],
         ["x + y = 3", "x - y = 2"], "incorrect"),
        ("ambos impossíveis", ["x + y = 1", "x + y = 2"],
         ["x = 1", "x = 2"], "correct"),
        ("não linear", ["x² + y = 1"], ["y = 1 - x²"], "indeterminate"),
        ("com restrição de domínio", ["1/x = y"], ["1/x = y"],
         "indeterminate"),
        ("equação sem igualdade", ["x + y"], ["x = 1"], "invalid"),
        ("não é lista", "x = 1", ["x = 1"], "invalid"),
    ]:
        testar(
            f"interface sistemas: {nome}",
            status_de(avaliar_equivalencia_sistemas, s1, s2),
            esperado
        )

    testar("interface sistemas paramétricos: equação multiplicada",
           lambda: avaliar_equivalencia_sistemas(
               ["a*x + y = 1", "x + a*y = 1"],
               ["2*a*x + 2*y = 2", "x + a*y = 1"],
               incognitas=["x", "y"])["status"]
           in ("correct", "conditional"),
           True)
    testar("interface sistemas paramétricos: termo alterado",
           status_de(avaliar_equivalencia_sistemas,
                     ["a*x + y = 1", "x + a*y = 1"],
                     ["a*x + y = 1", "x + a*y = 2"],
                     incognitas=["x", "y"]),
           "conditional")
    testar("interface sistemas paramétricos: parâmetros reportados",
           lambda: avaliar_equivalencia_sistemas(
               ["a*x + y = 1", "x + a*y = 1"],
               ["a*x + y = 1", "x + a*y = 2"],
               incognitas=["x", "y"])["detalhes"]["parametros"],
           ["a"])

    testar("interface domínio: denominador",
           lambda: analisar_dominio_expressao("1/(x - 3)")["restricoes"],
           ["x - 3 != 0"])
    testar("interface domínio: radical",
           lambda: analisar_dominio_expressao("sqrt(x - 2)")["restricoes"],
           ["x - 2 >= 0"])
    testar("interface domínio: conjunto",
           lambda: analisar_dominio_expressao(
               "sqrt(x - 2)")["detalhes"]["dominio"], "Interval(2, oo)")
    testar("interface domínio: entrada inválida",
           status_de(analisar_dominio_expressao, "sqrt(-4)"), "invalid")

    # Todos os resultados precisam ser serializáveis em JSON.
    def serializavel(resultado):
        json.dumps(resultado)
        return True

    for nome, chamada in [
        ("expressões", lambda: avaliar_equivalencia_expressoes(
            "x/x", "1")),
        ("equações", lambda: avaliar_equivalencia_equacoes(
            "(x² - 1)/(x - 1) = 0", "x + 1 = 0")),
        ("sistemas", lambda: avaliar_equivalencia_sistemas(
            ["a*x + y = 1", "x + a*y = 1"],
            ["a*x + y = 1", "x + a*y = 2"],
            incognitas=["x", "y"])),
        ("domínio", lambda: analisar_dominio_expressao("sqrt(x - 2)")),
    ]:
        testar(
            f"interface serializável em JSON: {nome}",
            lambda c=chamada: serializavel(c()),
            True
        )

    # ------------------------------------------------------------
    # Etapa 7: resolução de equações
    # ------------------------------------------------------------
    for nome, equacao, tipo, solucoes in [
        ("linear", "2x + 6 = 10", "finito", ["2"]),
        ("quadrática com duas raízes", "x² = 4", "finito", ["-2", "2"]),
        ("quadrática completa", "x² - 5x + 6 = 0", "finito", ["2", "3"]),
        ("raiz irracional", "x² = 2", "finito", ["-sqrt(2)", "sqrt(2)"]),
        ("cúbica", "x³ - x = 0", "finito", ["-1", "0", "1"]),
        ("sem solução real", "x² + 1 = 0", "vazio", []),
        ("contradição", "x + 1 = x + 2", "vazio", []),
        ("raiz quadrada", "sqrt(x) = 2", "finito", ["4"]),
        ("raiz com solução extra", "sqrt(x + 1) = x - 1", "finito", ["3"]),
        ("módulo", "abs(x) = 2", "finito", ["-2", "2"]),
        ("módulo impossível", "abs(x) = -1", "vazio", []),
        ("racional", "1/(x - 3) = 1", "finito", ["4"]),
        ("racional com solução proibida",
         "(x² - 1)/(x - 1) = 2", "vazio", []),
        ("racional com solução válida",
         "(x² - 1)/(x - 1) = 0", "finito", ["-1"]),
        ("identidade", "x + 1 = x + 1", "infinito", []),
        ("identidade com domínio", "x/x = 1", "infinito", []),
    ]:
        testar(
            f"resolver: {nome} (tipo)",
            lambda e=equacao: resolver_equacao(e)["detalhes"]["tipo"],
            tipo
        )
        testar(
            f"resolver: {nome} (soluções)",
            lambda e=equacao: resolver_equacao(e)["detalhes"]["solucoes"],
            solucoes
        )

    testar("resolver: quantidade de soluções",
           lambda: resolver_equacao("x² = 4")["detalhes"]["quantidade"], 2)
    testar("resolver: quantidade no caso vazio",
           lambda: resolver_equacao("x² + 1 = 0")["detalhes"]["quantidade"],
           0)
    testar("resolver: quantidade no caso infinito",
           lambda: resolver_equacao(
               "x + 1 = x + 1")["detalhes"]["quantidade"], None)
    testar("resolver: solução descartada pelo domínio",
           lambda: resolver_equacao(
               "(x² - 1)/(x - 1) = 2")["detalhes"]["descartadas_por_dominio"],
           ["1"])
    testar("resolver: restrições",
           lambda: resolver_equacao("1/(x - 3) = 1")["restricoes"],
           ["x - 3 != 0"])
    testar("resolver: status de sucesso",
           lambda: resolver_equacao("x² = 4")["status"], "correct")
    testar("resolver: duas variáveis",
           status_de(resolver_equacao, "x + y = 1"), "indeterminate")
    testar("resolver: sem variáveis",
           status_de(resolver_equacao, "1 = 1"), "indeterminate")
    testar("resolver: sem sinal de igualdade",
           status_de(resolver_equacao, "x + 1"), "invalid")
    testar("resolver: serializável em JSON",
           lambda: serializavel(resolver_equacao("sqrt(x + 1) = x - 1")),
           True)

    testar("equivalência: ambas sem solução real",
           status_de(avaliar_equivalencia_equacoes,
                     "x² + 1 = 0", "x² + 2 = 0"),
           "correct")

    for nome, equacao, valor, esperado, motivo in [
        ("solução positiva", "x² = 4", "2", "correct", None),
        ("solução negativa", "x² = 4", "-2", "correct", None),
        ("não é solução", "x² = 4", "3", "incorrect", "nao_satisfaz"),
        ("fração", "2x = 1", "1/2", "correct", None),
        ("vírgula decimal", "2x = 3", "1,5", "correct", None),
        ("irracional", "x² = 2", "sqrt(2)", "correct", None),
        ("fora do domínio (denominador)",
         "(x² - 1)/(x - 1) = 2", "1", "incorrect", "fora_do_dominio"),
        ("fora do domínio (radical)",
         "sqrt(x) = 2", "-4", "incorrect", "fora_do_dominio"),
        ("raiz válida", "sqrt(x) = 2", "4", "correct", None),
        ("identidade", "x + 1 = x + 1", "7", "correct", None),
        ("número em vez de texto", "x = 5", 5, "correct", None),
        ("valor não numérico", "x = 1", "y", "invalid", None),
        ("duas variáveis", "x + y = 1", "1", "indeterminate", None),
    ]:
        testar(
            f"verificar solução: {nome}",
            status_de(verificar_solucao_equacao, equacao, valor),
            esperado
        )

        if motivo is not None:
            testar(
                f"verificar solução: {nome} (motivo)",
                lambda e=equacao, v=valor: verificar_solucao_equacao(
                    e, v)["detalhes"]["motivo"],
                motivo
            )

    # ------------------------------------------------------------
    # Etapa 6: verificação de transformações
    # ------------------------------------------------------------
    for nome, ant, novo, status, tipo in [
        # Expressões
        ("expansão", "(x + 2)(x + 3)", "x² + 5x + 6",
         "correct", "equivalente"),
        ("fatoração", "x² - 9", "(x - 3)(x + 3)",
         "correct", "equivalente"),
        ("simplificação", "(2x + 4)/2", "x + 2",
         "correct", "equivalente"),
        ("cancelar x/x", "x/x", "1",
         "conditional", "valida_sob_condicoes"),
        ("cancelar fator comum", "(x² - 1)/(x - 1)", "x + 1",
         "conditional", "valida_sob_condicoes"),
        ("erro de expansão", "(x + 1)²", "x² + 1",
         "incorrect", "nao_equivalente"),
        ("raiz do quadrado", "sqrt(x²)", "x",
         "incorrect", "nao_equivalente"),
        ("erro de sinal", "x - (y - 1)", "x - y - 1",
         "incorrect", "nao_equivalente"),
        # Equações
        ("distributiva", "2(x + 3) = 10", "2x + 6 = 10",
         "correct", "equivalente"),
        ("isolar termos", "2x + 6 = 10", "2x = 4",
         "correct", "equivalente"),
        ("dividir por constante", "2x = 4", "x = 2",
         "correct", "equivalente"),
        ("racional com domínio", "(x² - 1)/(x - 1) = 0", "x + 1 = 0",
         "correct", "equivalente"),
        ("ambas sem solução real", "x² + 1 = 0", "x² + 2 = 0",
         "correct", "equivalente"),
        ("equação com raiz", "sqrt(x) = 2", "x = 4",
         "correct", "equivalente"),
        ("multiplicar por x", "x = 2", "x² = 2x",
         "conditional", "solucoes_extras"),
        ("elevar ao quadrado", "sqrt(x + 1) = x - 1", "x + 1 = (x - 1)²",
         "conditional", "solucoes_extras"),
        ("solução fora do domínio", "(x² - 1)/(x - 1) = 2", "x + 1 = 2",
         "conditional", "solucoes_extras"),
        ("perde solução", "x² = 9", "x = 3",
         "incorrect", "perda_de_solucoes"),
        ("dividir por x", "x² = 2x", "x = 2",
         "incorrect", "perda_de_solucoes"),
        ("troca de constante", "x² = 4", "x² = 9",
         "incorrect", "perda_e_solucoes_extras"),
        ("duas variáveis equivalentes", "x + y = 1", "y = 1 - x",
         "correct", "equivalente"),
        ("duas variáveis diferentes", "x + y = 1", "x - y = 0",
         "incorrect", "nao_equivalente"),
    ]:
        testar(
            f"transformação: {nome} (status)",
            status_de(verificar_transformacao, ant, novo),
            status
        )
        testar(
            f"transformação: {nome} (tipo)",
            lambda a=ant, n=novo: verificar_transformacao(
                a, n)["detalhes"]["tipo"],
            tipo
        )

    testar("transformação: condição de x/x",
           lambda: verificar_transformacao("x/x", "1")["condicoes"],
           ["x != 0"])
    testar("transformação: contraexemplo de sqrt(x²) = x",
           lambda: verificar_transformacao(
               "sqrt(x²)", "x")["detalhes"]["contraexemplo"],
           {"ponto": {"x": "-1"}, "valor_anterior": "1",
            "valor_novo": "-1"})
    testar("transformação: contraexemplo de (x+1)² = x²+1",
           lambda: verificar_transformacao(
               "(x + 1)²", "x² + 1")["detalhes"]["contraexemplo"],
           {"ponto": {"x": "1"}, "valor_anterior": "4",
            "valor_novo": "2"})

    for nome, ant, novo, perdidas, extras in [
        ("perde -3", "x² = 9", "x = 3", ["-3"], []),
        ("extra 0", "x = 2", "x² = 2x", [], ["0"]),
        ("perde 0", "x² = 2x", "x = 2", ["0"], []),
        ("extra proibida pelo domínio",
         "(x² - 1)/(x - 1) = 2", "x + 1 = 2", [], ["1"]),
        ("perde e introduz", "x² = 4", "x² = 9",
         ["-2", "2"], ["-3", "3"]),
    ]:
        testar(
            f"transformação: {nome} (soluções perdidas)",
            lambda a=ant, n=novo: verificar_transformacao(
                a, n)["detalhes"]["solucoes_perdidas"],
            perdidas
        )
        testar(
            f"transformação: {nome} (soluções extras)",
            lambda a=ant, n=novo: verificar_transformacao(
                a, n)["detalhes"]["solucoes_extras"],
            extras
        )

    for nome, ant, novo in [
        ("expressão inválida", "2 +", "2"),
        ("expressão para equação", "x + 1", "x = 1"),
        ("equação incompleta", "x² =", "x = 1"),
    ]:
        testar(
            f"transformação inválida: {nome}",
            status_de(verificar_transformacao, ant, novo),
            "invalid"
        )

    testar("transformação: serializável (equação)",
           lambda: serializavel(verificar_transformacao("x² = 9", "x = 3")),
           True)
    testar("transformação: serializável (contraexemplo)",
           lambda: serializavel(verificar_transformacao("sqrt(x²)", "x")),
           True)

    # ------------------------------------------------------------
    # Etapa 8: análise de procedimentos
    # ------------------------------------------------------------
    def procedimento(etapas):
        return analisar_procedimento(etapas)

    resolucao_correta = [
        "2(x + 3) = 10", "2x + 6 = 10", "2x = 4", "x = 2"
    ]

    # Erro na etapa 2 (2x + 3 em vez de 2x + 6); as etapas 3 e 4
    # estão corretas a partir do resultado errado.
    resolucao_com_erro = [
        "2(x + 3) = 10", "2x + 3 = 10", "2x = 7", "x = 7/2"
    ]

    resolucao_com_extras = [
        "sqrt(x + 1) = x - 1", "x + 1 = (x - 1)²",
        "x² - 3x = 0", "x(x - 3) = 0"
    ]

    expressao_correta = [
        "(x + 2)(x + 3)", "x² + 3x + 2x + 6", "x² + 5x + 6"
    ]

    expressao_com_erro = ["(x + 1)²", "x² + 1", "x² + 1 + 0"]

    linha_ilegivel = ["2x + 6 = 10", "2x ==", "x = 2"]

    # Procedimento correto
    testar("procedimento correto: status",
           lambda: procedimento(resolucao_correta)["status"], "correct")
    testar("procedimento correto: contagem",
           lambda: procedimento(resolucao_correta)["detalhes"][
               "contagem"]["correct"], 3)
    testar("procedimento correto: sem erro",
           lambda: procedimento(resolucao_correta)["detalhes"][
               "primeiro_erro"], None)
    testar("procedimento correto: coerência global",
           lambda: procedimento(resolucao_correta)["detalhes"][
               "equivalencia_global"]["status"], "correct")
    testar("procedimento de expressões correto",
           lambda: procedimento(expressao_correta)["status"], "correct")

    # Procedimento com erro e crédito parcial
    testar("procedimento com erro: status",
           lambda: procedimento(resolucao_com_erro)["status"], "incorrect")
    testar("procedimento com erro: primeiro erro",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "primeiro_erro"], 2)
    testar("procedimento com erro: etapas incorretas",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "etapas_incorretas"], [2])
    testar("procedimento com erro: corretas após o erro",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "corretas_apos_erro"], [3, 4])
    testar("procedimento com erro: marcação de apos_erro",
           lambda: [t["apos_erro"] for t in procedimento(
               resolucao_com_erro)["detalhes"]["transformacoes"]],
           [False, True, True])
    testar("procedimento com erro: status por etapa",
           lambda: [t["resultado"]["status"] for t in procedimento(
               resolucao_com_erro)["detalhes"]["transformacoes"]],
           ["incorrect", "correct", "correct"])
    testar("procedimento com erro: tipo do erro",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "transformacoes"][0]["resultado"]["detalhes"]["tipo"],
           "perda_e_solucoes_extras")
    testar("procedimento com erro: numeração das etapas",
           lambda: [t["etapa"] for t in procedimento(
               resolucao_com_erro)["detalhes"]["transformacoes"]],
           [2, 3, 4])
    testar("procedimento com erro: coerência global",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "equivalencia_global"]["status"], "incorrect")
    testar("procedimento de expressões com erro",
           lambda: procedimento(expressao_com_erro)["detalhes"][
               "corretas_apos_erro"], [3])

    # Procedimento com soluções extras
    testar("procedimento com extras: status",
           lambda: procedimento(resolucao_com_extras)["status"],
           "conditional")
    testar("procedimento com extras: contagem de condicionais",
           lambda: procedimento(resolucao_com_extras)["detalhes"][
               "contagem"]["conditional"], 1)
    testar("procedimento com extras: contagem de corretas",
           lambda: procedimento(resolucao_com_extras)["detalhes"][
               "contagem"]["correct"], 2)
    testar("procedimento com extras: sem erro",
           lambda: procedimento(resolucao_com_extras)["detalhes"][
               "primeiro_erro"], None)
    testar("procedimento com extras: coerência global",
           lambda: procedimento(resolucao_com_extras)["detalhes"][
               "equivalencia_global"]["tipo"], "solucoes_extras")

    # Linha ilegível
    testar("linha ilegível: status geral",
           lambda: procedimento(linha_ilegivel)["status"], "indeterminate")
    testar("linha ilegível: contagem de inválidas",
           lambda: procedimento(linha_ilegivel)["detalhes"][
               "contagem"]["invalid"], 2)
    testar("linha ilegível: aponta a etapa culpada",
           lambda: [t["resultado"]["detalhes"]["etapa_invalida"]
                    for t in procedimento(
                        linha_ilegivel)["detalhes"]["transformacoes"]],
           [2, 2])
    testar("linha ilegível: ainda compara início e fim",
           lambda: procedimento(linha_ilegivel)["detalhes"][
               "equivalencia_global"]["status"], "correct")

    # Entrada inválida
    for nome, entrada in [
        ("lista vazia", []),
        ("uma só etapa", ["x = 1"]),
        ("não é lista", "x = 1"),
        ("etapas demais", ["x = 1"] * 31),
    ]:
        testar(
            f"procedimento inválido: {nome}",
            status_de(analisar_procedimento, entrada),
            "invalid"
        )

    testar("procedimento com etapa não textual",
           status_de(analisar_procedimento, ["x = 1", 5]), "indeterminate")

    testar("procedimento: serializável em JSON (com erro)",
           lambda: serializavel(procedimento(resolucao_com_erro)), True)
    testar("procedimento: serializável em JSON (linha ilegível)",
           lambda: serializavel(procedimento(linha_ilegivel)), True)
    testar("procedimento: restrições reunidas",
           lambda: procedimento(
               ["(x² - 1)/(x - 1) = 0", "x + 1 = 0", "x = -1"])[
                   "restricoes"], ["x - 1 != 0"])
    testar("transformação: restrições (uma variável)",
           lambda: verificar_transformacao(
               "(x² - 1)/(x - 1) = 0", "x + 1 = 0")["restricoes"],
           ["x - 1 != 0"])
    testar("transformação: restrições em soluções extras",
           lambda: verificar_transformacao(
               "(x² - 1)/(x - 1) = 2", "x + 1 = 2")["restricoes"],
           ["x - 1 != 0"])
    testar("transformação: sem restrições",
           lambda: verificar_transformacao("2x = 4", "x = 2")["restricoes"],
           [])

    # ------------------------------------------------------------
    # Etapa 9: diagnóstico de erros
    # ------------------------------------------------------------
    def diagnostico_de(anterior, novo):
        return diagnosticar_transformacao(
            anterior, novo)["detalhes"]["diagnostico"]

    for nome, ant, novo, categoria in [
        # Expressões
        ("aritmético", "2 + 3", "6", "erro_aritmetico"),
        ("sinal", "x - (y - 1)", "x - y - 1", "erro_de_sinal"),
        ("coeficiente", "x + 1", "x + 2", "erro_de_coeficiente"),
        ("expansão", "(x + 1)²", "x² + 1", "erro_de_expansao"),
        ("expansão com coeficiente", "(x + 2)(x + 3)", "x² + 5x + 5",
         "erro_de_expansao"),
        ("fatoração", "x² - 9", "(x - 3)²", "erro_de_fatoracao"),
        ("propriedade da raiz", "sqrt(x²)", "x", "erro_de_propriedade"),
        ("módulo removido", "abs(x)", "x", "erro_de_propriedade"),
        ("termo omitido", "x² + 2x + 1", "x² + 1", "termos_omitidos"),
        ("termo extra", "x² + 1", "x² + 1 + y", "termos_extras"),
        ("restrição de domínio", "x/x", "1", "restricao_de_dominio"),
        # Equações
        ("fator cancelado (x+3)", "x² = 9", "x = 3", "fator_cancelado"),
        ("fator cancelado (x)", "x² = 2x", "x = 2", "fator_cancelado"),
        ("multiplicação por x", "x = 2", "x² = 2x",
         "multiplicacao_por_fator"),
        ("elevação ao quadrado", "sqrt(x + 1) = x - 1",
         "x + 1 = (x - 1)²", "elevacao_ao_quadrado"),
        ("solução fora do domínio", "(x² - 1)/(x - 1) = 2", "x + 1 = 2",
         "erro_de_dominio"),
        ("perde e introduz", "x² = 4", "x² = 9",
         "perda_e_solucoes_extras"),
    ]:
        testar(
            f"diagnóstico: {nome} (categoria)",
            lambda a=ant, n=novo: diagnostico_de(a, n)["categoria"],
            categoria
        )
        testar(
            f"diagnóstico: {nome} (específico)",
            lambda a=ant, n=novo: diagnostico_de(a, n)["especifico"],
            categoria != "perda_e_solucoes_extras"
        )

    # Evidências
    testar("diagnóstico: evidência do sinal",
           lambda: diagnostico_de("x - (y - 1)", "x - y - 1")[
               "evidencias"]["termos_com_sinal_invertido"], ["1"])
    testar("diagnóstico: evidência do coeficiente",
           lambda: diagnostico_de("x + 1", "x + 2")[
               "evidencias"]["termos_alterados"], ["1 -> 2"])
    testar("diagnóstico: termo omitido na expansão",
           lambda: diagnostico_de("(x + 1)²", "x² + 1")[
               "evidencias"]["termos_omitidos"], ["2*x"])
    testar("diagnóstico: coeficiente errado na expansão",
           lambda: diagnostico_de("(x + 2)(x + 3)", "x² + 5x + 5")[
               "evidencias"]["termos_alterados"], ["6 -> 5"])
    testar("diagnóstico: expansão do resultado na fatoração",
           lambda: diagnostico_de("x² - 9", "(x - 3)²")[
               "evidencias"]["expansao_do_resultado"], "x**2 - 6*x + 9")
    testar("diagnóstico: valores do erro aritmético",
           lambda: diagnostico_de("2 + 3", "6")["evidencias"],
           {"valor_anterior": "5", "valor_apresentado": "6"})
    testar("diagnóstico: condições do domínio",
           lambda: diagnostico_de("x/x", "1")["evidencias"]["condicoes"],
           ["x != 0"])
    testar("diagnóstico: fator cancelado",
           lambda: diagnostico_de("x² = 9", "x = 3")["evidencias"]["fator"],
           "x + 3")
    testar("diagnóstico: soluções perdidas",
           lambda: diagnostico_de("x² = 9", "x = 3")[
               "evidencias"]["solucoes_perdidas"], ["-3"])
    testar("diagnóstico: fator multiplicado",
           lambda: diagnostico_de("x = 2", "x² = 2x")[
               "evidencias"]["fator"], "x")
    testar("diagnóstico: soluções extras",
           lambda: diagnostico_de("x = 2", "x² = 2x")[
               "evidencias"]["solucoes_extras"], ["0"])
    testar("diagnóstico: solução fora do domínio (extras)",
           lambda: diagnostico_de("(x² - 1)/(x - 1) = 2", "x + 1 = 2")[
               "evidencias"]["solucoes_extras"], ["1"])
    testar("diagnóstico: restrição da equação anterior",
           lambda: diagnostico_de("(x² - 1)/(x - 1) = 2", "x + 1 = 2")[
               "evidencias"]["restricoes_da_equacao_anterior"],
           ["x - 1 != 0"])

    # Casos sem causa comprovável: descrição genérica
    for nome, ant, novo in [
        ("expressão racional", "1/x", "2/x"),
        ("duas variáveis", "x + y = 1", "x - y = 0"),
    ]:
        testar(
            f"diagnóstico genérico: {nome} (categoria)",
            lambda a=ant, n=novo: diagnostico_de(a, n)["categoria"],
            "transformacao_invalida"
        )
        testar(
            f"diagnóstico genérico: {nome} (específico)",
            lambda a=ant, n=novo: diagnostico_de(a, n)["especifico"],
            False
        )

    # Transformações sem diagnóstico
    for nome, ant, novo in [
        ("correta (expressão)", "(x + 2)(x + 3)", "x² + 5x + 6"),
        ("correta (equação)", "2x = 4", "x = 2"),
        ("inválida", "2 +", "2"),
    ]:
        testar(
            f"sem diagnóstico: {nome}",
            lambda a=ant, n=novo: diagnostico_de(a, n),
            None
        )

    testar("diagnóstico: status preservado",
           status_de(diagnosticar_transformacao, "x² = 9", "x = 3"),
           "incorrect")
    testar("diagnóstico: serializável em JSON",
           lambda: serializavel(
               diagnosticar_transformacao("x² = 9", "x = 3")), True)

    # Integração com a análise de procedimentos
    testar("procedimento: diagnóstico do passo errado",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "transformacoes"][0]["diagnostico"]["categoria"],
           "perda_e_solucoes_extras")
    testar("procedimento: passo correto sem diagnóstico",
           lambda: procedimento(resolucao_com_erro)["detalhes"][
               "transformacoes"][1]["diagnostico"], None)
    testar("procedimento: diagnóstico do passo condicional",
           lambda: procedimento(resolucao_com_extras)["detalhes"][
               "transformacoes"][0]["diagnostico"]["categoria"],
           "elevacao_ao_quadrado")
    testar("procedimento de expressões: diagnóstico do erro",
           lambda: procedimento(expressao_com_erro)["detalhes"][
               "transformacoes"][0]["diagnostico"]["categoria"],
           "erro_de_expansao")
    testar("procedimento: serializável com diagnóstico",
           lambda: serializavel(procedimento(resolucao_com_extras)), True)

    # ------------------------------------------------------------
    # Etapa 10: controle de tempo
    # Os auxiliares _auxiliar_* ficam no nível do módulo.
    # ------------------------------------------------------------
    import time

    # Configuração inválida
    for nome, valor in [
        ("negativo", -1),
        ("zero", 0),
        ("texto", "5"),
        ("booleano", True),
        ("infinito", float("inf")),
        ("não numérico", float("nan")),
    ]:
        testar_erro(
            f"limite de tempo inválido: {nome}",
            lambda v=valor: configurar_limite_de_tempo(v)
        )

    configurar_limite_de_tempo(2.5)
    testar("limite efetivo com fator",
           lambda: _limite_efetivo(4), 10.0)

    # Sem isolamento
    configurar_limite_de_tempo(None)

    testar("limite desativado",
           lambda: _limite_efetivo(4), None)
    testar("sem limite: execução direta",
           lambda: _auxiliar_lento_para_teste(0.01)["status"], "correct")
    testar("sem limite: erro interno contido",
           lambda: _auxiliar_com_erro_para_teste()["detalhes"],
           {"erro_interno": "ZeroDivisionError",
            "mensagem_do_erro": "division by zero"})

    resultado_direto = resolver_equacao("x² = 4")

    # Com isolamento
    configurar_limite_de_tempo(10.0)

    testar("com limite: execução normal",
           lambda: _auxiliar_lento_para_teste(0.01)["status"], "correct")
    testar("com limite: resultado verdadeiro",
           lambda: _auxiliar_lento_para_teste(0.01)["resultado"], True)
    testar("com limite: erro interno contido",
           lambda: _auxiliar_com_erro_para_teste()["detalhes"],
           {"erro_interno": "ZeroDivisionError",
            "mensagem_do_erro": "division by zero"})
    testar("com limite: queda do processo contida",
           lambda: _auxiliar_que_derruba_o_processo()["detalhes"][
               "erro_interno"], "ProcessoEncerrado")
    testar("com limite: mesmo resultado que sem limite",
           lambda: resolver_equacao("x² = 4") == resultado_direto, True)

    # A partida do processo não conta no limite
    configurar_limite_de_tempo(1.0)
    testar("partida do processo não conta no limite",
           lambda: _auxiliar_lento_para_teste(0.3)["status"], "correct")

    # Tempo excedido
    configurar_limite_de_tempo(0.5)

    inicio = time.perf_counter()
    resultado_lento = _auxiliar_lento_para_teste(60)
    duracao = time.perf_counter() - inicio

    testar("tempo excedido: status",
           lambda: resultado_lento["status"], "indeterminate")
    testar("tempo excedido: resultado nulo",
           lambda: resultado_lento["resultado"], None)
    testar("tempo excedido: motivo",
           lambda: resultado_lento["detalhes"]["motivo"], "tempo_excedido")
    testar("tempo excedido: limite informado",
           lambda: resultado_lento["detalhes"]["limite_segundos"], 0.5)
    testar("tempo excedido: interrompido bem antes do fim do cálculo",
           lambda: duracao < 30, True)
    testar("tempo excedido: sem processos remanescentes",
           lambda: len(multiprocessing.active_children()), 0)
    testar("tempo excedido: serializável em JSON",
           lambda: serializavel(resultado_lento), True)

    configurar_limite_de_tempo(10.0)

    # ------------------------------------------------------------
    # Etapa 11: verificação numérica
    # ------------------------------------------------------------
    def numerico(esperado, apresentado, **regra):
        return comparar_resultado_numerico(esperado, apresentado, **regra)

    for nome, esp, apr, regra, status, tipo in [
        # Igualdade exata
        ("fração e decimal com vírgula", "1/2", "0,5", {},
         "correct", "exato"),
        ("decimal e fração", "0.5", "1/2", {}, "correct", "exato"),
        ("frações equivalentes", "2/4", "1/2", {}, "correct", "exato"),
        ("radical", "sqrt(2)*sqrt(2)", "2", {}, "correct", "exato"),
        ("notação científica", "1e-3", "0,001", {}, "correct", "exato"),
        ("notação científica com vírgula", "1,5e2", "150", {},
         "correct", "exato"),
        ("negativos", "-0,5", "-1/2", {}, "correct", "exato"),
        ("números Python", 0.5, 0.5, {}, "correct", "exato"),
        ("inteiro e decimal", 1, 1.0, {}, "correct", "exato"),
        # Aproximação sem regra
        ("1/3 e 0,333333", "1/3", "0,333333", {},
         "conditional", "aproximado_sem_regra"),
        ("arredondamento", "2/3", "0,67", {},
         "conditional", "aproximado_sem_regra"),
        ("truncamento", "2/3", "0,66", {},
         "conditional", "aproximado_sem_regra"),
        ("uma casa", "2/3", "0,7", {},
         "conditional", "aproximado_sem_regra"),
        ("radical aproximado", "sqrt(2)", "1,4142", {},
         "conditional", "aproximado_sem_regra"),
        ("esperado decimal, resposta fração", "3,14", "22/7", {},
         "conditional", "aproximado_sem_regra"),
        ("esperado decimal, resposta exata", "0,333333", "1/3", {},
         "conditional", "aproximado_sem_regra"),
        # Incompatíveis
        ("decimal errado", "2/3", "0,68", {}, "incorrect", "incompativel"),
        ("decimal errado 1/3", "1/3", "0,34", {},
         "incorrect", "incompativel"),
        ("inteiro não é aproximação", "1/3", "0", {},
         "incorrect", "incompativel"),
        ("outra fração", "1/3", "1/4", {}, "incorrect", "incompativel"),
        ("radical errado", "sqrt(2)", "1,4143", {},
         "incorrect", "incompativel"),
        ("dois decimais diferentes", "3,14", "3,15", {},
         "incorrect", "incompativel"),
        # Casas decimais
        ("2 casas", "1/3", "0,33", {"casas_decimais": 2},
         "correct", "arredondado_conforme_regra"),
        ("2 casas, arredondado", "2/3", "0,67", {"casas_decimais": 2},
         "correct", "arredondado_conforme_regra"),
        ("4 casas", "2/3", "0,6667", {"casas_decimais": 4},
         "correct", "arredondado_conforme_regra"),
        ("truncado quando exige arredondamento", "2/3", "0,66",
         {"casas_decimais": 2}, "incorrect", "incompativel"),
        ("truncamento permitido", "2/3", "0,66",
         {"casas_decimais": 2, "modo_arredondamento": "truncamento"},
         "correct", "arredondado_conforme_regra"),
        ("qualquer modo (truncado)", "2/3", "0,66",
         {"casas_decimais": 2, "modo_arredondamento": "qualquer"},
         "correct", "arredondado_conforme_regra"),
        ("qualquer modo (arredondado)", "2/3", "0,67",
         {"casas_decimais": 2, "modo_arredondamento": "qualquer"},
         "correct", "arredondado_conforme_regra"),
        ("mais casas que o exigido", "1/3", "0,333",
         {"casas_decimais": 2}, "incorrect", "incompativel"),
        ("exato continua valendo com regra", "1/2", "0,5",
         {"casas_decimais": 2}, "correct", "exato"),
        # Tolerância
        ("tolerância absoluta", "1/3", "0,33",
         {"tolerancia_absoluta": 0.01},
         "correct", "dentro_da_tolerancia"),
        ("fora da tolerância absoluta", "1/3", "0,33",
         {"tolerancia_absoluta": 0.001}, "incorrect", "incompativel"),
        ("tolerância relativa", "100", "101",
         {"tolerancia_relativa": 0.02},
         "correct", "dentro_da_tolerancia"),
        ("fora da tolerância relativa", "100", "101",
         {"tolerancia_relativa": 0.005}, "incorrect", "incompativel"),
        ("tolerância com radical", "sqrt(2)", "1,41",
         {"tolerancia_absoluta": 0.01},
         "correct", "dentro_da_tolerancia"),
    ]:
        testar(
            f"numérico: {nome} (status)",
            lambda e=esp, a=apr, r=regra: numerico(e, a, **r)["status"],
            status
        )
        testar(
            f"numérico: {nome} (tipo)",
            lambda e=esp, a=apr, r=regra: numerico(
                e, a, **r)["detalhes"]["tipo"],
            tipo
        )

    # Modos de aproximação reconhecidos
    for nome, esp, apr, modos in [
        ("ambos", "1/3", "0,333333", ["arredondamento", "truncamento"]),
        ("só arredondamento", "2/3", "0,67", ["arredondamento"]),
        ("só truncamento", "2/3", "0,66", ["truncamento"]),
    ]:
        testar(
            f"numérico: modos compatíveis ({nome})",
            lambda e=esp, a=apr: numerico(
                e, a)["detalhes"]["modos_compativeis"],
            modos
        )

    testar("numérico: lado aproximado (apresentado)",
           lambda: numerico("1/3", "0,333333")["detalhes"][
               "lado_aproximado"], "apresentado")
    testar("numérico: lado aproximado (esperado)",
           lambda: numerico("3,14", "22/7")["detalhes"][
               "lado_aproximado"], "esperado")
    testar("numérico: casas do apresentado",
           lambda: numerico("1/3", "0,333333")["detalhes"][
               "casas_decimais_apresentadas"], 6)
    testar("numérico: condição de precisão pedida",
           lambda: numerico("1/3", "0,333333")["condicoes"],
           ["definir a regra de precisão (casas decimais ou tolerância)"])
    testar("numérico: valor esperado em decimal",
           lambda: numerico("1/3", "0,333333")["detalhes"][
               "valor_esperado_decimal"], "0.333333333333333")
    testar("numérico: resultado nulo no condicional",
           lambda: numerico("1/3", "0,333333")["resultado"], None)
    testar("numérico: resultado verdadeiro no exato",
           lambda: numerico("1/2", "0,5")["resultado"], True)
    testar("numérico: regra de casas registrada",
           lambda: numerico("1/3", "0,33", casas_decimais=2)["detalhes"][
               "regra"], {"casas_decimais": 2, "modo": "arredondamento"})
    testar("numérico: diferença relativa nula quando esperado é zero",
           lambda: numerico("0", "0,1")["detalhes"]["diferenca_relativa"],
           None)

    # Entradas inválidas
    for nome, esp, apr, regra in [
        ("variável", "x", "1", {}),
        ("divisão por zero", "1/0", "1", {}),
        ("constante não suportada", "pi", "3,14", {}),
        ("texto livre", "1/3", "aproximadamente 0,33", {}),
        ("expoente fora do intervalo", "1/3", "1e999", {}),
        ("tolerância negativa", "1/3", "0,3", {"tolerancia_absoluta": -1}),
        ("casas fora do intervalo", "1/3", "0,3", {"casas_decimais": 51}),
        ("casas booleanas", "1/3", "0,3", {"casas_decimais": True}),
        ("tolerância e casas", "1/3", "0,3",
         {"tolerancia_absoluta": 0.1, "casas_decimais": 2}),
        ("modo desconhecido", "1/3", "0,3",
         {"casas_decimais": 2, "modo_arredondamento": "aproximado"}),
        ("valor booleano", True, "1", {}),
        ("espaço dentro do número", "1 000", "1000", {}),
    ]:
        testar(
            f"numérico inválido: {nome}",
            lambda e=esp, a=apr, r=regra: numerico(e, a, **r)["status"],
            "invalid"
        )

    testar("numérico: serializável em JSON (condicional)",
           lambda: serializavel(numerico("1/3", "0,333333")), True)
    testar("numérico: serializável em JSON (com regra)",
           lambda: serializavel(
               numerico("1/3", "0,33", tolerancia_absoluta=0.01)), True)
    # ------------------------------------------------------------
    # Limitações conhecidas (não contam como falha)
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # Relatório
    # ------------------------------------------------------------
    total = contagem["total"]
    print(f"{total - len(falhas)}/{total} testes passaram.")

    for falha in falhas:
        print("FALHA:", falha)

    print("\nLimitações conhecidas (não contam como falha):")

    for descricao, ok in pendencias:
        print(("  [resolvido] " if ok else "  [pendente]  ") + descricao)

    raise SystemExit(1 if falhas else 0)
