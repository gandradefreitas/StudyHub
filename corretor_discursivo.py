from pathlib import Path
import json
import copy
import re
from gemini_client import criar_cliente, MODELO_GEMINI
from google.genai import types
from validador import calcular_nota
from verificador_matematico import analisar_procedimento


_PADRAO_LINHA_MATEMATICA = re.compile(
    r"[0-9A-Za-z\s_+\-*/^=().,\[\]|√²³⁻×÷·−<>≤≥]+"
)


def extrair_etapas_matematicas(resposta_estudante):
    """Extrai linhas de igualdade literais para checagem independente.

    Linhas de texto livre não são reescritas nem completadas. A extração é
    deliberadamente conservadora: somente linhas com igualdade e caracteres
    matemáticos simples são encaminhadas ao motor.
    """
    if not isinstance(resposta_estudante, str):
        return []

    etapas = []

    for linha in resposta_estudante.splitlines():
        candidata = linha.strip().strip("`")
        candidata = re.sub(r"^(?:\(\d+\)|\d+[.)])\s*", "", candidata)

        if "=" not in candidata:
            continue

        if _PADRAO_LINHA_MATEMATICA.fullmatch(candidata):
            etapas.append(candidata)

    return etapas


def analisar_resposta_matematica(resposta_estudante):
    """Verifica as transformações visíveis, sem inferir etapas omitidas."""
    etapas = extrair_etapas_matematicas(resposta_estudante)

    if len(etapas) < 2:
        return {
            "status": "sem_etapas_suficientes",
            "etapas": etapas,
            "observacao": (
                "Não foram identificadas pelo menos duas linhas matemáticas "
                "comparáveis. Não inferir nem inventar etapas."
            ),
        }

    return analisar_procedimento(etapas)


def _normalizar_trecho_matematico(texto):
    texto = str(texto).lower()
    texto = texto.replace("−", "-").replace("×", "*").replace("÷", "/")
    return re.sub(r"\s+", "", texto)


def _criterio_de_resultado_final(criterio):
    nome = criterio.get("criterio", "").lower()
    return bool(re.search(
        r"\b(resultado|resposta|solu[cç][aã]o)\s+final\b",
        nome,
    ))


def _criterio_menciona_divisao(criterio):
    nome = criterio.get("criterio", "").lower()
    return bool(re.search(r"divis|quociente|coeficiente", nome))


def _suspender_correcao_matematica(resposta_ia, motivo):
    resposta_ia["status"] = "revisao_necessaria"
    resposta_ia["observacoes_gerais"] = " ".join(
        parte for parte in [
            resposta_ia.get("observacoes_gerais", "").strip(),
            f"A nota automática foi suspensa: {motivo}",
        ] if parte
    )

    alerta = {
        "tipo": "problema_de_correcao",
        "descricao": (
            "A verificação matemática não pôde ser associada com segurança "
            "aos critérios. A correção requer revisão humana."
        ),
        "gravidade": "alta",
        "item": None,
    }
    alertas = resposta_ia.setdefault("alertas", [])
    if alerta not in alertas:
        alertas.append(alerta)

    for item in resposta_ia.get("itens", []):
        item["status"] = "revisao_necessaria"
        for criterio in item.get("criterios", []):
            criterio["status"] = "revisao_necessaria"
            criterio["pontos_sugeridos"] = None

    return resposta_ia


