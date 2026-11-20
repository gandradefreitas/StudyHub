from models.questao_discursiva import ProvaDiscursiva


def validar_prova_discursiva(prova: ProvaDiscursiva) -> list[str]:
    erros = []

    if not prova.questoes:
        erros.append("A prova não possui questões.")

    numeros_questoes = [
        questao.numero for questao in prova.questoes
    ]

    if len(numeros_questoes) != len(set(numeros_questoes)):
        erros.append("Existem números de questões duplicados.")

    for questao in prova.questoes:

        if not questao.itens:
            erros.append(
                f"Questão {questao.numero}: não possui itens."
            )
            continue

        for item in questao.itens:

            identificacao = f"Questão {questao.numero}"

            if item.letra:
                identificacao += f", item {item.letra}"

            if item.valor <= 0:
                erros.append(
                    f"{identificacao}: o valor do item deve ser positivo."
                )

            if not item.criterios_correcao:
                erros.append(
                    f"{identificacao}: não possui critérios de correção."
                )
                continue

            soma_pontos = sum(
                criterio.pontos
                for criterio in item.criterios_correcao
            )

            for criterio in item.criterios_correcao:
                if criterio.pontos <= 0:
                    erros.append(
                        f"{identificacao}: o critério "
                        f"'{criterio.criterio}' deve ter pontuação positiva."
                    )

            if soma_pontos > item.valor:
                erros.append(
                    f"{identificacao}: os critérios somam "
                    f"{soma_pontos} pontos, mas o item vale "
                    f"{item.valor}."
                )

    return erros
