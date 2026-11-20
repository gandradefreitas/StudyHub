import math


def validar_pontuacoes(resposta_ia):

    resultado = criar_resultado_validacao()

    for item in resposta_ia["itens"]:

        letra = item["letra"]
        pontos_maximos_item = item["pontos_maximos"]

        if (
                isinstance(pontos_maximos_item, bool)
                or not isinstance(pontos_maximos_item, (int, float))
                or not math.isfinite(pontos_maximos_item)
                or pontos_maximos_item <= 0
        ):
            resultado["erros"].append(
                f"Item {item['letra']}: pontuação máxima inválida."
            )
            continue

        soma_pontos_sugeridos = 0
        soma_pontos_maximos = 0

        for criterio in item["criterios"]:

            pontos_maximos = criterio["pontos_maximos"]
            pontos_sugeridos = criterio["pontos_sugeridos"]

            # Verifica se o valor máximo é numérico e finito
            if (
                    isinstance(pontos_maximos, bool)
                    or not isinstance(pontos_maximos, (int, float))
                    or not math.isfinite(pontos_maximos)
            ):
                resultado["erros"].append(
                    f"Item {letra}: valor máximo do critério inválido."
                )

                continue

            # Verifica se o valor máximo é positivo
            if pontos_maximos <= 0:
                resultado["erros"].append(
                    f"Item {letra}: valor máximo do critério "
                    f"deve ser maior que zero."
                )

                continue

            # Soma os valores máximos dos critérios
            soma_pontos_maximos += pontos_maximos

            # Critério não avaliável
            if pontos_sugeridos is None:
                continue

            # Verifica se o valor é numérico e finito
            if (
                isinstance(pontos_sugeridos, bool)
                or not isinstance(pontos_sugeridos, (int, float))
                or not math.isfinite(pontos_sugeridos)
            ):

                resultado["erros"].append(
                    f"Item {letra}: pontuação inválida."
                )

                continue

            # Verifica pontuação negativa
            if pontos_sugeridos < 0:

                resultado["erros"].append(
                    f"Item {letra}: pontuação negativa."
                )

            # Verifica limite individual
            if pontos_sugeridos > pontos_maximos:

                resultado["erros"].append(
                    f"Item {letra}: critério recebeu "
                    f"{pontos_sugeridos} pontos, mas o máximo "
                    f"é {pontos_maximos}."
                )

            soma_pontos_sugeridos += pontos_sugeridos

        # Verifica soma dos valores máximos dos critérios
        if not math.isclose(
            soma_pontos_maximos,
            pontos_maximos_item,
            rel_tol=1e-9,
            abs_tol=1e-9
        ):

            resultado["erros"].append(
                f"Item {letra}: a soma dos valores máximos "
                f"dos critérios ({soma_pontos_maximos}) é diferente "
                f"da pontuação máxima do item ({pontos_maximos_item})."
            )

    return resultado