def aplicar_barreira_matematica(resposta_ia, dados):
    """Reconcilia erros comprovados e suspende casos sem vínculo seguro."""
    analise = dados.get("analise_matematica_motor")

    if not isinstance(analise, dict) or analise.get("status") == "correct":
        return resposta_ia

    if analise.get("status") != "incorrect":
        motivo = analise.get("justificativa") or analise.get("observacao") or (
            "O motor matemático não conseguiu confirmar o procedimento."
        )
        return _suspender_correcao_matematica(resposta_ia, motivo)

    detalhes = analise.get("detalhes") or {}
    transformacoes_incorretas = [
        transformacao
        for transformacao in detalhes.get("transformacoes", [])
        if transformacao.get("resultado", {}).get("status") == "incorrect"
    ]
    if not transformacoes_incorretas:
        return _suspender_correcao_matematica(
            resposta_ia,
            "O motor indicou erro sem fornecer a transformação correspondente.",
        )

    equivalencia_global = detalhes.get("equivalencia_global") or {}
    status_global = equivalencia_global.get("status")
    transformacoes = detalhes.get("transformacoes", [])
    criterios_final = []
    criterios_por_transformacao = []

    for item in resposta_ia.get("itens", []):
        for criterio in item.get("criterios", []):
            if _criterio_de_resultado_final(criterio):
                criterios_final.append(criterio)

    for transformacao in transformacoes_incorretas:
        trecho_alvo = _normalizar_trecho_matematico(
            transformacao.get("para", "")
        )
        trecho_origem = _normalizar_trecho_matematico(
            transformacao.get("de", "")
        )
        if not trecho_alvo:
            return _suspender_correcao_matematica(
                resposta_ia,
                "Uma transformação incorreta não contém trecho identificável.",
            )

        criterios_correspondentes = []
        for item in resposta_ia.get("itens", []):
            for criterio in item.get("criterios", []):
                evidencias = criterio.get("evidencias", [])
                evidencia_confirma_destino = any(
                    trecho_alvo in _normalizar_trecho_matematico(
                        evidencia.get("trecho", "")
                    )
                    for evidencia in evidencias
                )
                evidencia_confirma_origem_da_divisao = (
                    _criterio_menciona_divisao(criterio)
                    and trecho_origem
                    and any(
                        trecho_origem in _normalizar_trecho_matematico(
                            evidencia.get("trecho", "")
                        )
                        for evidencia in evidencias
                    )
                )
                if (
                    evidencia_confirma_destino
                    or evidencia_confirma_origem_da_divisao
                ):
                    criterios_correspondentes.append((item, criterio))

        criterios_de_procedimento = [
            par for par in criterios_correspondentes
            if not _criterio_de_resultado_final(par[1])
        ]
        if not criterios_de_procedimento:
            return _suspender_correcao_matematica(
                resposta_ia,
                "Uma transformação incorreta não pôde ser ligada a um "
                "critério de procedimento pelas evidências da resposta.",
            )

        criterios_por_transformacao.append(
            (transformacao, criterios_de_procedimento)
        )

    # Confirma critérios positivos apoiados por uma transformação que o motor
    # verificou como correta, mesmo quando a IA os deixou pendentes por causa
    # de outro erro no procedimento.
    transformacoes_corretas = [
        transformacao
        for transformacao in transformacoes
        if transformacao.get("resultado", {}).get("status") == "correct"
    ]
    for item in resposta_ia.get("itens", []):
        for criterio in item.get("criterios", []):
            if (
                _criterio_de_resultado_final(criterio)
                or criterio.get("status") not in (
                    "revisao_necessaria", "nao_avaliavel"
                )
                or criterio.get("pontos_sugeridos") is not None
            ):
                continue

            evidencias_positivas = [
                evidencia
                for evidencia in criterio.get("evidencias", [])
                if evidencia.get("tipo") == "evidencia_positiva"
            ]
            if any(
                _normalizar_trecho_matematico(
                    transformacao.get("para", "")
                )
                in _normalizar_trecho_matematico(
                    evidencia.get("trecho", "")
                )
                for transformacao in transformacoes_corretas
                for evidencia in evidencias_positivas
            ):
                criterio["status"] = "atendido"
                criterio["pontos_sugeridos"] = criterio["pontos_maximos"]
                criterio["justificativa"] = (
                    "O motor confirmou como correta a transformação mostrada "
                    "na evidência. Este critério foi avaliado separadamente "
                    "dos erros em outras etapas."
                )

    for transformacao, correspondencias in criterios_por_transformacao:
        de = transformacao.get("de", "")
        para = transformacao.get("para", "")
        etapa = transformacao.get("etapa", "?")
        justificativa_motor = (
            transformacao.get("resultado", {}).get("justificativa")
            or "A transformação não preserva a equivalência."
        )

        for item, criterio in correspondencias:
            criterio["status"] = "nao_atendido"
            criterio["pontos_sugeridos"] = 0
            criterio["justificativa"] = (
                f"Etapa {etapa}: {justificativa_motor} "
                f"Transformação verificada: {de} → {para}."
            )
            criterio.setdefault("erros", []).append({
                "descricao": justificativa_motor,
                "evidencia": f"{de} → {para}",
            })

        alerta = {
            "tipo": "erro_algebrico",
            "descricao": (
                f"O motor matemático identificou uma transformação "
                f"incorreta na etapa {etapa}: {de} → {para}."
            ),
            "gravidade": "media",
            "item": correspondencias[0][0].get("letra"),
        }
        alertas = resposta_ia.setdefault("alertas", [])
        if alerta not in alertas:
            alertas.append(alerta)

    if criterios_final:
        if status_global == "correct":
            ultima_linha = _normalizar_trecho_matematico(
                transformacoes[-1].get("para", "")
            ) if transformacoes else ""
            for criterio in criterios_final:
                criterio["status"] = "atendido"
                criterio["pontos_sugeridos"] = criterio["pontos_maximos"]
                criterio["justificativa"] = (
                    "O motor confirmou que a última equação é equivalente à "
                    "equação inicial. O resultado final foi pontuado "
                    "separadamente dos passos intermediários incorretos."
                )
                for evidencia in criterio.get("evidencias", []):
                    trecho = _normalizar_trecho_matematico(
                        evidencia.get("trecho", "")
                    )
                    if ultima_linha and ultima_linha in trecho:
                        evidencia["tipo"] = "evidencia_positiva"
        elif status_global == "incorrect":
            for criterio in criterios_final:
                criterio["status"] = "nao_atendido"
                criterio["pontos_sugeridos"] = 0
                criterio["justificativa"] = (
                    "O motor confirmou que a última equação não é equivalente "
                    "à equação inicial; o resultado final está incorreto."
                )
        else:
            return _suspender_correcao_matematica(
                resposta_ia,
                "O motor não conseguiu confirmar o resultado final.",
            )

    pendencia = False
    for item in resposta_ia.get("itens", []):
        status_criterios = [
            criterio.get("status") for criterio in item.get("criterios", [])
        ]
        item["status"] = (
            "revisao_necessaria"
            if any(status in ("revisao_necessaria", "nao_avaliavel")
                   for status in status_criterios)
            else "avaliado"
        )
        pendencia = pendencia or item["status"] == "revisao_necessaria"

    resposta_ia["status"] = (
        "revisao_necessaria" if pendencia else "corrigido"
    )
    resposta_ia["observacoes_gerais"] = (
        "O motor matemático confirmou a equivalência global do resultado "
        "final separadamente dos passos intermediários. As transformações "
        "comprovadamente incorretas tiveram seus critérios associados "
        "ajustados; critérios sem evidência suficiente seguem para revisão."
    )

    return resposta_ia

