import os
from google import genai

MODELO_GEMINI = "gemini-3.5-flash-lite"

def criar_cliente():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "A variável de ambiente GEMINI_API_KEY não foi configurada."
        )

    return genai.Client(api_key=api_key)

def enviar_mensagem(mensagem):
    cliente = criar_cliente()

    try:
        resposta = cliente.models.generate_content(
            model=MODELO_GEMINI,
            contents=mensagem
        )

        return resposta.text

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao comunicar com a API Gemini: {erro}"
        ) from erro


if __name__ == "__main__":
    resposta = enviar_mensagem(
        "Responda apenas: Conexão com a API Gemini estabelecida!"
    )

    print("Resposta da Gemini:")
    print(resposta)