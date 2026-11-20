"""Análise de procedimentos com várias etapas."""

from .contrato import (
    STATUS_CONDICIONAL,
    STATUS_CORRETO,
    STATUS_INCORRETO,
    STATUS_INDETERMINADO,
    STATUS_INVALIDO,
    _ERROS_DE_ENTRADA,
    _resultado_invalido,
    montar_resultado,
)
from .diagnostico import _diagnosticar
from .equacoes import interpretar_equacao
from .interpretador import interpretar_expressao
from .tempo import _interface_protegida
from .transformacoes import (
    _eh_equacao,
    verificar_transformacao,
)


# ----------------------------------------------------------------
# Análise de procedimentos
# ----------------------------------------------------------------
_MAX_ETAPAS = 30


def _erro_de_leitura(etapa):
    """
    Retorna None se a etapa pode ser interpretada, ou o texto
    do erro caso contrário.
    """

    try:
        if _eh_equacao(etapa):
            interpretar_equacao(etapa)
        else:
            interpretar_expressao(etapa)

    except _ERROS_DE_ENTRADA as erro:
        return str(erro)

    return None


@_interface_protegida(fator=4)
def analisar_procedimento(etapas):
    """
    Verifica cada transformação de uma sequência de etapas.

    etapas: lista de expressões ou equações, na ordem escrita.

    Cada transformação é avaliada em relação à etapa anterior do
    estudante. Um erro em uma etapa não invalida as seguintes.

    detalhes:
        transformacoes: uma entrada por transformação, com
            etapa (a etapa produzida, contada de 1), de, para,
            apos_erro e o resultado completo.
        primeiro_erro, etapas_incorretas.
        corretas_apos_erro: transformações corretas feitas depois
            de um erro (base para crédito parcial).
        equivalencia_global: primeira etapa comparada com a última.
        contagem: quantidade de transformações por status.
    """

    try:
        if not isinstance(etapas, (list, tuple)) or len(etapas) < 2:
            raise ValueError(
                "O procedimento deve ser uma lista com pelo menos "
                "duas etapas."
            )

        if len(etapas) > _MAX_ETAPAS:
            raise ValueError(
                f"O procedimento deve ter no máximo {_MAX_ETAPAS} etapas."
            )

    except _ERROS_DE_ENTRADA as erro:
        return _resultado_invalido(erro)

    erros_de_leitura = [_erro_de_leitura(etapa) for etapa in etapas]

    transformacoes = []
    houve_erro = False

    for indice in range(1, len(etapas)):

        anterior = etapas[indice - 1]
        novo = etapas[indice]

        if (
            erros_de_leitura[indice - 1] is not None
            or erros_de_leitura[indice] is not None
        ):
            culpada = (
                indice - 1
                if erros_de_leitura[indice - 1] is not None
                else indice
            )

            resultado = montar_resultado(
                STATUS_INVALIDO,
                f"A etapa {culpada + 1} não pôde ser interpretada: "
                f"{erros_de_leitura[culpada]}",
                detalhes={"etapa_invalida": culpada + 1}
            )

        else:
            resultado = verificar_transformacao(anterior, novo)

        diagnostico = None

        if resultado["status"] in (STATUS_INCORRETO, STATUS_CONDICIONAL):
            diagnostico = _diagnosticar(anterior, novo, resultado)

        transformacoes.append({
            "etapa": indice + 1,
            "de": str(anterior),
            "para": str(novo),
            "apos_erro": houve_erro,
            "resultado": resultado,
            "diagnostico": diagnostico
        })

        if resultado["status"] == STATUS_INCORRETO:
            houve_erro = True

    contagem = {
        STATUS_CORRETO: 0,
        STATUS_CONDICIONAL: 0,
        STATUS_INCORRETO: 0,
        STATUS_INDETERMINADO: 0,
        STATUS_INVALIDO: 0
    }

    for transformacao in transformacoes:
        contagem[transformacao["resultado"]["status"]] += 1

    etapas_incorretas = [
        t["etapa"]
        for t in transformacoes
        if t["resultado"]["status"] == STATUS_INCORRETO
    ]

    corretas_apos_erro = [
        t["etapa"]
        for t in transformacoes
        if t["apos_erro"]
        and t["resultado"]["status"] in (STATUS_CORRETO, STATUS_CONDICIONAL)
    ]

    # Coerência entre o ponto de partida e o de chegada.
    equivalencia_global = None

    if erros_de_leitura[0] is None and erros_de_leitura[-1] is None:
        global_ = verificar_transformacao(etapas[0], etapas[-1])

        equivalencia_global = {
            "status": global_["status"],
            "tipo": global_["detalhes"].get("tipo"),
            "justificativa": global_["justificativa"]
        }

    restricoes = []
    condicoes = []

    for transformacao in transformacoes:
        restricoes += transformacao["resultado"]["restricoes"]
        condicoes += transformacao["resultado"]["condicoes"]

    detalhes = {
        "total_etapas": len(etapas),
        "transformacoes": transformacoes,
        "contagem": contagem,
        "primeiro_erro": etapas_incorretas[0] if etapas_incorretas else None,
        "etapas_incorretas": etapas_incorretas,
        "corretas_apos_erro": corretas_apos_erro,
        "equivalencia_global": equivalencia_global
    }

    restricoes = list(dict.fromkeys(restricoes))
    condicoes = list(dict.fromkeys(condicoes))

    if contagem[STATUS_INCORRETO]:
        quantidade = contagem[STATUS_INCORRETO]

        return montar_resultado(
            STATUS_INCORRETO,
            f"O procedimento possui {quantidade} transformação(ões) "
            f"incorreta(s); o primeiro erro está na etapa "
            f"{etapas_incorretas[0]}.",
            restricoes=restricoes,
            condicoes=condicoes,
            detalhes=detalhes
        )

    if contagem[STATUS_INVALIDO] or contagem[STATUS_INDETERMINADO]:
        return montar_resultado(
            STATUS_INDETERMINADO,
            "Nenhum erro foi comprovado, mas algumas transformações "
            "não puderam ser verificadas.",
            restricoes=restricoes,
            condicoes=condicoes,
            detalhes=detalhes
        )

    if contagem[STATUS_CONDICIONAL]:
        return montar_resultado(
            STATUS_CONDICIONAL,
            "Todas as transformações são válidas, mas algumas exigem "
            "condições adicionais.",
            restricoes=restricoes,
            condicoes=condicoes,
            detalhes=detalhes
        )

    return montar_resultado(
        STATUS_CORRETO,
        "Todas as transformações preservam a equivalência.",
        restricoes=restricoes,
        condicoes=condicoes,
        detalhes=detalhes
    )
