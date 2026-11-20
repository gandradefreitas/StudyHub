"""Corrige provas comparando somente as respostas finais com o gabarito."""

import re
import unicodedata

from corretor_discursivo import gerar_correcao, preparar_dados_correcao
from services.provas_discursivas_service import obter_prova_discursiva
from validador import calcular_nota


ARQUIVOS_PROVA_ITA = {
    "matematica": "ita/2025/2_fase/matematica.json",
    "fisica": "ita/2025/2_fase/fisica.json",
    "quimica": "ita/2025/2_fase/quimica.json",
}

CRITERIO_RESPOSTA_FINAL = "Comparar a resposta final com o gabarito cadastrado."
CRITERIO_Q8A_GEOMETRIA = "Identificar quatro partículas nos vértices de um quadrado."
CRITERIO_Q8A_CARGAS = (
    "Colocar as duas cargas positivas em vértices opostos e as negativas nos outros vértices opostos."
)
CRITERIOS_Q7A_QUIMICA = (
    "Protonar a amina com HCl.",
    "Desprotonar o ácido carboxílico com NaHCO3.",
    "Desprotonar o fenol com NaOH.",
)
CRITERIOS_Q10C_QUIMICA = (
    "Informar a perda de aproximadamente 0,355 g no catodo.",
    "Informar que a massa do anodo permanece inalterada.",
)


def _criterios_item(disciplina_slug, letra, valor):
    if disciplina_slug == "fisica" and letra == "Q8a":
        metade = valor / 2
        return [
            {"criterio": CRITERIO_Q8A_GEOMETRIA, "valor": metade},
            {"criterio": CRITERIO_Q8A_CARGAS, "valor": metade},
        ]
    if disciplina_slug == "quimica" and letra == "Q7a":
        pontos = valor / len(CRITERIOS_Q7A_QUIMICA)
        return [
            {"criterio": criterio, "valor": pontos}
            for criterio in CRITERIOS_Q7A_QUIMICA
        ]
    if disciplina_slug == "quimica" and letra == "Q10c":
        metade = valor / len(CRITERIOS_Q10C_QUIMICA)
        return [
            {"criterio": criterio, "valor": metade}
            for criterio in CRITERIOS_Q10C_QUIMICA
        ]
    return [{"criterio": CRITERIO_RESPOSTA_FINAL, "valor": valor}]