def validar_criterios_originais(resposta_ia, questao_original):

    resultado = criar_resultado_validacao()

    itens_originais = {
        item["letra"]: item
        for item in questao_original["itens"]
    }

    itens_corrigidos = {
        item["letra"]: item
        for item in resposta_ia["itens"]
    }

    # Verifica se todos os itens originais foram avaliados
    for letra in itens_originais:

        if letra not in itens_corrigidos:

            resultado["erros"].append(
                f"Item {letra}: não foi incluído na correção."
            )

    # Verifica se a IA inventou itens
    for letra in itens_corrigidos:

        if letra not in itens_originais:

            resultado["erros"].append(
                f"Item {letra}: não existe na questão original."
            )

    # Compara os critérios de cada item
    for letra, original in itens_originais.items():

        if letra not in itens_corrigidos:
            continue

        corrigido = itens_corrigidos[letra]

        criterios_originais = {
            c["criterio"]: c
            for c in original["criterios_correcao"]
        }

        criterios_corrigidos = {
            c["criterio"]: c
            for c in corrigido["criterios"]
        }

        # Critérios ausentes
        for nome in criterios_originais:

            if nome not in criterios_corrigidos:

                resultado["erros"].append(
                    f"Item {letra}: critério ausente: {nome}."
                )

        # Critérios inventados
        for nome in criterios_corrigidos:

            if nome not in criterios_originais:

                resultado["erros"].append(
                    f"Item {letra}: critério não previsto: {nome}."
                )

        # Compara pontuações máximas
        for nome, criterio_original in criterios_originais.items():

            if nome not in criterios_corrigidos:
                continue

            criterio_ia = criterios_corrigidos[nome]

            valor_original = criterio_original["valor"]
            valor_ia = criterio_ia["pontos_maximos"]

            if (
                    isinstance(valor_ia, bool)
                    or not isinstance(valor_ia, (int, float))
                    or not math.isfinite(valor_ia)
            ):
                resultado["erros"].append(
                    f"Item {letra}: o critério '{nome}' "
                    "possui valor máximo inválido na resposta da IA."
                )

                continue

            if not math.isclose(
                    valor_original,
                    valor_ia,
                    rel_tol=1e-9,
                    abs_tol=1e-9
            ):
                resultado["erros"].append(
                    f"Item {letra}: o critério '{nome}' "
                    f"teve seu valor máximo alterado. "
                    f"Original: {valor_original}; "
                    f"IA: {valor_ia}."
                )

        valor_original = original["valor"]
        valor_ia = corrigido["pontos_maximos"]

        if (
                isinstance(valor_ia, bool)
                or not isinstance(valor_ia, (int, float))
                or not math.isfinite(valor_ia)
        ):
            resultado["erros"].append(
                f"Item {letra}: valor máximo inválido na resposta da IA."
            )

            continue

        if not math.isclose(
                valor_original,
                valor_ia,
                rel_tol=1e-9,
                abs_tol=1e-9
        ):
            resultado["erros"].append(
                f"Item {letra}: valor máximo alterado. "
                f"Original: {valor_original}; IA: {valor_ia}."
            )

    return resultado

def validar_consistencia_gabarito(questao_original):

    resultado = criar_resultado_validacao()

    for item in questao_original["itens"]:

        letra = item["letra"]
        valor_item = item["valor"]

        # Valida o valor máximo do item
        if (
            isinstance(valor_item, bool)
            or not isinstance(valor_item, (int, float))
            or not math.isfinite(valor_item)
            or valor_item <= 0
        ):
            resultado["erros"].append(
                f"Item {letra}: valor máximo inválido."
            )

            continue

        soma_criterios = 0
        item_valido = True

        for criterio in item["criterios_correcao"]:

            valor = criterio["valor"]

            if (
                isinstance(valor, bool)
                or not isinstance(valor, (int, float))
                or not math.isfinite(valor)
                or valor <= 0
            ):
                resultado["erros"].append(
                    f"Item {letra}: o critério "
                    f"'{criterio['criterio']}' possui "
                    f"pontuação máxima inválida."
                )

                item_valido = False
                continue

            soma_criterios += valor

        if not item_valido:
            continue

        if not math.isclose(
            soma_criterios,
            valor_item,
            rel_tol=1e-9,
            abs_tol=1e-9
        ):
            resultado["erros"].append(
                f"Item {letra}: a soma dos critérios "
                f"({soma_criterios}) é diferente do "
                f"valor máximo do item ({valor_item})."
            )

    return resultado

def validar_integridade_gabarito(questao_original):

    resultado = criar_resultado_validacao()

    letras = [
        item["letra"]
        for item in questao_original["itens"]
    ]

    # Verifica itens duplicados
    if len(letras) != len(set(letras)):

        resultado["erros"].append(
            "O gabarito original possui itens duplicados."
        )

    # Verifica critérios duplicados
    for item in questao_original["itens"]:

        letra = item["letra"]

        nomes = [
            criterio["criterio"]
            for criterio in item["criterios_correcao"]
        ]

        if len(nomes) != len(set(nomes)):

            resultado["erros"].append(
                f"Item {letra}: o gabarito original "
                f"possui critérios duplicados."
            )

    return resultado

