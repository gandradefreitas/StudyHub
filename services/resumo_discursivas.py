def resumir_correcao_discursiva(tentativa):
    """Normaliza notas legadas e provisórias para Histórico, Notas e relatórios."""
    parecer = tentativa.get("resultado_correcao") or {}
    status = tentativa["status"]
    nota, maxima = tentativa["nota_total"], tentativa["nota_maxima"]

    if parecer.get("status") == "provisoria":
        situacao = "Correção provisória"
        nota = parecer.get("nota_provisoria")
    elif parecer.get("status") == "revisao_necessaria":
        situacao = "Revisão necessária"
    elif parecer.get("status") == "falha_definitiva":
        situacao = "Correção indisponível"
    elif status == "corrigida" or parecer.get("status") == "corrigida":
        situacao = "Corrigida"
        if nota is None:
            nota = parecer.get("nota")
    elif status == "finalizada":
        situacao = "Aguardando correção"
    else:
        situacao = "Em andamento"

    if maxima is None:
        maxima = parecer.get("nota_maxima")
    if nota is not None and maxima is not None:
        resultado = f"{nota}/{maxima}"
    elif parecer.get("correcao"):
        resultado = "Parecer disponível"
    elif situacao == "Correção indisponível":
        resultado = situacao
    else:
        resultado = "Correção pendente" if status == "finalizada" else "—"
    return {"situacao": situacao, "nota_total": nota, "nota_maxima": maxima,
            "resultado_formatado": resultado}