def _normalizar_resposta(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return re.sub(r"\s+", " ", texto).strip()


def _avaliar_configuracao_q8a(resposta, valor):
    """Confere os dois elementos explícitos exigidos pela configuração de Q8a."""
    normalizada = _normalizar_resposta(resposta)
    geometria = (
        "quadrad" in normalizada
        and (re.search(r"\b4\b", normalizada) or "quatro" in normalizada)
    )
    positivas = bool(re.search(r"positiv\w*|cargas?\s*\+", normalizada))
    negativas = bool(re.search(r"negativ\w*|cargas?\s*-", normalizada))
    relacao_oposta = bool(re.search(r"opost\w*|diagonal\w*|antipod\w*", normalizada))
    disposicao_cargas = positivas and negativas and relacao_oposta

    criterios = []
    for nome, atendido, justificativa in (
        (
            CRITERIO_Q8A_GEOMETRIA,
            geometria,
            "A resposta identificou quatro partículas nos vértices de um quadrado."
            if geometria else
            "A resposta não identificou explicitamente quatro partículas nos vértices de um quadrado.",
        ),
        (
            CRITERIO_Q8A_CARGAS,
            disposicao_cargas,
            "A resposta indicou cargas positivas e negativas em posições opostas."
            if disposicao_cargas else
            "A resposta precisa indicar as duas cargas positivas e as duas negativas, com cada par em posições opostas.",
        ),
    ):
        maximo = valor / 2
        criterios.append({
            "criterio": nome,
            "pontos_maximos": maximo,
            "pontos_sugeridos": maximo if atendido else 0,
            "status": "atendido" if atendido else "nao_atendido",
            "justificativa": justificativa,
            "evidencias": [{"trecho": resposta, "tipo": "evidencia_positiva" if atendido else "evidencia_negativa"}],
            "erros": [] if atendido else [{"descricao": justificativa, "evidencia": resposta}],
            "omissoes": [] if atendido else [justificativa],
        })
    pontos = sum(criterio["pontos_sugeridos"] for criterio in criterios)
    return {
        "criterios": criterios,
        "pontos": pontos,
        "status": "avaliado",
        "justificativa": (
            "A configuração foi avaliada pelos elementos explícitos da resposta. "
            "A nota parcial não verifica o raciocínio usado."
        ),
    }


def _criterio_deterministico(nome, maximo, resposta, atendido, justificativa):
    return {
        "criterio": nome,
        "pontos_maximos": maximo,
        "pontos_sugeridos": maximo if atendido else 0,
        "status": "atendido" if atendido else "nao_atendido",
        "justificativa": justificativa,
        "evidencias": [{
            "trecho": resposta,
            "tipo": "evidencia_positiva" if atendido else "evidencia_negativa",
        }],
        "erros": [] if atendido else [{"descricao": justificativa, "evidencia": resposta}],
        "omissoes": [] if atendido else [justificativa],
    }


def _avaliar_quimica_q7a(resposta, valor):
    normalizada = _normalizar_resposta(resposta)
    compacta = re.sub(r"[^a-z0-9]", "", normalizada)
    verificacoes = (
        (
            CRITERIOS_Q7A_QUIMICA[0],
            all(token in compacta for token in ("rnh2", "hcl", "rnh3")),
            "A resposta precisa mostrar a protonacao de R-NH2 por HCl formando R-NH3+.",
        ),
        (
            CRITERIOS_Q7A_QUIMICA[1],
            all(token in compacta for token in ("rcooh", "nahco3", "rcoona", "co2")),
            "A resposta precisa mostrar R-COOH reagindo com NaHCO3 para formar carboxilato e CO2.",
        ),
        (
            CRITERIOS_Q7A_QUIMICA[2],
            all(token in compacta for token in ("roh", "naoh", "rona")),
            "A resposta precisa mostrar R-OH reagindo com NaOH para formar R-O-Na+.",
        ),
    )
    maximo = valor / len(verificacoes)
    criterios = [
        _criterio_deterministico(nome, maximo, resposta, atendido, justificativa)
        for nome, atendido, justificativa in verificacoes
    ]
    return {
        "criterios": criterios,
        "status": "avaliado",
        "justificativa": "As três etapas de separação foram conferidas individualmente.",
    }


def _avaliar_quimica_q10c(resposta, valor):
    normalizada = _normalizar_resposta(resposta)
    perda_certeza = bool(
        re.search(r"0[,.]35[5-9]|0[,.]36|355\s*mg", normalizada)
        and re.search(r"catod", normalizada)
        and re.search(r"diminu|perd|negativ|[-−]\s*0[,.]35", normalizada)
    )
    anodo_inalterado = bool(
        re.search(r"anod", normalizada)
        and re.search(r"nula|zero|nao varia|sem alteracao|inalterad|0\s*g", normalizada)
    )
    metade = valor / 2
    criterios = [
        _criterio_deterministico(
            CRITERIOS_Q10C_QUIMICA[0], metade, resposta, perda_certeza,
            "A resposta precisa indicar que o catodo perde aproximadamente 0,355 g.",
        ),
        _criterio_deterministico(
            CRITERIOS_Q10C_QUIMICA[1], metade, resposta, anodo_inalterado,
            "A resposta precisa informar que a massa do anodo de platina não varia.",
        ),
    ]
    return {
        "criterios": criterios,
        "status": "avaliado",
        "justificativa": "As variações de massa do catodo e do anodo foram conferidas separadamente.",
    }


def _pontos_item(item):
    return sum(
        criterio.get("pontos_sugeridos") or 0
        for criterio in item.get("criterios", [])
    )


def corrigir_tentativa_resposta_final(tentativa_id, respostas, disciplina="matematica"):
    """Avalia as respostas finais da prova, sem pontuar o processo de resolução."""
    disciplina_slug = {
        "Matemática": "matematica", "matematica": "matematica",
        "Física": "fisica", "fisica": "fisica",
        "Química": "quimica", "quimica": "quimica",
    }.get(disciplina)
    if disciplina_slug not in ARQUIVOS_PROVA_ITA:
        raise ValueError(f"Disciplina não suportada para resposta final: {disciplina}")
    prova = obter_prova_discursiva(ARQUIVOS_PROVA_ITA[disciplina_slug])

    originais = []
    correcoes = []
    itens_em_branco = []

    for questao in prova.questoes:
        for item in questao.itens:
            sufixo = str(item.letra or "").strip()
            letra = f"Q{questao.numero}{sufixo}"
            resposta = str(
                respostas.get((questao.numero, item.letra), "") or ""
            ).strip()
            criterios_originais = _criterios_item(disciplina_slug, letra, item.valor)
            original = {
                "letra": letra,
                "valor": item.valor,
                "criterios_correcao": criterios_originais,
            }
            originais.append(original)

            if not resposta:
                itens_em_branco.append({
                    "letra": letra,
                    "status": "avaliado",
                    "pontos_maximos": item.valor,
                    "criterios": [{
                        "criterio": criterio["criterio"],
                        "pontos_maximos": criterio["valor"],
                        "pontos_sugeridos": 0,
                        "status": "nao_atendido",
                        "justificativa": "Nenhuma resposta foi registrada para este item; foi atribuído zero.",
                        "evidencias": [],
                        "erros": [],
                        "omissoes": [],
                    } for criterio in criterios_originais],
                    "justificativa": "Nenhuma resposta foi registrada para este item; foi atribuído zero.",
                })
                continue

            correcoes.append(preparar_dados_correcao(
                enunciado="\n\n".join(
                    parte for parte in (questao.enunciado, item.enunciado) if parte
                ),
                resposta_estudante=resposta,
                gabarito=(
                    f"Resposta esperada: {item.resposta_esperada}"
                ),
                criterios_correcao=criterios_originais,
                letra_item=letra,
                modo="final",
                verificar_matematica=False,
            ))

    if correcoes:
        resposta_ia = gerar_correcao({
            "modo": "final",
            "correcoes_por_item": correcoes,
            "instrucao_lote": (
                "Compare somente a resposta final de cada questão com o gabarito. "
            "A saída deve repetir exatamente os identificadores enviados, como Q1a, Q1b ou Q2; "
                "não avalie nem invente raciocínio ou etapas."
            ),
        })
    else:
        resposta_ia = {
            "versao_contrato": "1.0",
            "status": "corrigido",
            "resumo": {"pontos_fortes": [], "pontos_a_melhorar": []},
            "itens": [],
            "alertas": [],
            "observacoes_gerais": "Não houve respostas preenchidas; os itens receberam zero.",
        }

    itens_por_letra = {
        item.get("letra"): item for item in resposta_ia.get("itens", [])
    }
    for item in itens_em_branco:
        itens_por_letra[item["letra"]] = item

    resposta_ia["itens"] = [
        itens_por_letra.get(f"Q{questao.numero}{str(item.letra or '').strip()}")
        for questao in prova.questoes
        for item in questao.itens
    ]
    if any(item is None for item in resposta_ia["itens"]):
        raise ValueError("A IA não retornou a avaliação de todas as questões.")

    respostas_por_letra = {}
    for questao in prova.questoes:
        for item in questao.itens:
            letra = f"Q{questao.numero}{str(item.letra or '').strip()}"
            respostas_por_letra[letra] = str(
                respostas.get((questao.numero, item.letra), "") or ""
            ).strip()

    # Como o estudante envia somente a resposta final, não há base para
    # conceder pontos de procedimento nem pontuação parcial por etapas.
    for item in resposta_ia["itens"]:
        criterios = item.get("criterios", [])
        if item.get("letra") == "Q8a" and disciplina_slug == "fisica":
            avaliacao = _avaliar_configuracao_q8a(
                respostas_por_letra["Q8a"], item["pontos_maximos"]
            )
            item["criterios"] = avaliacao["criterios"]
            item["status"] = avaliacao["status"]
            item["justificativa"] = avaliacao["justificativa"]
            continue
        avaliador_deterministico = {
            ("quimica", "Q7a"): _avaliar_quimica_q7a,
            ("quimica", "Q10c"): _avaliar_quimica_q10c,
        }.get((disciplina_slug, item.get("letra")))
        if avaliador_deterministico:
            avaliacao = avaliador_deterministico(
                respostas_por_letra[item["letra"]], item["pontos_maximos"]
            )
            item["criterios"] = avaliacao["criterios"]
            item["status"] = avaliacao["status"]
            item["justificativa"] = avaliacao["justificativa"]
            continue
        if len(criterios) != 1:
            raise ValueError("A IA retornou critérios incompatíveis com o modo de resposta final.")
        criterio = criterios[0]
        pontuacao = criterio.get("pontos_sugeridos")
        maximo = criterio.get("pontos_maximos")
        if criterio.get("status") == "atendido" and pontuacao == maximo:
            criterio["justificativa"] = (
                "A resposta final foi considerada equivalente ao gabarito cadastrado. "
                "O raciocínio não foi avaliado."
            )
            item["justificativa"] = criterio["justificativa"]
            continue
        if criterio.get("status") == "nao_atendido" and pontuacao == 0:
            criterio["justificativa"] = (
                "A resposta final não corresponde ao gabarito cadastrado. "
                "O raciocínio não foi avaliado."
            )
            item["justificativa"] = criterio["justificativa"]
            continue
        criterio["status"] = "revisao_necessaria"
        criterio["pontos_sugeridos"] = None
        item["status"] = "revisao_necessaria"
        resposta_ia["status"] = "revisao_necessaria"
        criterio["justificativa"] = (
            "A comparação da resposta final ficou inconclusiva; é necessária revisão."
        )
        item["justificativa"] = criterio["justificativa"]

    resposta_ia["resumo"] = {
        "pontos_fortes": [
            f"{item['letra']}: resposta final equivalente ao gabarito."
            for item in resposta_ia["itens"]
            if _pontos_item(item) == item["pontos_maximos"]
        ],
        "pontos_a_melhorar": [
            (
                f"{item['letra']}: resposta parcialmente correta; "
                f"{_pontos_item(item):g} de {item['pontos_maximos']:g} pontos."
                if 0 < _pontos_item(item) < item["pontos_maximos"]
                else f"{item['letra']}: resposta final divergente do gabarito."
            )
            for item in resposta_ia["itens"]
            if _pontos_item(item) < item["pontos_maximos"]
        ] + [
            f"{item['letra']}: comparação da resposta final inconclusiva."
            for item in resposta_ia["itens"]
            if item["criterios"][0].get("status") == "revisao_necessaria"
        ],
    }

    resposta_ia["observacoes_gerais"] = (
        "A avaliação comparou somente as respostas finais com os gabaritos. "
        "Ela não verificou o raciocínio ou os procedimentos usados pelo estudante. "
        "Confira se seu raciocínio está correto."
    )

    validacao = calcular_nota(resposta_ia, {"itens": originais})
    nota = validacao.get("nota") if validacao.get("aprovado") else None
    nota_provisoria = None
    status = "corrigida" if nota is not None else "provisoria"

    pontuacoes_itens = []
    for item in resposta_ia["itens"]:
        pontos_criterios = [
            criterio.get("pontos_sugeridos")
            for criterio in item.get("criterios", [])
        ]
        if any(pontos is None for pontos in pontos_criterios):
            pontos = 0
            item_status = "provisorio"
        else:
            pontos = sum(pontos_criterios)
            item_status = "avaliado"
        pontuacoes_itens.append({
            "letra": item["letra"],
            "nota": pontos,
            "nota_maxima": item["pontos_maximos"],
            "status": item_status,
        })

    if status == "provisoria":
        nota_provisoria = round(sum(item["nota"] for item in pontuacoes_itens), 2)
        resposta_ia["alertas"] = [
            alerta for alerta in resposta_ia.get("alertas", [])
            if alerta.get("tipo") != "problema_de_correcao"
        ]
        resposta_ia["alertas"].append({
            "tipo": "comparacao_inconclusiva",
            "descricao": "Uma ou mais respostas finais não puderam ser comparadas com segurança.",
            "gravidade": "media",
            "item": None,
        })

    return {
        "status": status,
        "correcao": resposta_ia,
        "validacao": validacao,
        "pontuacoes_itens": pontuacoes_itens,
        "nota_parcial_avaliada": round(sum(
            item["nota"] for item in pontuacoes_itens
            if item["status"] == "avaliado"
        ), 2),
        "nota": nota,
        "nota_provisoria": nota_provisoria,
        "nota_maxima": validacao.get("nota_maxima") or sum(i["valor"] for i in originais),
        "tentativa_id": tentativa_id,
        "modo_correcao": "resposta_final",
    }