def preparar_dados_correcao(
    enunciado,
    resposta_estudante,
    gabarito,
    criterios_correcao,
    letra_item,
    modo="desenvolvimento",
    verificar_matematica=False,
):
    dados = {
        "enunciado": enunciado,
        "resposta_estudante": resposta_estudante,
        "gabarito": gabarito,
        "criterios_correcao": criterios_correcao,
        "letra_item": letra_item,
        "modo": modo
    }

    if verificar_matematica and modo == "desenvolvimento":
        dados["analise_matematica_motor"] = analisar_resposta_matematica(
            resposta_estudante
        )

    return dados


def construir_prompt_correcao(dados):
    instrucoes = """
Você é um avaliador especializado em questões discursivas de vestibulares
de alta exigência, especialmente do Instituto Tecnológico de Aeronáutica (ITA).

Sua tarefa é analisar a resposta do estudante com rigor técnico, considerando
o raciocínio apresentado e os critérios oficiais de correção.

Quando "modo" for "final", as instruções específicas desse modo prevalecem:
o estudante forneceu somente o resultado, então não avalie nem descreva seu
raciocínio ou procedimentos.

REGRAS GERAIS:

1. Utilize o gabarito e os critérios fornecidos como referência oficial.
2. Não invente critérios, pontuações ou exigências que não estejam no material.
3. Avalie cada critério individualmente.
4. Fundamente suas avaliações em evidências encontradas na resposta.
5. Não considere uma resposta incorreta apenas porque utiliza um método
   diferente do gabarito, desde que seja matematicamente ou cientificamente válido.
6. Não desconte pontos repetidamente pelo mesmo erro.
7. Diferencie erros conceituais, algébricos, de cálculo e de unidade.
8. Se houver ambiguidade, informação insuficiente ou inconsistência no gabarito,
   sinalize a situação em vez de inventar uma solução.
9. Não ultrapasse a pontuação máxima de cada critério.
10. Não invente etapas que o estudante não apresentou.

FORMATO DA RESPOSTA DO ESTUDANTE:

Aceite resoluções em prosa, parágrafos, tópicos, equações ou combinações desses
formatos. Não exija uma linha por equação nem recomende um formato específico
quando o raciocínio puder ser compreendido.

Não trate escolhas de formatação como ponto a melhorar, a menos que a organização
realmente impeça a compreensão de uma etapa matemática.

VERIFICAÇÃO MATEMÁTICA E FIDELIDADE À RESPOSTA:

11. Avalie exclusivamente as operações, transformações e justificativas
    efetivamente apresentadas pelo estudante.

12. Não presuma operações intermediárias, cálculos mentais ou simplificações
    que não estejam explicitamente demonstrados ou que não possam ser
    deduzidos de maneira inequívoca da resposta.

13. Em questões matemáticas, verifique a validade de cada transformação
    algébrica apresentada. Uma igualdade incorreta deve ser identificada
    como erro, mesmo que o resultado seguinte seja coerente com ela.

14. Nunca justifique uma transformação incorreta inventando uma operação
    implícita que alteraria o significado da expressão apresentada.

15. Diferencie uma etapa omitida de uma etapa executada incorretamente.
    Uma operação não apresentada não deve ser considerada automaticamente
    correta.

16. Verifique o resultado final substituindo-o no enunciado original,
    sempre que essa verificação for matematicamente aplicável.

17. Não declare o gabarito inconsistente apenas porque a resposta do
    estudante diverge dele. Antes, verifique independentemente a validade
    do gabarito utilizando o enunciado original.

18. Quando uma etapa estiver matematicamente incorreta, registre o erro
    correspondente, apresente a evidência textual e não atribua pontuação
    como se o procedimento tivesse sido realizado corretamente.

DISTINÇÃO ENTRE ERRO DO ESTUDANTE E INCONSISTÊNCIA DO GABARITO:

19. A divergência entre a resposta do estudante e o gabarito oficial
    não constitui, por si só, uma inconsistência do gabarito.

20. Antes de emitir um alerta do tipo "gabarito_inconsistente",
    resolva independentemente o problema a partir do enunciado original
    e compare o resultado matematicamente correto com o gabarito.

21. Se o gabarito estiver matematicamente correto e o estudante apresentar
    resultado diferente devido a um erro próprio, avalie como resposta
    incorreta. Não emita alerta de gabarito inconsistente.

22. Diferencie erros propagados de erros independentes. Quando uma operação
    posterior estiver correta, mas utilizar um resultado incorreto anterior,
    considere a possibilidade de conceder os pontos correspondentes ao
    procedimento posterior, conforme os critérios oficiais.

23. Não utilize revisão humana quando o erro puder ser identificado,
    demonstrado e pontuado com segurança pelos critérios fornecidos.

24. Utilize "revisao_necessaria" somente quando houver uma dúvida real
    que impeça uma avaliação confiável, e não simplesmente porque o
    estudante cometeu um erro matemático.

AVALIAÇÃO DE ERROS PROPAGADOS:

25. Avalie cada critério considerando a operação ou competência
    específica que ele descreve.

26. Quando um critério envolver uma operação matemática executada
    sobre um resultado intermediário incorreto, verifique se a
    operação em si foi realizada corretamente.

27. Se a operação estiver correta, conceda a pontuação correspondente
    ao critério, mesmo que o valor utilizado tenha origem em um erro
    anterior, desde que o critério não exija explicitamente a correção
    desse valor de origem.

28. Não desconte novamente pontos por um erro já penalizado em outro
    critério, salvo quando houver um erro independente adicional.

29. Diferencie a correção do procedimento da correção do resultado:
    uma operação pode estar correta mesmo quando o resultado global
    da resolução permanece incorreto.

30. Preserve exatamente os identificadores dos itens fornecidos nos dados
    da correção, incluindo letras, números, acentuação e capitalização.
    Nunca altere a identificação de um item.

VERIFICAÇÃO INDEPENDENTE PELO MOTOR MATEMÁTICO:

Quando os dados incluírem "analise_matematica_motor", use o resultado como
checagem independente das linhas matemáticas efetivamente extraídas da resposta.
Considere cada transformação marcada como incorreta e seus diagnósticos ao
avaliar os critérios correspondentes. Não trate etapas não identificadas como
corretas. Se o motor retornar resultado indeterminado, inválido ou sem etapas
suficientes, não invente uma conclusão; sinalize revisão quando isso impedir
uma avaliação confiável.

Ao citar evidência de um critério sobre uma transformação, inclua as duas linhas
adjacentes da resposta (origem e resultado) sempre que ambas estiverem presentes.
Avalie o resultado final separadamente: uma etapa intermediária incorreta não
torna automaticamente incorreta uma resposta final que resolva a equação original.

O motor verifica equivalência algébrica entre linhas. Ele não substitui a
avaliação dos critérios oficiais, da interpretação do enunciado, da clareza da
justificativa ou de operações que não estejam representadas nas linhas.

CONSISTÊNCIA DA AVALIAÇÃO:

- A justificativa deve corresponder exatamente às evidências apresentadas.
- Não classifique um critério como atendido quando a operação demonstrada
  pelo estudante estiver incorreta.
- Não utilize o resultado de uma etapa incorreta como evidência de que
  o procedimento anterior foi correto.
- A pontuação, o status, os erros, as omissões e as justificativas devem
  ser mutuamente consistentes.
- Se uma inconsistência impedir uma avaliação confiável, solicite revisão
  em vez de atribuir uma pontuação arbitrária.

Não gere um alerta do tipo "gabarito_inconsistente" quando sua própria análise confirmar que o resultado apresentado no gabarito está matematicamente correto.

Antes de emitir esse alerta, resolva independentemente o problema e compare o resultado obtido com o gabarito original.

Se ambos forem equivalentes, não emita o alerta, mesmo que o estudante tenha apresentado uma resposta diferente ou cometido erros durante o desenvolvimento.

Um erro do estudante não constitui evidência de inconsistência do gabarito.

A avaliação de cada critério deve considerar a operação matemática
exigida por ele, e não apenas a aparência ou o formato do resultado.

Se um critério exigir uma transformação algébrica correta, não
classifique como atendido quando a transformação apresentada
estiver matematicamente incorreta.

A identificação de um erro em alertas, justificativas ou observações
gerais deve ser refletida também na pontuação e no status do
critério correspondente.

Não classifique simultaneamente uma operação como correta e
incorreta em diferentes partes da avaliação.

Quando houver erro em uma etapa, avalie separadamente as etapas
posteriores. Uma operação posterior matematicamente correta pode
receber pontuação mesmo quando utiliza um resultado intermediário
incorreto, desde que o critério não exija que esse resultado esteja
correto.

Quando uma etapa posterior executar corretamente uma operação
matemática sobre um resultado intermediário incorreto, avalie
essa operação de forma independente.

Não atribua null nem solicite revisão apenas porque o resultado
intermediário diverge do gabarito.

Se o critério exigir somente a execução correta da operação
posterior, atribua a pontuação correspondente normalmente.

A divergência com o gabarito não constitui, isoladamente,
motivo para revisão humana.

Utilize o status revisao_necessaria somente quando existir
uma dúvida real que impeça uma avaliação confiável do critério.

Verifique independentemente cada operação aritmética apresentada
pelo estudante, incluindo adições, subtrações, multiplicações
e divisões.

Não considere uma operação correta apenas porque sua estrutura
algébrica é adequada.

A execução numérica também precisa estar correta.

Se o estudante escrever uma operação com resultado incorreto,
não conceda os pontos referentes à execução dessa operação.

Não confunda coincidência entre a resposta final e o gabarito
com uma resolução matematicamente válida.

Se a resposta final coincidir com o gabarito, mas não decorrer
corretamente do desenvolvimento apresentado, avalie separadamente
o resultado final e o procedimento, respeitando os critérios
originais.

ANÁLISE CONFORME O MODO:

Modo desenvolvimento:
Analise o desenvolvimento apresentado pelo estudante.
Verifique a validade dos procedimentos, das justificativas, das operações
e das conclusões intermediárias.
Considere o raciocínio demonstrado, não apenas o resultado final.

Modo final:
Avalie somente a resposta final apresentada, comparando-a ao gabarito e à
referência matemática. Aceite expressões equivalentes, notações diferentes,
respostas em texto e aproximações compatíveis com o enunciado. Não exija
desenvolvimento, não infira o raciocínio e não atribua pontos por etapas.
Para o critério único de resposta final, atribua pontuação máxima se a resposta
for equivalente ao gabarito, zero se for claramente incorreta e revisão
necessária se a comparação for ambígua. Não dê pontuação parcial nesse modo.

PONTUAÇÃO:

- Atendido: pontuação máxima do critério.
- Parcialmente atendido: pontuação positiva inferior à máxima.
- Não atendido: zero ponto.
- Não avaliável: pontuação nula (null) e necessidade de revisão.
- Revisão necessária: pontuação nula (null) e necessidade de revisão.

A pontuação sugerida deve respeitar os critérios oficiais.
Quando não for possível avaliar um critério com segurança, utilize null
e explique o motivo.

SAÍDA:

Produza exclusivamente um objeto JSON compatível com o contrato de saída
fornecido pela aplicação.

Não inclua comentários, introduções ou blocos Markdown.
"""

    if dados.get("modo") == "final":
        instrucoes = """
Você compara respostas finais de questões de prova.

Para cada item, compare exclusivamente "resposta_estudante" com "gabarito" e
com o enunciado. Aceite formas equivalentes, notações diferentes, alternativas
válidas e aproximações numéricas compatíveis. Não avalie nem invente raciocínio,
etapas, justificativas ou pontos de procedimento.

O item tem um único critério de resposta final: atribua a pontuação máxima se
a resposta for equivalente ao gabarito; zero se for claramente incorreta; e
revisão necessária com pontuação null somente se houver ambiguidade real.
Não atribua pontuação parcial. Preserve os identificadores Q1...Q10 e o nome,
valor máximo e formato dos critérios recebidos.

Retorne exclusivamente o objeto JSON exigido pelo contrato, sem Markdown.
"""

    dados_json = json.dumps(
        dados,
        ensure_ascii=False,
        indent=2
    )

    return f"""
{instrucoes}

DADOS DA CORREÇÃO:

{dados_json}
"""

