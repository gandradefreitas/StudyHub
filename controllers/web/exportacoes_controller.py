import json

from flask import Response, redirect, session, url_for

from services.exportacao_dados import obter_dados_relatorio
from services.relatorio_pdf import gerar_relatorio_pdf


def exportar_dados():

    if "usuario_id" not in session:
        return redirect(
            url_for("pagina_login")
        )

    dados = obter_dados_relatorio(
        session["usuario_id"]
    )

    arquivo = json.dumps(
        dados,
        ensure_ascii=False,
        indent=4,
        default=str
    )

    return Response(
        arquivo,
        mimetype="application/json",
        headers={
            "Content-Disposition":
                "attachment; filename=studyhub_dados.json"
        }
    )

def exportar_dados_pdf():

    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"))

    dados = obter_dados_relatorio(
        session["usuario_id"]
    )

    if not isinstance(dados, dict):
        return "Não foi possível gerar o relatório.", 500

    return Response(
        gerar_relatorio_pdf(dados),
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
                'attachment; filename="studyhub_relatorio.pdf"',
            "Cache-Control": "no-store"
        }
    )


def registrar_exportacoes(app):
    app.add_url_rule("/configuracoes/dados/exportar", view_func=exportar_dados)
    app.add_url_rule("/configuracoes/dados/exportar/pdf", view_func=exportar_dados_pdf)