def validar_integridade(resposta_ia):

    resultado = criar_resultado_validacao()

    # -----------------------------------------
    # 1. Verificar itens duplicados
    # -----------------------------------------

    letras = [
        item["letra"]
        for item in resposta_ia["itens"]
    ]

    if len(letras) != len(set(letras)):

        resultado["erros"].append(
            "Existem itens duplicados na correção."
        )

    # -----------------------------------------
    # 2. Verificar critérios duplicados
    # -----------------------------------------

    for item in resposta_ia["itens"]:

        letra = item["letra"]

        nomes = [
            criterio["criterio"]
            for criterio in item["criterios"]
        ]

        if len(nomes) != len(set(nomes)):

            resultado["erros"].append(
                f"Item {letra}: existem critérios duplicados."
            )

    # -----------------------------------------
    # 3. Verificar critérios que exigem revisão
    # -----------------------------------------

    for item in resposta_ia["itens"]:

        letra = item["letra"]
        criterios_pendentes = []

        for criterio in item["criterios"]:

            pontos_sugeridos = criterio["pontos_sugeridos"]
            status_criterio = criterio["status"]

            if (
                pontos_sugeridos is None
                or status_criterio in [
                    "revisao_necessaria",
                    "nao_avaliavel"
                ]
            ):

                criterios_pendentes.append(
                    criterio["criterio"]
                )

        # Se existem critérios pendentes, detalha cada um
        if criterios_pendentes:

            for nome in criterios_pendentes:

                resultado["revisoes"].append(
                    f"Item {letra}: o critério "
                    f"'{nome}' exige revisão humana."
                )

        # Se o item exige revisão, mas nenhum critério
        # específico foi identificado, registra o item
        elif item["status"] in [
            "revisao_necessaria",
            "nao_avaliavel"
        ]:

            resultado["revisoes"].append(
                f"Item {letra}: exige revisão humana."
            )

    # -----------------------------------------
    # 4. Verificar status geral
    # -----------------------------------------

    status_geral = resposta_ia["status"]

    if status_geral == "corrigido" and resultado["revisoes"]:

        resultado["erros"].append(
            "A IA marcou a correção como concluída, "
            "mas existem critérios que exigem revisão."
        )

    elif (
        status_geral in [
            "revisao_necessaria",
            "nao_avaliavel"
        ]
        and not resultado["revisoes"]
    ):

        if status_geral == "revisao_necessaria":

            resultado["revisoes"].append(
                "A correção precisa de revisão humana."
            )

        else:

            resultado["revisoes"].append(
                "A correção não pôde ser avaliada."
            )

    return resultado


