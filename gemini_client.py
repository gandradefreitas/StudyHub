import os
from google import genai
from google.genai import types

MODELO_GEMINI = "gemini-3.5-flash-lite"

def criar_cliente():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "A variável de ambiente GEMINI_API_KEY não foi configurada."
        )

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1)),
    )

def enviar_mensagem(mensagem):
    try:
        with criar_cliente() as cliente:
            resposta = cliente.models.generate_content(
                model=MODELO_GEMINI,
                contents=mensagem,
            )
            return resposta.text

    except Exception as erro:
        raise RuntimeError(
            "Erro ao comunicar com a API Gemini."
        ) from erro


if __name__ == "__main__":
    resposta = enviar_mensagem(
        "Responda apenas: Conexão com a API Gemini estabelecida!"
    )

    print("Resposta da Gemini:")
    print(resposta)