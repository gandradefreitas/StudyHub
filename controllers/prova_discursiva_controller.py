from services.provas_discursivas_service import (obter_prova_discursiva,)

from services.validacao_provas_discursivas import (validar_prova_discursiva,)

from database.respostas_discursivas_repository import (
    LimiteDiarioTentativaAtingido,
    obter_ou_criar_tentativa,
    obter_respostas,
    obter_status_tentativa,
    salvar_respostas_em_lote,
)


def carregar_prova_ita_segunda_fase(disciplina="matematica"):
    arquivos = {
        "matematica": "ita/2025/2_fase/matematica.json",
        "fisica": "ita/2025/2_fase/fisica.json",
        "quimica": "ita/2025/2_fase/quimica.json",
    }

    if disciplina not in arquivos:
        raise ValueError("Disciplina inválida para a segunda fase do ITA.")

    prova = obter_prova_discursiva(arquivos[disciplina])

    erros = validar_prova_discursiva(prova)

    if erros:
        raise ValueError(
            "A prova discursiva contém erros: "
            + "; ".join(erros)
        )

    return prova


def preparar_tentativa_discursiva(usuario_id, disciplina="Matemática"):
    instituicao = "ITA"
    ano = 2025
    fase = "Segunda Fase"

    try:
        tentativa_id = obter_ou_criar_tentativa(
            usuario_id=usuario_id,
            instituicao=instituicao,
            ano=ano,
            fase=fase,
            disciplina=disciplina,
        )
    except LimiteDiarioTentativaAtingido:
        return None, {}, "limite_diario"

    status = obter_status_tentativa(
        tentativa_id=tentativa_id,
        usuario_id=usuario_id,
        instituicao=instituicao,
        ano=ano,
        fase=fase,
        disciplina=disciplina,
    )

    respostas = obter_respostas(tentativa_id)

    return tentativa_id, respostas, status


def salvar_respostas_tentativa(tentativa_id, usuario_id, prova, dados_formulario, *, finalizar=False):
    campos_enviados = {chave for chave in dados_formulario if chave.startswith("resposta_")}
    if not campos_enviados.issubset(obter_campos_permitidos(prova)):
        raise ValueError("O formulário contém campos de resposta inválidos.")
    if any(len(dados_formulario[chave]) > 2000 for chave in campos_enviados):
        raise ValueError("Uma resposta ultrapassou o limite de 2.000 caracteres.")

    respostas = []

    for questao in prova.questoes:
        for indice, item in enumerate(questao.itens, start=1):
            chave = f"resposta_{questao.numero}_{indice}"

            # Preserva respostas de campos que não foram enviados.
            if chave not in dados_formulario:
                continue

            texto = dados_formulario.get(chave, "").strip()

            respostas.append(
                {
                    "questao_numero": questao.numero,
                    "item_letra": item.letra,
                    "resposta": texto,
                }
            )

    salvar_respostas_em_lote(
        tentativa_id=tentativa_id,
        usuario_id=usuario_id,
        prova=prova,
        respostas=respostas,
        finalizar=finalizar,
    )


def obter_campos_permitidos(prova):
    campos = set()

    for questao in prova.questoes:
        for indice, item in enumerate(questao.itens, start=1):
            campos.add(f"resposta_{questao.numero}_{indice}")

    return campos