def carregar_schema_saida():
    caminho_schema = (
        Path(__file__).parent
        / "dados"
        / "saida.schema.json"
    )

    with open(caminho_schema, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def adaptar_schema_gemini(schema):
    schema_adaptado = copy.deepcopy(schema)

    def processar(objeto):
        if isinstance(objeto, dict):

            # Remove propriedades não suportadas
            objeto.pop("$schema", None)
            objeto.pop("minLength", None)

            # Converte const em enum
            if "const" in objeto:
                valor = objeto.pop("const")
                objeto["enum"] = [valor]

            # Processa propriedades internas
            for valor in objeto.values():
                processar(valor)

        elif isinstance(objeto, list):
            for elemento in objeto:
                processar(elemento)

    processar(schema_adaptado)

    return schema_adaptado


def gerar_correcao(dados):
    prompt = construir_prompt_correcao(dados)

    schema = carregar_schema_saida()
    schema_gemini = adaptar_schema_gemini(schema)

    with criar_cliente() as cliente:
        resposta = cliente.models.generate_content(
            model=MODELO_GEMINI,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=schema_gemini,
            ),
        )

    resultado = json.loads(resposta.text)

    # A correção da prova inteira usa uma chamada ao modelo, mas a barreira
    # matemática continua isolada por questão para não misturar evidências.
    correcoes_por_item = dados.get("correcoes_por_item")
    if correcoes_por_item:
        dados_por_letra = {
            item["letra_item"]: item for item in correcoes_por_item
        }
        encontrados = [item.get("letra") for item in resultado.get("itens", [])]
        esperados = set(dados_por_letra)
        if len(encontrados) != len(set(encontrados)) or set(encontrados) != esperados:
            return _suspender_correcao_matematica(
                resultado,
                "A resposta do corretor não corresponde exatamente às questões enviadas.",
            )

        alertas = list(resultado.get("alertas", []))
        itens_corrigidos = []
        pontuacoes_sugeridas_ia = {}
        for item_resposta in resultado.get("itens", []):
            dados_item = dados_por_letra[item_resposta["letra"]]
            pontuacoes_sugeridas_ia[item_resposta["letra"]] = {
                criterio.get("criterio"): criterio.get("pontos_sugeridos")
                for criterio in item_resposta.get("criterios", [])
            }
            subresultado = {
                "status": resultado.get("status"),
                "resumo": resultado.get("resumo", {}),
                "itens": [item_resposta],
                "alertas": [
                    alerta for alerta in resultado.get("alertas", [])
                    if alerta.get("item") == item_resposta["letra"]
                ],
                "observacoes_gerais": resultado.get("observacoes_gerais", ""),
            }
            subresultado = aplicar_barreira_matematica(subresultado, dados_item)
            itens_corrigidos.extend(subresultado["itens"])
            for alerta in subresultado["alertas"]:
                if alerta.get("item") is None:
                    alerta["item"] = item_resposta["letra"]
                alertas.append(alerta)

        resultado["itens"] = itens_corrigidos
        resultado["alertas"] = []
        vistos = set()
        for alerta in alertas:
            chave = json.dumps(alerta, ensure_ascii=False, sort_keys=True)
            if chave not in vistos:
                vistos.add(chave)
                resultado["alertas"].append(alerta)
        resultado["status"] = (
            "corrigido"
            if all(item.get("status") == "avaliado" for item in itens_corrigidos)
            else "revisao_necessaria"
        )
        resultado["_pontuacoes_sugeridas_ia"] = pontuacoes_sugeridas_ia
        return resultado

    return aplicar_barreira_matematica(resultado, dados)


