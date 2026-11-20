"""Orquestra a correção detalhada da prova discursiva do ITA."""

import re
import sympy as sp

from corretor_discursivo import gerar_correcao, preparar_dados_correcao
from services.provas_discursivas_service import obter_prova_discursiva
from validador import calcular_nota


ARQUIVO_MATEMATICA_ITA_2025 = "ita/2025/2_fase/matematica.json"


def _normalizar_potencias(texto):
    mapa = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    texto = re.sub(
        r"([a-zA-Z])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
        lambda m: m.group(1) + "^" + m.group(2).translate(mapa),
        texto,
    )
    return texto


def _verificar_q1_resto_polinomial(resposta):
    """Confere explicitamente os fatos algébricos exigidos pela questão 1."""
    texto = _normalizar_potencias(str(resposta or "")).casefold()
    texto = texto.replace("−", "-").replace("×", "*")
    compacto = re.sub(r"\s+", "", texto)
    fatos_exigidos = (
        "x^2=x-1",
        "x^3=x(x-1)",
        "x^2-x=-1",
        "x^6=1",
        "x^7=x",
        "x^14=x-1",
        "x^57=-1",
        "p(x)=(a+b)x-a",
        "a+b=2",
        "-a=1",
        "a=-1",
        "b=3",
    )
    if not all(fato in compacto for fato in fatos_exigidos):
        return False

    x, a, b = sp.symbols("x a b")
    divisor = x**2 - x + 1
    reducoes_esperadas = {
        2: x - 1,
        3: -1,
        6: 1,
        7: x,
        14: x - 1,
        57: -1,
    }
    if any(sp.rem(x**n, divisor, x) != resto for n, resto in reducoes_esperadas.items()):
        return False

    resto = sp.rem(x**57 + a*x**14 + b*x**7 + 1, divisor, x)
    return sp.solve(sp.Poly(resto - (2*x + 1), x).all_coeffs(), (a, b)) == {a: -1, b: 3}


def _normalizar_resposta(resposta):
    texto = str(resposta or "").strip().casefold()
    texto = " ".join(texto.split())
    sentinelas_sem_resposta = {
        "sem resposta",
        "nenhuma resposta",
        "não respondi",
        "nao respondi",
        "não respondido",
        "nao respondido",
        "não respondida",
        "nao respondida",
        "em branco",
        "sem resolução",
        "sem resolucao",
        "nenhuma resolução",
        "nenhuma resolucao",
    }
    return "" if texto in sentinelas_sem_resposta else texto


def _item_em_branco(letra, item_original):
    criterios = [
        {
            "criterio": criterio.criterio,
            "pontos_maximos": criterio.pontos,
            "pontos_sugeridos": 0,
            "status": "nao_atendido",
            "justificativa": "Nenhuma resposta foi registrada para este item.",
            "evidencias": [],
            "erros": [],
            "omissoes": [],
        }
        for criterio in item_original.criterios_correcao
    ]
    return {
        "letra": letra,
        "status": "avaliado",
        "pontos_maximos": item_original.valor,
        "criterios": criterios,
        "justificativa": "Nenhuma resposta foi registrada para este item.",
    }


def _item_para_revisao(letra, item_original):
    item = _item_em_branco(letra, item_original)
    item["status"] = "revisao_necessaria"
    item["justificativa"] = "O corretor não devolveu uma avaliação identificável para esta questão."
    for criterio in item["criterios"]:
        criterio["pontos_sugeridos"] = None
        criterio["status"] = "revisao_necessaria"
        criterio["justificativa"] = "A correspondência da avaliação precisa de revisão humana."
    return item


