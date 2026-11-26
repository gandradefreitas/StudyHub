from unicodedata import normalize

FAIXAS_REDACAO = (0, 10, 20, 35, 50, 70, 95, 125, 160, 200)
EXP_QUESTOES = {"facil": 50, "medio": 100, "media": 100, "dificil": 200}


def exp_questao(dificuldade):
    chave = normalize("NFKD", (dificuldade or "").strip().lower()).encode("ascii", "ignore").decode()
    return EXP_QUESTOES.get(chave, 0)


def exp_redacao(nota, instituicao):
    # A aplicação guarda a nota do ITA em décimos (7,5 é armazenado como 75).
    maximo = 100 if instituicao == "ITA" else 1000
    if not 0 <= nota <= maximo:
        return 0
    largura = maximo // 10
    faixa = max(0, (nota - 1) // largura)
    return FAIXAS_REDACAO[faixa] * 10


def total_para_nivel(nivel):
    # Soma dos custos em décimos, do nível 0 até o nível anterior.
    return 10 * (100 * nivel + 10 * nivel * (nivel - 1)
                 + nivel * (nivel - 1) * (2 * nivel - 1) // 3)


def calcular_progresso(total):
    inferior, superior = 0, 1
    while total_para_nivel(superior) <= total:
        inferior, superior = superior, superior * 2
    while superior - inferior > 1:
        meio = (inferior + superior) // 2
        if total_para_nivel(meio) <= total:
            inferior = meio
        else:
            superior = meio

    acumulado = total_para_nivel(inferior)
    custo = total_para_nivel(inferior + 1) - acumulado
    return {
        "nivel": inferior,
        "proximo": inferior + 1,
        "progresso": total - acumulado,
        "necessario": custo,
    }