questao_original = {
    "itens": [
        {
            "letra": "única",
            "valor": 1.0,
            "criterios_correcao": [
                {
                    "criterio": "Isolar corretamente o termo com a incógnita.",
                    "valor": 0.4
                },
                {
                    "criterio": "Realizar corretamente a divisão pelo coeficiente de x.",
                    "valor": 0.4
                },
                {
                    "criterio": "Apresentar o resultado final correto.",
                    "valor": 0.2
                }
            ]
        }
    ]
}


if __name__ == "__main__":

    dados = preparar_dados_correcao(
        enunciado = "Resolva a equação 2x+4=10.",
        resposta_estudante="""
        2x + 4 = 10
        2x = 10 - 4
        2x = 2
        x = 3
        """
        ,
        gabarito = "x = 3",
        criterios_correcao=[
            {
                "criterio": "Isolar corretamente o termo com a incógnita.",
                "valor": 0.4
            },
            {
                "criterio": "Realizar corretamente a divisão pelo coeficiente de x.",
                "valor": 0.4
            },
            {
                "criterio": "Apresentar o resultado final correto.",
                "valor": 0.2
            }
        ],
        letra_item="única",
        modo="desenvolvimento",
        verificar_matematica=True,
    )

    print("Enviando questão para a Gemini...\n")

    resultado = gerar_correcao(dados)

    print("Resposta recebida:\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))

    print("\nValidando correção...\n")

    resultado_validacao = calcular_nota(
        resultado,
        questao_original
    )

    print(json.dumps(
        resultado_validacao,
        ensure_ascii=False,
        indent=2
    ))