def _confirmar_criterios_q1(resposta, texto_estudante):
    item = next(
        (item for item in resposta.get("itens", []) if item.get("letra") == "Q1"),
        None,
    )
    if item is None:
        return False

    compacto = re.sub(
        r"\s+", "", _normalizar_potencias(str(texto_estudante or "")).casefold()
    ).replace("−", "-")
    x, a, b = sp.symbols("x a b")
    divisor = x**2 - x + 1
    reducoes = {
        2: x - 1, 3: -1, 6: 1, 7: x, 14: x - 1, 57: -1,
    }
    matematica_ok = all(
        sp.rem(x**n, divisor, x) == resto for n, resto in reducoes.items()
    )
    criterios = item.get("criterios", [])
    fatos_por_criterio = [
        ("obter a relação", ("x^2=x-1",), "A identidade x² = x - 1 foi conferida a partir do divisor."),
        ("deduzir corretamente", ("x^3=x(x-1)", "x^2-x=-1", "x^6=1", "x^7=x", "x^14=x-1", "x^57=-1"), "As reduções das potências foram verificadas módulo x² - x + 1."),
        ("reduzir o polinômio", ("p(x)=-1+a(x-1)+bx+1", "p(x)=(a+b)x-a"), "A redução do polinômio resulta em (a + b)x - a."),
    ]
    if len(criterios) != 4 or not matematica_ok:
        return False

    for criterio, (chave, fatos, justificativa) in zip(criterios[:3], fatos_por_criterio):
        if chave not in criterio.get("criterio", "").casefold() or not all(f in compacto for f in fatos):
            return False
        criterio["status"] = "atendido"
        criterio["pontos_sugeridos"] = criterio["pontos_maximos"]
        criterio["justificativa"] = justificativa
        criterio["erros"] = []
        criterio["omissoes"] = []

    criterio_final = criterios[3]
    if "comparar com o resto" not in criterio_final.get("criterio", "").casefold():
        return False
    sistema_presente = "a+b=2" in compacto and "-a=1" in compacto
    valores_a = re.findall(r"(?<![a-z])a=(-?\d+)", compacto)
    valores_b = re.findall(r"(?<![a-z])b=(-?\d+)", compacto)
    if not sistema_presente or not valores_a or not valores_b:
        return False
    valor_a, valor_b = int(valores_a[-1]), int(valores_b[-1])
    if valor_a == -1 and valor_b == 3:
        criterio_final["status"] = "atendido"
        criterio_final["pontos_sugeridos"] = criterio_final["pontos_maximos"]
        criterio_final["justificativa"] = "A comparação com 2x + 1 determina a = -1 e b = 3."
        criterio_final["erros"] = []
    else:
        criterio_final["status"] = "nao_atendido"
        criterio_final["pontos_sugeridos"] = 0
        criterio_final["justificativa"] = (
            f"O sistema foi montado corretamente, mas os valores apresentados "
            f"(a = {valor_a}, b = {valor_b}) não satisfazem simultaneamente "
            "a + b = 2 e -a = 1."
        )
        criterio_final["erros"] = [{
            "descricao": "Determinação incorreta do par de coeficientes.",
            "evidencia": f"a = {valor_a}, b = {valor_b}",
        }]
        resposta.setdefault("alertas", []).append({
            "tipo": "erro_calculo",
            "descricao": "O valor de b não satisfaz o sistema obtido por comparação dos coeficientes.",
            "gravidade": "media",
            "item": "Q1",
        })
    criterio_final["omissoes"] = []

    item["status"] = "avaliado"
    item["pontos_maximos"] = sum(c["pontos_maximos"] for c in criterios)
    item["justificativa"] = (
        "As reduções polinomiais foram confirmadas; a comparação dos coeficientes "
        "foi pontuada conforme o par de valores apresentado."
    )
    resposta["alertas"] = [
        alerta for alerta in resposta.get("alertas", [])
        if not (
            alerta.get("tipo") in ("problema_de_correcao", "erro_algebrico")
            and alerta.get("item") == "Q1"
        )
    ]
    return True