def calcular_nota(resposta_ia, questao_original):

    resultado = criar_resultado_validacao()

    # -----------------------------------------
    # 1. Executar todas as validações
    # -----------------------------------------

    validacoes = [
        validar_pontuacoes(resposta_ia),

        validar_criterios_originais(
            resposta_ia,
            questao_original
        ),

        validar_integridade(resposta_ia),

        validar_consistencia_gabarito(
            questao_original
        ),

        validar_integridade_gabarito(
            questao_original
        ),

        validar_alertas(
            resposta_ia,
            questao_original
        ),

        validar_alertas_duplicados(
            resposta_ia
        ),

        validar_consistencia_status(resposta_ia),

        validar_soma_criterios(resposta_ia),

        validar_consistencia_status_itens(resposta_ia),
    ]

    # -----------------------------------------
    # 2. Consolidar resultados
    # -----------------------------------------

    for validacao in validacoes:

        for categoria in ["erros", "alertas", "revisoes"]:

            resultado[categoria].extend(
                validacao[categoria]
            )

    # -----------------------------------------
    # 2.1. Incorporar alertas da IA
    # -----------------------------------------

    alertas_unicos = []
    alertas_vistos = set()

    for alerta in resposta_ia["alertas"]:

        identificador = (
            alerta["tipo"],
            alerta["descricao"],
            alerta["gravidade"],
            alerta["item"]
        )

        if identificador not in alertas_vistos:
            alertas_vistos.add(identificador)
            alertas_unicos.append(alerta)

    resultado["alertas"].extend(alertas_unicos)

    # -----------------------------------------
    # 2.2. Verificar alertas de alta gravidade
    # -----------------------------------------

    for alerta in resposta_ia["alertas"]:

        if alerta["gravidade"] == "alta":

            resultado["revisoes"].append(
                f"Alerta de alta gravidade: "
                f"{alerta['descricao']}"
            )

    # -----------------------------------------
    # 3. Verificar se pode calcular
    # -----------------------------------------

    if resultado["erros"] or resultado["revisoes"]:

        return {
            "aprovado": False,
            "nota": None,
            **resultado
        }

    nota_maxima = sum(
        item["valor"]
        for item in questao_original["itens"]
    )

    # -----------------------------------------
    # 4. Calcular nota dos itens
    # -----------------------------------------

    resultados_itens = []

    nota_total = 0

    for item in resposta_ia["itens"]:

        nota_item = sum(
            criterio["pontos_sugeridos"]
            for criterio in item["criterios"]
        )

        nota_total += nota_item

        resultados_itens.append({
            "letra": item["letra"],
            "nota": round(nota_item, 2),
            "nota_maxima": item["pontos_maximos"]
        })

    # -----------------------------------------
    # 5. Retornar resultado definitivo
    # -----------------------------------------

    return {
        "aprovado": True,
        "nota": round(nota_total, 2),

        "nota_maxima": nota_maxima,

        "itens": resultados_itens,

        **resultado
    }

def criar_resultado_validacao():
    return {
        "erros": [],
        "alertas": [],
        "revisoes": []
    }

def validar_alertas(resposta_ia, questao_original):

    resultado = criar_resultado_validacao()

    # -----------------------------------------
    # 1. Obter itens existentes no gabarito
    # -----------------------------------------

    itens_validos = {
        str(item["letra"])
        for item in questao_original["itens"]
    }

    # -----------------------------------------
    # 2. Verificar alertas
    # -----------------------------------------

    for alerta in resposta_ia["alertas"]:

        item_alerta = alerta["item"]

        # Alertas gerais podem não estar associados
        # a um item específico.

        if item_alerta is None:
            continue

        # Verificar se o item existe

        if str(item_alerta) not in itens_validos:

            resultado["erros"].append(
                f"O alerta menciona o item "
                f"'{item_alerta}', que não existe "
                f"na questão original."
            )

    return resultado

def validar_alertas_duplicados(resposta_ia):

    resultado = criar_resultado_validacao()

    alertas_vistos = set()

    for alerta in resposta_ia["alertas"]:

        identificador = (
            alerta["tipo"],
            alerta["descricao"],
            alerta["gravidade"],
            alerta["item"]
        )

        if identificador in alertas_vistos:

            resultado["erros"].append(
                f"Alerta duplicado encontrado: "
                f"{alerta['descricao']}"
            )

        else:

            alertas_vistos.add(identificador)

    return resultado

