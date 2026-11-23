"""Relatório pessoal em PDF, a partir dos dados agregados de exportação."""

import io
from datetime import date, datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from services.resumo_discursivas import resumir_correcao_discursiva


def gerar_relatorio_pdf(dados):
    memoria = io.BytesIO()

    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.7 * cm,
        bottomMargin=2 * cm,
        title="Relatório de dados - StudyHub",
        author="StudyHub"
    )

    estilos = getSampleStyleSheet()

    estilos.add(
        ParagraphStyle(
            name="TituloStudyHub",
            parent=estilos["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=5
        )
    )

    estilos.add(
        ParagraphStyle(
            name="SubtituloStudyHub",
            parent=estilos["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=18
        )
    )

    estilos.add(
        ParagraphStyle(
            name="SecaoStudyHub",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TextoStudyHub",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155"),
            wordWrap="LTR"
        )
    )

    estilos.add(
        ParagraphStyle(
            name="TextoPequenoStudyHub",
            parent=estilos["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#334155"),
            wordWrap="LTR"
        )
    )

    estilos.add(
        ParagraphStyle(
            name="CabecalhoTabelaStudyHub",
            parent=estilos["TextoPequenoStudyHub"],
            fontName="Helvetica-Bold",
            textColor=colors.white
        )
    )

    estilos.add(
        ParagraphStyle(
            name="IndicadorValorStudyHub",
            parent=estilos["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563EB"),
            spaceAfter=4
        )
    )

    estilos.add(
        ParagraphStyle(
            name="IndicadorRotuloStudyHub",
            parent=estilos["Normal"],
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B")
        )
    )

    elementos = []

    # --------------------------------------------------
    # FUNÇÕES AUXILIARES
    # --------------------------------------------------

    def formatar_texto(valor):

        if valor is None or valor == "":
            return "—"

        if isinstance(valor, bool):
            return "Sim" if valor else "Não"

        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M")

        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor)

        # Evita que caracteres especiais sejam interpretados
        # como tags HTML pelo ReportLab.
        from xml.sax.saxutils import escape

        return escape(texto)

    def formatar_data(valor, incluir_hora=False):

        if valor is None:
            return "—"

        if isinstance(valor, datetime):
            formato = (
                "%d/%m/%Y %H:%M"
                if incluir_hora
                else "%d/%m/%Y"
            )

            return valor.strftime(formato)

        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor)

        try:
            data = datetime.fromisoformat(texto)

            formato = (
                "%d/%m/%Y %H:%M"
                if incluir_hora
                else "%d/%m/%Y"
            )

            return data.strftime(formato)

        except (ValueError, TypeError):
            return texto

    def formatar_duracao(valor):

        if valor is None:
            return "—"

        if isinstance(valor, str):

            partes = valor.split(":")

            try:
                if len(partes) == 3:
                    horas, minutos, segundos = map(int, partes)

                    total_segundos = (
                        horas * 3600
                        + minutos * 60
                        + segundos
                    )

                elif len(partes) == 2:
                    minutos, segundos = map(int, partes)

                    total_segundos = (
                        minutos * 60
                        + segundos
                    )

                else:
                    total_segundos = int(valor)

            except ValueError:
                return valor

        else:
            try:
                total_segundos = int(valor)
            except (ValueError, TypeError):
                return str(valor)

        horas, resto = divmod(total_segundos, 3600)
        minutos, segundos = divmod(resto, 60)

        partes_formatadas = []

        if horas:
            partes_formatadas.append(f"{horas}h")

        if minutos:
            partes_formatadas.append(f"{minutos}min")

        if segundos and not horas:
            partes_formatadas.append(f"{segundos}s")

        return " ".join(partes_formatadas) or "0min"

    def adicionar_secao(titulo):

        elementos.append(
            Paragraph(
                titulo,
                estilos["SecaoStudyHub"]
            )
        )

    def adicionar_tabela(cabecalho, linhas, larguras):

        if not linhas:
            return

        dados_tabela = [
            [
                Paragraph(
                    formatar_texto(coluna),
                    estilos["CabecalhoTabelaStudyHub"]
                )
                for coluna in cabecalho
            ]
        ]

        for linha in linhas:

            dados_tabela.append([
                Paragraph(
                    formatar_texto(valor),
                    estilos["TextoPequenoStudyHub"]
                )
                for valor in linha
            ])

        tabela = Table(
            dados_tabela,
            colWidths=larguras,
            repeatRows=1,
            hAlign="LEFT"
        )

        tabela.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1E40AF")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F8FAFC")
                    ]
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        elementos.append(tabela)
        elementos.append(Spacer(1, 0.25 * cm))

    def adicionar_indicadores(indicadores):

        celulas = []

        for valor, rotulo in indicadores:
            valor_formatado = Paragraph(
                formatar_texto(valor),
                estilos["IndicadorValorStudyHub"]
            )

            rotulo_formatado = Paragraph(
                formatar_texto(rotulo),
                estilos["IndicadorRotuloStudyHub"]
            )

            celulas.append([
                valor_formatado,
                rotulo_formatado
            ])

        if not celulas:
            return

        largura_disponivel = A4[0] - 3.4 * cm
        largura_celula = largura_disponivel / len(celulas)

        tabela = Table(
            [celulas],
            colWidths=[largura_celula] * len(celulas),
            hAlign="LEFT"
        )

        tabela.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F1F5F9")
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#E2E8F0")
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                )
            ])
        )

        elementos.append(tabela)
        elementos.append(Spacer(1, 0.35 * cm))

    # --------------------------------------------------
    # DADOS DO USUÁRIO
    # --------------------------------------------------

    usuario = dados.get("usuario")
    configuracoes = dados.get("configuracoes")

    if usuario:
        nome = usuario["nome"]
        email = usuario["email"]
    else:
        nome = "Usuário"
        email = None

    if configuracoes:
        tema = configuracoes["tema"]
        meta_estudo = configuracoes["meta_estudo"]
        meta_questoes = configuracoes["meta_questoes"]
    else:
        tema = "sistema"
        meta_estudo = 60
        meta_questoes = 20

    estudos = dados.get("estudos") or []
    tarefas = dados.get("tarefas") or []
    anotacoes = dados.get("anotacoes") or []
    resultados_provas = dados.get("resultados_provas") or []

    # --------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------

    elementos.append(
        Paragraph(
            "StudyHub",
            estilos["TituloStudyHub"]
        )
    )

    elementos.append(
        Paragraph(
            "Relatório de desempenho acadêmico",
            estilos["SubtituloStudyHub"]
        )
    )

    elementos.append(
        Paragraph(
            f"Exportado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            estilos["TextoStudyHub"]
        )
    )

    elementos.append(Spacer(1, 0.3 * cm))

    adicionar_secao("Identificação")

    adicionar_tabela(
        ["Informação", "Valor"],
        [
            ["Nome", nome],
            ["E-mail", email],
            [
                "Meta diária de estudo",
                f"{meta_estudo} minutos"
            ],
            [
                "Meta diária de questões",
                f"{meta_questoes} questões"
            ]
        ],
        [5 * cm, 10 * cm]
    )

    # --------------------------------------------------
    # RESUMO DO DESEMPENHO
    # --------------------------------------------------

    adicionar_secao("Resumo do desempenho")

    estatisticas = dados["estatisticas"]
    resumo = estatisticas["resumo"]
    tempo_total = estatisticas["tempo_total_segundos"]

    total_questoes = (
            resumo["acertos"]
            + resumo["erros"]
    )

    total_provas = resumo["provas"]

    if total_questoes > 0:
        taxa_acerto = (
                              resumo["acertos"] / total_questoes
                      ) * 100
    else:
        taxa_acerto = 0

    adicionar_indicadores([
        (
            total_questoes,
            "Questões resolvidas"
        ),
        (
            total_provas,
            "Provas realizadas"
        ),
        (
            f"{taxa_acerto:.1f}%".replace(".", ","),
            "Taxa de acerto"
        ),
        (
            formatar_duracao(tempo_total),
            "Tempo total"
        )
    ])

    # --------------------------------------------------
    # DESEMPENHO EM QUESTÕES
    # --------------------------------------------------

    adicionar_secao("Desempenho total de questões objetivas")
    questoes_respondidas = estatisticas["total_questoes"]
    acertos = estatisticas["total_acertos"]
    aproveitamento = acertos * 100 / questoes_respondidas if questoes_respondidas else 0
    adicionar_indicadores([
        (questoes_respondidas, "Questões resolvidas"),
        (acertos, "Acertos"),
        (questoes_respondidas - acertos, "Erros"),
        (f"{aproveitamento:.1f}%".replace(".", ","), "Aproveitamento"),
    ])

    evolucao = estatisticas["evolucao_mensal"]
    if evolucao:
        mes = date.fromisoformat(evolucao[0]["data"]).strftime("%m/%Y")
        adicionar_secao(f"Evolução dos estudos — {mes}")
        dias_com_atividade = [
            [formatar_data(dia["data"]), formatar_duracao(dia["duracao"])]
            for dia in evolucao if dia["duracao"]
        ]
        if dias_com_atividade:
            adicionar_tabela(["Dia", "Tempo estudado"], dias_com_atividade, [8 * cm, 8 * cm])
        else:
            elementos.append(Paragraph("Nenhum tempo registrado neste mês.", estilos["TextoStudyHub"]))

    # --------------------------------------------------
    # DESEMPENHO POR ÁREA — PROVAS
    # --------------------------------------------------

    for prova, areas in estatisticas["desempenho_provas"].items():
        adicionar_secao(f"{prova} — Questões objetivas por área")
        if not areas:
            elementos.append(Paragraph("Nenhuma questão respondida.", estilos["TextoStudyHub"]))
            continue
        adicionar_tabela(
            ["Área", "Questões", "Acertos", "Erros", "Aproveitamento"],
            [[area, item["questoes"], item["acertos"], item["questoes"] - item["acertos"],
              f'{item["acertos"] * 100 / item["questoes"]:.1f}%'.replace(".", ",")]
             for area, item in sorted(areas.items())],
            [6 * cm, 2 * cm, 2 * cm, 2 * cm, 4 * cm],
        )

    # --------------------------------------------------
    # DESEMPENHO NAS QUESTÕES PRATICADAS
    # --------------------------------------------------

    adicionar_secao("Desempenho nas questões")

    desempenho_questoes = estatisticas["questoes_praticadas_por_area"]

    if desempenho_questoes:

        linhas = []

        for area, resultado in sorted(
                desempenho_questoes.items(),
                key=lambda item: item[1]["porcentagem"],
                reverse=True
        ):
            linhas.append([
                area,
                resultado["questoes"],
                resultado["acertos"],
                resultado["erros"],
                f'{resultado["porcentagem"]:.1f}%'.replace(".", ",")
            ])

        adicionar_tabela(
            [
                "Área do conhecimento",
                "Questões",
                "Acertos",
                "Erros",
                "Aproveitamento"
            ],
            linhas,
            [
                5.0 * cm,
                2.0 * cm,
                2.0 * cm,
                2.0 * cm,
                3.0 * cm
            ]
        )

    else:

        elementos.append(
            Paragraph(
                "Ainda não há questões praticadas suficientes "
                "para apresentar esta análise.",
                estilos["TextoStudyHub"]
            )
        )

        elementos.append(Spacer(1, 0.25 * cm))

    # --------------------------------------------------
    # ANÁLISE DETALHADA DAS QUESTÕES
    # --------------------------------------------------

    adicionar_secao("Análise detalhada das questões")

    criterios = [
        ("dificuldade", "Desempenho por dificuldade"),
        ("competencia", "Desempenho por competência"),
        ("habilidade", "Desempenho por habilidade"),
        ("lingua", "Desempenho por idioma")
    ]

    for criterio, titulo in criterios:

        desempenho = estatisticas["analise_questoes_praticadas"][criterio]

        if not desempenho:
            continue

        adicionar_secao(titulo)

        linhas = []

        for categoria, resultado in sorted(
                desempenho.items(),
                key=lambda item: item[1]["porcentagem"],
                reverse=True
        ):
            linhas.append([
                categoria,
                resultado["questoes"],
                resultado["acertos"],
                resultado["erros"],
                f'{resultado["porcentagem"]:.1f}%'.replace(".", ",")
            ])

        adicionar_tabela(
            [
                "Categoria",
                "Questões",
                "Acertos",
                "Erros",
                "Aproveitamento"
            ],
            linhas,
            [
                5.0 * cm,
                2.0 * cm,
                2.0 * cm,
                2.0 * cm,
                3.0 * cm
            ]
        )

    # --------------------------------------------------
    # ANÁLISE DO DESEMPENHO
    # --------------------------------------------------

    adicionar_secao("Análise do desempenho")

    destaques = []
    for rotulo, chave in (("Ponto forte", "ponto_forte"), ("Ponto de atenção", "ponto_atencao")):
        if estatisticas[chave]:
            prova, area, percentual = estatisticas[chave]
            destaques.append([rotulo, f"{prova} — {area} — {percentual:.1f}%".replace(".", ",")])
    if destaques:
        adicionar_tabela(["Indicador", "Resultado"], destaques, [6 * cm, 10 * cm])
    else:
        elementos.append(Paragraph("Nenhuma questão respondida.", estilos["TextoStudyHub"]))

    # --------------------------------------------------
    # RESULTADOS DAS PROVAS
    # --------------------------------------------------

    if resultados_provas:

        adicionar_secao("Resultados das provas")

        linhas = []

        for resultado in resultados_provas:
            acertos = resultado["acertos"]
            erros = resultado["erros"]
            nao_respondidas = resultado["nao_respondidas"]
            total = resultado["total"]
            tempo_gasto = resultado["tempo_gasto"]
            porcentagem = resultado["porcentagem"]
            data_realizacao = resultado["data_realizacao"]

            linhas.append([
                resultado["prova"],
                f"{acertos}/{total}",
                erros,
                nao_respondidas,
                f"{float(porcentagem):.2f}%".replace(".", ","),
                formatar_duracao(tempo_gasto),
                formatar_data(
                    data_realizacao,
                    incluir_hora=True
                )
            ])

        adicionar_tabela(
            [
                "Prova",
                "Acertos",
                "Erros",
                "Em branco",
                "Aproveitamento",
                "Duração",
                "Realização"
            ],
            linhas,
            [
                3.0 * cm,
                1.5 * cm,
                1.2 * cm,
                1.5 * cm,
                2.0 * cm,
                1.5 * cm,
                3.3 * cm
            ]
        )

    # --------------------------------------------------
    # RODAPÉ
    # --------------------------------------------------

    def adicionar_rodape(canvas, doc):

        canvas.saveState()

        largura, altura = A4

        canvas.setStrokeColor(
            colors.HexColor("#CBD5E1")
        )

        canvas.line(
            1.7 * cm,
            1.5 * cm,
            largura - 1.7 * cm,
            1.5 * cm
        )

        canvas.setFont("Helvetica", 8)

        canvas.setFillColor(
            colors.HexColor("#64748B")
        )

        canvas.drawString(
            1.7 * cm,
            1 * cm,
            "StudyHub | Relatório pessoal"
        )

        canvas.drawRightString(
            largura - 1.7 * cm,
            1 * cm,
            f"Página {doc.page}"
        )

        canvas.restoreState()

    discursivas = [prova for prova in dados["provas_discursivas"] if prova["data_finalizacao"]]
    if discursivas:
        adicionar_secao("Resultados das provas discursivas")
        linhas = []
        for prova in discursivas:
            resumo_nota = resumir_correcao_discursiva(prova)
            resultado = resumo_nota["resultado_formatado"]
            if resumo_nota["situacao"] == "Correção provisória":
                resultado += " (provisória)"
            linhas.append([
                f'{prova["instituicao"]} {prova["ano"]} — {prova["fase"]} — {prova["disciplina"]}',
                resultado,
                formatar_data(prova["data_finalizacao"], incluir_hora=True),
            ])
        adicionar_tabela(["Prova", "Resultado", "Finalização"], linhas, [8 * cm, 4 * cm, 4 * cm])

    adicionar_secao("Leitura e produção de texto")
    leituras = dados.get("leituras_idiomas") or []
    redacoes_concluidas = dados.get("redacoes") or []
    adicionar_tabela(
        ["Indicador", "Total"],
        [
            ["Leituras concluídas", len(leituras)],
            ["Palavras lidas", sum(leitura["palavras"] for leitura in leituras)],
            ["Redações enviadas", len(redacoes_concluidas)],
            ["Provas discursivas finalizadas", sum(
                prova["data_finalizacao"] is not None for prova in dados.get("provas_discursivas", [])
            )],
        ],
        [11 * cm, 5.5 * cm],
    )
    if redacoes_concluidas:
        adicionar_tabela(
            ["Prova", "Tema", "Nota estimada"],
            [[envio["instituicao"], envio["tema"], "Pendente" if envio["nota"] is None else
              (f'{envio["nota"] / 10:g} / 10' if envio["instituicao"] == "ITA" else f'{envio["nota"]} / 1000')]
             for envio in redacoes_concluidas],
            [2.5 * cm, 10.5 * cm, 3.5 * cm],
        )

    documento.build(
        elementos,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )

    return memoria.getvalue()

