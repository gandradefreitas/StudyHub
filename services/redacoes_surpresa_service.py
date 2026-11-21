LIMITES = {"ENEM": 60 * 60, "ITA": 50 * 60}

TEMAS_SURPRESA = {
    "ENEM": (
        {
            "titulo": "Desafios para reduzir o desperdício de alimentos no Brasil",
            "apoio": (
                "Em uma feira, frutas maduras são separadas antes do fechamento. Parte ainda está própria para consumo, mas acaba descartada quando faltam embalagens, transporte ou pessoas para recolhê-la.",
                "Em casa, comprar para muitos dias pode economizar viagens ao mercado, mas exige planejar o preparo e armazenar bem cada alimento. Uma família pode reduzir perdas ao consultar o que já tem antes de fazer compras.",
                "Bancos de alimentos aproximam doadores e entidades que atendem pessoas em situação de insegurança alimentar. O aproveitamento das doações depende também de triagem, refrigeração e entrega no prazo adequado.",
            ),
        },
        {
            "titulo": "Caminhos para promover a inclusão digital das pessoas idosas no Brasil",
            "apoio": (
                "Marcar uma consulta ou solicitar um documento pelo celular pode evitar deslocamentos. Para quem divide um aparelho ou tem pouca familiaridade com aplicativos, o mesmo processo pode criar uma nova barreira.",
                "Uma biblioteca oferece encontros em que os participantes praticam tarefas escolhidas por eles, como enviar arquivos ou verificar mensagens suspeitas. As atividades permitem repetir cada etapa sem pressa.",
                "Letras pequenas, instruções pouco claras e autenticação complexa afetam a experiência de uso. Projetar serviços digitais com a participação de pessoas idosas ajuda a identificar dificuldades antes do lançamento.",
            ),
        },
    ),
    "ITA": (
        {
            "titulo": "A cidade entre a previsão de riscos e a capacidade de agir",
            "apoio": (
                "Uma equipe acompanha chuvas com sensores instalados ao longo de um rio. O alerta chega antes da inundação, mas algumas famílias não têm acesso à mensagem e outras desconhecem a rota mais segura.",
                "Moradores de um bairro indicam pontos que costumam alagar mesmo quando a chuva é breve. Ao incorporar essas observações aos mapas, técnicos descobrem que trechos pouco visíveis nos dados merecem vistoria.",
                "Uma prefeitura precisa decidir entre ampliar a rede de monitoramento e melhorar obras de drenagem e rotas de fuga. Cada investimento atua em um ponto diferente, da antecipação do perigo à redução de seus efeitos.",
            ),
        },
        {
            "titulo": "O papel do erro na formação científica contemporânea",
            "apoio": (
                "Dois grupos testam a mesma hipótese e chegam a resultados diferentes. Ao revisar o caderno de laboratório, percebem que adotaram critérios de medição distintos. A divergência ajuda a explicitar uma escolha que havia passado despercebida.",
                "Em uma competição escolar, apresentar apenas experiências bem-sucedidas pode facilitar a avaliação. Também pode esconder os testes que levaram o grupo a revisar a pergunta inicial.",
                "Um pesquisador publica o procedimento e as limitações de seu estudo. Outras equipes conseguem refazê-lo em condições diferentes e apontar onde seus resultados se sustentam e onde precisam ser revistos.",
            ),
        },
    ),
}


def obter_tema_surpresa(instituicao, rodada):
    temas = TEMAS_SURPRESA[instituicao]
    tema = temas[rodada % len(temas)]
    orientacao = (
        "Apresente uma proposta de intervenção que respeite os direitos humanos."
        if instituicao == "ENEM"
        else "Dê um título ao texto e desenvolva uma tese própria em diálogo com a coletânea e a atualidade."
    )
    return {
        **tema,
        "edicao": "Redação surpresa · tema autoral",
        "enunciado": (
            "Com base nos textos motivadores e em seus conhecimentos, redija um texto "
            f"dissertativo-argumentativo em português formal sobre “{tema['titulo']}”. {orientacao}"
        ),
    }