def validar_consistencia_status(resposta_ia):

    resultado = criar_resultado_validacao()

    for item in resposta_ia["itens"]:

        letra = item["letra"]

        for criterio in item["criterios"]:

            nome = criterio["criterio"]
            status = criterio["status"]
            pontos_maximos = criterio["pontos_maximos"]
            pontos_sugeridos = criterio["pontos_sugeridos"]

            mensagem = (
                f"Item {letra}: o critério '{nome}' "
            )

            # Status que exigem pontuação numérica
            if status in (
                "atendido",
                "parcialmente_atendido",
                "nao_atendido"
            ):

                if pontos_sugeridos is None:
                    resultado["erros"].append(
                        mensagem +
                        "possui status incompatível com pontuação nula."
                    )

                    continue

                if (
                    isinstance(pontos_sugeridos, bool)
                    or not isinstance(pontos_sugeridos, (int, float))
                    or not math.isfinite(pontos_sugeridos)
                ):
                    continue

                if (
                    isinstance(pontos_maximos, bool)
                    or not isinstance(pontos_maximos, (int, float))
                    or not math.isfinite(pontos_maximos)
                    or pontos_maximos <= 0
                ):
                    continue

                if status == "atendido":

                    if not math.isclose(
                        pontos_sugeridos,
                        pontos_maximos,
                        rel_tol=1e-9,
                        abs_tol=1e-9
                    ):
                        resultado["erros"].append(
                            mensagem +
                            "está marcado como atendido, "
                            "mas não recebeu a pontuação máxima."
                        )

                elif status == "parcialmente_atendido":

                    if (
                        pontos_sugeridos <= 0
                        or pontos_sugeridos >= pontos_maximos
                    ):
                        resultado["erros"].append(
                            mensagem +
                            "está marcado como parcialmente atendido, "
                            "mas sua pontuação não é parcial."
                        )

                elif status == "nao_atendido":

                    if not math.isclose(
                        pontos_sugeridos,
                        0,
                        rel_tol=1e-9,
                        abs_tol=1e-9
                    ):
                        resultado["erros"].append(
                            mensagem +
                            "está marcado como não atendido, "
                            "mas recebeu pontuação maior que zero."
                        )

            # Status que exigem revisão
            elif status in (
                "nao_avaliavel",
                "revisao_necessaria"
            ):

                if pontos_sugeridos is not None:
                    resultado["erros"].append(
                        mensagem +
                        "está marcado para revisão, "
                        "mas possui pontuação sugerida."
                    )

    return resultado

def validar_soma_criterios(resposta_ia):

    resultado = criar_resultado_validacao()

    for item in resposta_ia["itens"]:

        letra = item["letra"]
        soma_pontos = 0
        possui_pendencia = False

        for criterio in item["criterios"]:

            pontos = criterio["pontos_sugeridos"]

            if pontos is None:
                possui_pendencia = True
                continue

            if (
                isinstance(pontos, bool)
                or not isinstance(pontos, (int, float))
                or not math.isfinite(pontos)
            ):
                continue

            soma_pontos += pontos

        # Não compara uma nota parcial com uma soma incompleta.
        if possui_pendencia:
            continue

        pontos_maximos = item["pontos_maximos"]

        if (
            isinstance(pontos_maximos, bool)
            or not isinstance(pontos_maximos, (int, float))
            or not math.isfinite(pontos_maximos)
            or pontos_maximos <= 0
        ):
            continue

        if soma_pontos > pontos_maximos and not math.isclose(
            soma_pontos,
            pontos_maximos,
            rel_tol=1e-9,
            abs_tol=1e-9
        ):

            resultado["erros"].append(
                f"Item {letra}: a soma das pontuações "
                f"sugeridas ({soma_pontos}) ultrapassa "
                f"a pontuação máxima ({pontos_maximos})."
            )

    return resultado


def validar_consistencia_status_itens(resposta_ia):
    resultado = criar_resultado_validacao()

    for item in resposta_ia["itens"]:
        letra = item["letra"]
        status_item = item["status"]

        status_criterios = [
            criterio["status"]
            for criterio in item["criterios"]
        ]

        if "nao_avaliavel" in status_criterios:
            status_esperado = "nao_avaliavel"

        elif "revisao_necessaria" in status_criterios:
            status_esperado = "revisao_necessaria"

        else:
            status_esperado = "avaliado"

        if status_item != status_esperado:
            resultado["erros"].append(
                f"Item {letra}: status '{status_item}' incompatível "
                f"com os critérios. Status esperado: '{status_esperado}'."
            )

    return resultado