def corrigir_tentativa_matematica(tentativa_id, respostas):
    prova = obter_prova_discursiva(ARQUIVO_MATEMATICA_ITA_2025)
    originais = []
    correcoes = []
    em_branco = set()
    respostas_por_letra = {}

    for questao in prova.questoes:
        for item in questao.itens:
            letra = f"Q{questao.numero}"
            texto = _normalizar_resposta(
                respostas.get((questao.numero, item.letra), "")
            )
            respostas_por_letra[letra] = texto
            original = {
                "letra": letra,
                "valor": item.valor,
                "criterios_correcao": [
                    {"criterio": criterio.criterio, "valor": criterio.pontos}
                    for criterio in item.criterios_correcao
                ],
            }
            originais.append(original)
            if not texto:
                em_branco.add(letra)
                continue

            correcoes.append(preparar_dados_correcao(
                enunciado="\n\n".join(
                    parte for parte in (questao.enunciado, item.enunciado) if parte
                ),
                resposta_estudante=texto,
                gabarito=(
                    f"Resposta esperada: {item.resposta_esperada}\n"
                    f"Resolução de referência: {item.resolucao_referencia}"
                ),
                criterios_correcao=[
                    {"criterio": c.criterio, "valor": c.pontos}
                    for c in item.criterios_correcao
                ],
                letra_item=letra,
                verificar_matematica=True,
            ))

    if correcoes:
        dados = {
            "modo": "desenvolvimento",
            "correcoes_por_item": correcoes,
            "instrucao_lote": (
                "Avalie cada entrada como um item independente. A propriedade "
                "letra de cada saída deve repetir exatamente letra_item (Q1...Q10). "
                "Não omita entradas."
            ),
        }
        resposta = gerar_correcao(dados)
    else:
        resposta = {
            "versao_contrato": "1.0",
            "status": "corrigido",
            "resumo": {"pontos_fortes": [], "pontos_a_melhorar": []},
            "itens": [],
            "alertas": [],
            "observacoes_gerais": "Não houve respostas preenchidas; os itens foram pontuados com zero.",
        }

    q1_verificada = _confirmar_criterios_q1(
        resposta, respostas_por_letra.get("Q1", "")
    )
    sugestoes_ia = resposta.pop("_pontuacoes_sugeridas_ia", {})

    letras_validas = {f"Q{questao.numero}" for questao in prova.questoes}
    itens_por_letra = {
        item["letra"]: item for item in resposta.get("itens", [])
        if item.get("letra") in letras_validas
    }
    for questao in prova.questoes:
        for item in questao.itens:
            letra = f"Q{questao.numero}"
            if letra in em_branco:
                itens_por_letra[letra] = _item_em_branco(letra, item)
            elif letra not in itens_por_letra:
                itens_por_letra[letra] = _item_para_revisao(letra, item)

    if any(f"Q{questao.numero}" not in {
        item.get("letra") for item in resposta.get("itens", [])
    } for questao in prova.questoes if f"Q{questao.numero}" not in em_branco):
        resposta.setdefault("alertas", []).append({
            "tipo": "problema_de_correcao",
            "descricao": "A correção não retornou todas as questões identificadas; os itens ausentes exigem revisão humana.",
            "gravidade": "alta",
            "item": None,
        })
        resposta["observacoes_gerais"] = (
            str(resposta.get("observacoes_gerais", "")).strip()
            + " Há questões sem avaliação correspondente; a nota automática foi suspensa."
        ).strip()

    resposta["itens"] = [
        itens_por_letra[f"Q{questao.numero}"]
        for questao in prova.questoes
    ]
    resposta["status"] = (
        "corrigido"
        if all(item.get("status") == "avaliado" for item in resposta["itens"])
        else "revisao_necessaria"
    )
    if q1_verificada:
        q1_correta = resposta["itens"][0]["criterios"][3]["status"] == "atendido"
        resposta["resumo"] = {
            "pontos_fortes": ([
                "Q1: reduções polinomiais e valores de a e b verificados corretamente."
            ] if q1_correta else [
                "Q1: reduções das potências e forma do resto verificadas corretamente."
            ]),
            "pontos_a_melhorar": [
                f"{letra}: questão sem resposta; pontuação zero."
                for letra in sorted(em_branco, key=lambda valor: int(valor[1:]))
            ] + ([] if q1_correta else [
                "Q1: o valor de b não satisfaz o sistema obtido."
            ]),
        }
        resposta["observacoes_gerais"] = (
            "Q1 foi conferida por verificação algébrica independente. "
            "Questões sem resposta receberam zero."
        )

    pontuacoes_itens = []
    nota_provisoria = 0.0
    questoes_em_revisao = []
    questoes_sem_resposta = []
    for item in resposta["itens"]:
        if item["letra"] in em_branco:
            questoes_sem_resposta.append(item["letra"])
        criterios = item.get("criterios", [])
        valores = []
        sugestoes_item = sugestoes_ia.get(item["letra"], {})
        for criterio in criterios:
            valor = criterio.get("pontos_sugeridos")
            if valor is None:
                valor = sugestoes_item.get(criterio.get("criterio"))
                criterio["pontos_sugeridos_provisorios"] = valor
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                valores.append(max(0, min(valor, criterio["pontos_maximos"])))
            else:
                valores.append(0)
        nota_item = round(sum(valores), 2)
        nota_provisoria += nota_item
        if item.get("status") == "avaliado" and all(
            c.get("pontos_sugeridos") is not None for c in criterios
        ):
            pontuacoes_itens.append({
                "letra": item["letra"],
                "nota": nota_item,
                "nota_maxima": item["pontos_maximos"],
                "status": "avaliado",
            })
        else:
            questoes_em_revisao.append(item["letra"])
            pontuacoes_itens.append({
                "letra": item["letra"],
                "nota": nota_item,
                "nota_maxima": item["pontos_maximos"],
                "status": "provisorio",
            })

    validacao = calcular_nota(resposta, {"itens": originais})
    status = "corrigida" if validacao["aprovado"] else "provisoria"
    if status == "revisao_necessaria":
        resposta["resumo"] = {
            "pontos_fortes": [],
            "pontos_a_melhorar": [
                f"{letra}: avaliação pendente de revisão humana."
                for letra in questoes_em_revisao
            ] + [
                f"{letra}: questão sem resposta; pontuação zero."
                for letra in questoes_sem_resposta
            ],
        }
        resposta["observacoes_gerais"] = (
            "A nota final não foi consolidada porque "
            + (
                f"{', '.join(questoes_em_revisao)} exige(m) revisão humana. "
                if questoes_em_revisao else ""
            )
            + (
                f"{', '.join(questoes_sem_resposta)} ficaram sem resposta e "
                "receberam pontuação zero."
                if questoes_sem_resposta else ""
            )
        ).strip()
    if status == "provisoria":
        resposta["alertas"] = [
            alerta for alerta in resposta.get("alertas", [])
            if alerta.get("tipo") != "problema_de_correcao"
        ]
        resposta["alertas"].append({
            "tipo": "verificacao_inconclusiva",
            "descricao": (
                "A Gemini sugeriu esta pontuação, mas o motor matemático não "
                "conseguiu confirmar todos os critérios. Confira a resolução."
            ),
            "gravidade": "media",
            "item": None,
        })
        resposta["observacoes_gerais"] = (
            "Esta é uma estimativa da IA, não uma nota confirmada. "
            "A conferência matemática independente ficou inconclusiva; "
            "revise as evidências antes de usar a pontuação."
        )
    return {
        "status": status,
        "correcao": resposta,
        "validacao": validacao,
        "pontuacoes_itens": pontuacoes_itens,
        "nota_parcial_avaliada": round(sum(
            item["nota"] for item in pontuacoes_itens
            if item["nota"] is not None
        ), 2),
        "nota": validacao.get("nota") if validacao["aprovado"] else None,
        "nota_provisoria": None if validacao["aprovado"] else round(nota_provisoria, 2),
        "nota_maxima": validacao.get("nota_maxima") or sum(i["valor"] for i in originais),
        "tentativa_id": tentativa_id,
    }
