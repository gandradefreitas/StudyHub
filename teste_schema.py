import copy
import json

from jsonschema import validate
from jsonschema.exceptions import ValidationError



from validador import calcular_nota, validar_alertas, validar_alertas_duplicados, validar_pontuacoes, \
    validar_consistencia_status, validar_soma_criterios, validar_consistencia_status_itens

# Carrega o Schema
with open(
    "dados/saida.schema.json",
    "r",
    encoding="utf-8"
) as arquivo:

    schema = json.load(arquivo)


# Simulação da resposta do Gemini
resposta_ia = {

    "versao_contrato": "1.0",

    "status": "corrigido",

    "resumo": {

        "pontos_fortes": [
            "O estudante desenvolveu corretamente o primeiro equilíbrio químico.",
            "Identificou a relação entre as concentrações no segundo equilíbrio."
        ],

        "pontos_a_melhorar": [
            "Demonstrar como foi encontrada a quantidade de reagente adicionada.",
            "Apresentar todas as concentrações solicitadas."
        ]
    },

    "itens": [

        {
            "letra": "a",
            "status": "avaliado",
            "pontos_maximos": 3.3,
            "justificativa": "Resolução completa e correta.",

            "criterios": [

                {
                    "criterio": "Montar a expressão de Kc.",
                    "pontos_maximos": 1.6,
                    "pontos_sugeridos": 1.6,
                    "status": "atendido",
                    "justificativa": "Expressão de equilíbrio corretamente construída.",

                    "evidencias": [
                        {
                            "trecho": "Kc = (2x)² / (1-x)",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],
                    "omissoes": []
                },

                {
                    "criterio": "Determinar as concentrações do primeiro equilíbrio.",
                    "pontos_maximos": 1.7,
                    "pontos_sugeridos": 1.7,
                    "status": "atendido",
                    "justificativa": "Concentrações encontradas corretamente.",

                    "evidencias": [
                        {
                            "trecho": "[B] = 0.5 e [C] = 1.0",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],
                    "omissoes": []
                }
            ]
        },

        {
            "letra": "b",
            "status": "avaliado",
            "pontos_maximos": 3.3,
            "justificativa": "O estudante apresentou parte do desenvolvimento, mas não demonstrou completamente o cálculo de y.",

            "criterios": [

                {
                    "criterio": "Estabelecer as relações algébricas do segundo equilíbrio.",
                    "pontos_maximos": 1.6,
                    "pontos_sugeridos": 1.6,
                    "status": "atendido",
                    "justificativa": "As expressões das concentrações foram montadas corretamente.",

                    "evidencias": [
                        {
                            "trecho": "[B] = 0.5 + y - z",
                            "tipo": "evidencia_positiva"
                        },
                        {
                            "trecho": "[C] = 1 + 2z",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],
                    "omissoes": []
                },

                {
                    "criterio": "Determinar a quantidade de B adicionada.",
                    "pontos_maximos": 1.7,
                    "pontos_sugeridos": 0.8,
                    "status": "parcialmente_atendido",
                    "justificativa": "O estudante encontrou z, mas não demonstrou a relação necessária para determinar y.",

                    "evidencias": [
                        {
                            "trecho": "1 + 2z = 2",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],

                    "omissoes": [
                        {
                            "descricao": "Não apresentou a substituição na expressão [B] = 0.5 + y - z para determinar y."
                        }
                    ]
                }
            ]
        },

        {
            "letra": "c",
            "status": "avaliado",
            "pontos_maximos": 3.4,
            "justificativa": "O estudante apresentou somente uma das concentrações solicitadas.",

            "criterios": [

                {
                    "criterio": "Aplicar a condição de igualdade entre as concentrações.",
                    "pontos_maximos": 1.7,
                    "pontos_sugeridos": 1.7,
                    "status": "atendido",
                    "justificativa": "A concentração de B foi identificada corretamente.",

                    "evidencias": [
                        {
                            "trecho": "[B] = 2.0 mol/L",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],
                    "omissoes": []
                },

                {
                    "criterio": "Apresentar as concentrações finais de B e C.",
                    "pontos_maximos": 1.7,
                    "pontos_sugeridos": 0.0,
                    "status": "nao_atendido",
                    "justificativa": "A concentração de C não foi apresentada.",

                    "evidencias": [
                        {
                            "trecho": "[B] = 2.0 mol/L",
                            "tipo": "evidencia_positiva"
                        }
                    ],

                    "erros": [],

                    "omissoes": [
                        {
                            "descricao": "Não apresentou explicitamente [C] = 2.0 mol/L."
                        }
                    ]
                }
            ]
        }
    ],

    "alertas": [],

    "observacoes_gerais": "Correção simulada para testar a estrutura do contrato."
}

print("\nTeste de pontuação máxima do item:")

valor_original = resposta_ia["itens"][0]["pontos_maximos"]

valores_teste = [
    0,
    -2,
    "3.3",
    True,
    float("inf"),
    float("nan")
]

for valor in valores_teste:

    resposta_ia["itens"][0]["pontos_maximos"] = valor

    resultado_teste = validar_pontuacoes(resposta_ia)

    print(f"Valor: {valor!r} | Erros: {resultado_teste['erros']}")

resposta_ia["itens"][0]["pontos_maximos"] = valor_original

questao_original = {

    "itens": [

        {
            "letra": "a",
            "valor": 3.3,
            "criterios_correcao": [
                {
                    "criterio": "Montar a expressão de Kc.",
                    "valor": 1.6
                },
                {
                    "criterio": "Determinar as concentrações do primeiro equilíbrio.",
                    "valor": 1.7
                }
            ]
        },

        {
            "letra": "b",
            "valor": 3.3,
            "criterios_correcao": [
                {
                    "criterio": "Estabelecer as relações algébricas do segundo equilíbrio.",
                    "valor": 1.6
                },
                {
                    "criterio": "Determinar a quantidade de B adicionada.",
                    "valor": 1.7
                }
            ]
        },

        {
            "letra": "c",
            "valor": 3.4,
            "criterios_correcao": [
                {
                    "criterio": "Aplicar a condição de igualdade entre as concentrações.",
                    "valor": 1.7
                },
                {
                    "criterio": "Apresentar as concentrações finais de B e C.",
                    "valor": 1.7
                }
            ]
        }

    ]

}

resposta_ia["itens"][0]["criterios"][0]["pontos_maximos"] = 1.6
questao_original["itens"][0]["criterios_correcao"][0]["valor"] = 1.6
questao_original["itens"][0]["valor"] = 3.3

# -----------------------------------------
# 1. VALIDAÇÃO ESTRUTURAL
# -----------------------------------------

try:

    validate(
        instance=resposta_ia,
        schema=schema
    )

    print("Resposta válida!")
    print("Estrutura da correção aprovada.")

except ValidationError as erro:

    print("Resposta inválida!")
    print("Motivo:", erro.message)

    raise SystemExit


# -----------------------------------------
# 2. VALIDAÇÃO COMPLETA
# -----------------------------------------

resultado_validacao = calcular_nota(
    resposta_ia,
    questao_original
)

# -----------------------------------------
# 3. RESULTADO
# -----------------------------------------

if resultado_validacao["erros"]:

    print("\nCorreção NÃO aprovada!")

    for erro in resultado_validacao["erros"]:
        print("-", erro)

    for revisao in resultado_validacao["revisoes"]:
        print("Revisão:", revisao)

elif resultado_validacao["revisoes"]:

    print("\nCorreção aguardando revisão!")

    for revisao in resultado_validacao["revisoes"]:
        print("-", revisao)

else:

    print("\nCorreção aprovada!")

    for alerta in resultado_validacao["alertas"]:
        print("Alerta:", alerta)


print("\nResultado do cálculo:")

if resultado_validacao["aprovado"]:

    print("Nota:", resultado_validacao["nota"])
    print("Nota máxima:", resultado_validacao["nota_maxima"])

    for item in resultado_validacao["itens"]:

        print(
            f"Item {item['letra']}: "
            f"{item['nota']}/{item['nota_maxima']}"
        )

else:

    print("Cálculo definitivo bloqueado.")


resposta_ia["alertas"] = [
    {
        "tipo": "enunciado_ambiguo",
        "descricao": "O enunciado apresenta uma ambiguidade.",
        "gravidade": "media",
        "item": None
    },
    {
        "tipo": "enunciado_ambiguo",
        "descricao": "O enunciado apresenta uma ambiguidade.",
        "gravidade": "media",
        "item": None
    }
]

resultado_duplicados = validar_alertas_duplicados(
    resposta_ia
)

print("\nTeste isolado de alertas duplicados:")
print(resultado_duplicados)

resultado = calcular_nota(resposta_ia, questao_original)

print("Aprovado:", resultado["aprovado"])
print("Nota:", resultado["nota"])
print("Alertas:", resultado["alertas"])
print("Revisões:", resultado["revisoes"])

resultado_alertas = validar_alertas(
    resposta_ia,
    questao_original
)

print("\nTeste isolado de validar_alertas:")
print(resultado_alertas)

print("\nErros da validação principal:")
print(resultado["erros"])

print("\nTestes de consistência dos status:")

# Teste 1: atendido com pontuação máxima
teste = copy.deepcopy(resposta_ia)
criterio = teste["itens"][0]["criterios"][0]

criterio["status"] = "atendido"
criterio["pontos_sugeridos"] = criterio["pontos_maximos"]

print(
    "Atendido com pontuação máxima:",
    validar_consistencia_status(teste)["erros"]
)


# Teste 2: atendido com pontuação parcial
teste = copy.deepcopy(resposta_ia)
criterio = teste["itens"][0]["criterios"][0]

criterio["status"] = "atendido"
criterio["pontos_sugeridos"] = 0.8

print(
    "Atendido com pontuação parcial:",
    validar_consistencia_status(teste)["erros"]
)


# Teste 3: parcialmente atendido com zero
teste = copy.deepcopy(resposta_ia)
criterio = teste["itens"][0]["criterios"][0]

criterio["status"] = "parcialmente_atendido"
criterio["pontos_sugeridos"] = 0

print(
    "Parcialmente atendido com zero:",
    validar_consistencia_status(teste)["erros"]
)


# Teste 4: não atendido com pontuação positiva
teste = copy.deepcopy(resposta_ia)
criterio = teste["itens"][0]["criterios"][0]

criterio["status"] = "nao_atendido"
criterio["pontos_sugeridos"] = 0.5

print(
    "Não atendido com pontuação positiva:",
    validar_consistencia_status(teste)["erros"]
)


# Teste 5: revisão necessária com pontuação numérica
teste = copy.deepcopy(resposta_ia)
criterio = teste["itens"][0]["criterios"][0]

criterio["status"] = "revisao_necessaria"
criterio["pontos_sugeridos"] = 0.5

print(
    "Revisão necessária com pontuação:",
    validar_consistencia_status(teste)["erros"]
)


print("\nTestes de soma dos critérios:")

# Teste 1: soma dentro do limite
teste = copy.deepcopy(resposta_ia)

print(
    "Soma dentro do limite:",
    validar_soma_criterios(teste)["erros"]
)


# Teste 2: soma acima do limite
teste = copy.deepcopy(resposta_ia)

teste["itens"][0]["criterios"][0]["pontos_sugeridos"] = 2.0
teste["itens"][0]["criterios"][1]["pontos_sugeridos"] = 1.7

print(
    "Soma acima do limite:",
    validar_soma_criterios(teste)["erros"]
)


# Teste 3: soma exatamente igual ao limite
teste = copy.deepcopy(resposta_ia)

teste["itens"][1]["criterios"][0]["pontos_sugeridos"] = 1.6
teste["itens"][1]["criterios"][1]["pontos_sugeridos"] = 1.7

print(
    "Soma exatamente igual ao limite:",
    validar_soma_criterios(teste)["erros"]
)

print("\nTestes de consistência dos status dos itens:")

# Teste 1: todos os critérios avaliados
teste = copy.deepcopy(resposta_ia)

print(
    "Todos os critérios avaliados:",
    validar_consistencia_status_itens(teste)["erros"]
)

# Teste 2: item precisa de revisão
teste = copy.deepcopy(resposta_ia)
teste["itens"][0]["status"] = "revisao_necessaria"
teste["itens"][0]["criterios"][0]["status"] = "revisao_necessaria"

print(
    "Item com revisão necessária:",
    validar_consistencia_status_itens(teste)["erros"]
)

# Teste 3: item não avaliável
teste = copy.deepcopy(resposta_ia)
teste["itens"][0]["status"] = "nao_avaliavel"
teste["itens"][0]["criterios"][0]["status"] = "nao_avaliavel"

print(
    "Item não avaliável:",
    validar_consistencia_status_itens(teste)["erros"]
)

# Teste 4: item marcado como avaliado, mas com critério pendente
teste = copy.deepcopy(resposta_ia)
teste["itens"][0]["status"] = "avaliado"
teste["itens"][0]["criterios"][0]["status"] = "revisao_necessaria"

print(
    "Item avaliado com critério pendente:",
    validar_consistencia_status_itens(teste)["erros"]
)

# Teste 5: item marcado para revisão, mas todos os critérios avaliados
teste = copy.deepcopy(resposta_ia)
teste["itens"][0]["status"] = "revisao_necessaria"

print(
    "Item em revisão sem critérios pendentes:",
    validar_consistencia_status_itens(teste)["erros"]
)