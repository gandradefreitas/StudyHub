let graficoEstudos = null;
let dataGraficoEstudos = new Date();

/* =========================================================
   INICIALIZAÇÃO
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    carregarResumo();

    carregarEvolucao();

    carregarProvas();

    carregarDesempenhoAreas();

    carregarDesempenhoQuestoesAreas();

    carregarAnaliseDetalhadaQuestoes();


    const seletorAnalise = document.getElementById(
        "criterio-analise-questoes"
    );

    if (seletorAnalise) {

        seletorAnalise.addEventListener(
            "change",
            carregarAnaliseDetalhadaQuestoes
        );

    }


    const botaoAnterior =
        document.querySelector(
            "#botao-mes-anterior"
        );


    const botaoProximo =
        document.querySelector(
            "#botao-mes-proximo"
        );


    if (botaoAnterior) {

        botaoAnterior.addEventListener(
            "click",
            () => {

                dataGraficoEstudos.setMonth(
                    dataGraficoEstudos.getMonth() - 1
                );


                carregarEvolucao();

            }
        );

    }


    if (botaoProximo) {

        botaoProximo.addEventListener(
            "click",
            () => {

                const hoje =
                    new Date();


                const proximoMes =
                    new Date(
                        dataGraficoEstudos
                    );


                proximoMes.setMonth(
                    proximoMes.getMonth() + 1
                );


                /*
                 * Não permite avançar para
                 * um mês futuro.
                 */

                if (
                    proximoMes.getFullYear() >
                        hoje.getFullYear()
                    ||
                    (
                        proximoMes.getFullYear() ===
                            hoje.getFullYear()
                        &&
                        proximoMes.getMonth() >
                            hoje.getMonth()
                    )
                ) {

                    return;

                }


                dataGraficoEstudos =
                    proximoMes;


                carregarEvolucao();

            }
        );

    }

});

// =============================================
// ANÁLISE DETALHADA DAS QUESTÕES
// =============================================

async function carregarAnaliseDetalhadaQuestoes() {

    const seletor = document.getElementById(
        "criterio-analise-questoes"
    );

    const container = document.getElementById(
        "estatisticas-analise-detalhada"
    );

    if (!seletor || !container) {
        return;
    }

    const criterio = seletor.value;

    container.innerHTML = `
        <p class="estado-vazio">
            Carregando análise...
        </p>
    `;

    try {

        const resposta = await fetch(
            `/estatisticas/questoes-detalhadas?criterio=${encodeURIComponent(criterio)}`
        );

        if (!resposta.ok) {
            throw new Error(
                "Não foi possível carregar a análise detalhada."
            );
        }

        const dados = await resposta.json();

        renderizarAnaliseDetalhadaQuestoes(dados);

    } catch (erro) {

        console.error(
            "Erro ao carregar análise detalhada:",
            erro
        );

        container.innerHTML = `
            <p class="estado-vazio">
                Não foi possível carregar esta análise.
                Tente novamente mais tarde.
            </p>
        `;
    }
}


// =============================================
// RENDERIZAR CARTÕES DA ANÁLISE
// =============================================

function renderizarAnaliseDetalhadaQuestoes(dados) {

    const container = document.getElementById(
        "estatisticas-analise-detalhada"
    );

    if (!container) {
        return;
    }

    container.replaceChildren();

    const categorias = Object.entries(dados);

    if (categorias.length === 0) {

        const mensagem = document.createElement("p");

        mensagem.className = "estado-vazio";

        mensagem.textContent =
            "Ainda não existem respostas registradas para esta análise.";

        container.appendChild(mensagem);

        return;
    }

    // Ordenar do maior para o menor aproveitamento.
    categorias.sort(
        (a, b) => b[1].porcentagem - a[1].porcentagem
    );

    categorias.forEach(([categoria, dadosCategoria]) => {

        const cartao = document.createElement("article");

        cartao.className = "cartao-analise-detalhada";

        const titulo = document.createElement("h3");

        titulo.textContent = categoria;

        const total = document.createElement("p");

        total.className = "resumo-analise-detalhada";

        total.textContent =
            `${dadosCategoria.questoes} respostas registradas`;

        const resultados = document.createElement("div");

        resultados.className = "resultados-analise-detalhada";

        const acertos = document.createElement("span");

        acertos.textContent =
            `${dadosCategoria.acertos} acertos`;

        const erros = document.createElement("span");

        erros.textContent =
            `${dadosCategoria.erros} erros`;

        resultados.append(acertos, erros);

        const porcentagem = document.createElement("p");

        porcentagem.className =
            "porcentagem-analise-detalhada";

        porcentagem.textContent =
            `${Number(dadosCategoria.porcentagem).toLocaleString(
                "pt-BR",
                {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1
                }
            )}% de acerto`;

        const barra = document.createElement("div");

        barra.className = "barra-analise-detalhada";

        const progresso = document.createElement("div");

        progresso.className = "progresso-analise-detalhada";

        const percentual = Math.min(
            100,
            Math.max(0, Number(dadosCategoria.porcentagem) || 0)
        );

        progresso.style.width = `${percentual}%`;

        barra.appendChild(progresso);

        cartao.append(
            titulo,
            total,
            resultados,
            porcentagem,
            barra
        );

        container.appendChild(cartao);
    });
}


/* =========================================================
   CARREGAMENTO DOS DADOS
========================================================= */

async function carregarResumo() {

    try {

        const resposta = await fetch(
            "/estatisticas/resumo"
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar as estatísticas."
            );

        }


        const dados = await resposta.json();


        renderizarResumo({

            horasEstudadas:
                dados.horas_estudadas,

            questoesResolvidas:
                dados.questoes,

            taxaAcerto:
                dados.porcentagem,

            provasRealizadas:
                dados.provas

        });


        renderizarQuestoes({

            resolvidas:
                Number(dados.acertos) +
                Number(dados.erros),

            acertos:
                Number(dados.acertos),

            erros:
                Number(dados.erros),

            naoRespondidas:
                Number(dados.nao_respondidas),

            aproveitamento:
                Number(dados.porcentagem)

        });


    } catch (erro) {

        console.error(
            "Erro ao carregar estatísticas:",
            erro
        );

    }

}


async function carregarDesempenhoQuestoesAreas() {

    const container = document.getElementById(
        "estatisticas-desempenho-questoes-areas"
    );

    if (!container) {
        return;
    }

    try {

        const resposta = await fetch(
            "/estatisticas/questoes-areas"
        );

        if (!resposta.ok) {
            throw new Error(
                "Não foi possível carregar o desempenho."
            );
        }

        const dados = await resposta.json();

        renderizarDesempenhoQuestoesAreas(dados);

    } catch (erro) {

        console.error(
            "Erro ao carregar desempenho das questões:",
            erro
        );

        container.innerHTML = `
            <p class="estado-vazio">
                Não foi possível carregar o desempenho das questões.
                Tente novamente mais tarde.
            </p>
        `;
    }
}


function renderizarDesempenhoQuestoesAreas(dados) {

    const container = document.getElementById(
        "estatisticas-desempenho-questoes-areas"
    );

    if (!container) {
        return;
    }

    container.replaceChildren();

    const areas = Object.entries(dados);

    if (areas.length === 0) {

        const mensagem = document.createElement("p");

        mensagem.className = "estado-vazio";

        mensagem.textContent =
            "Você ainda não respondeu a questões de estudo.";

        container.appendChild(mensagem);

        return;
    }

    areas.sort((a, b) =>
        b[1].porcentagem - a[1].porcentagem
    );

    areas.forEach(([area, dadosArea]) => {

        const cartao = document.createElement("article");

        cartao.className = "cartao-desempenho-questoes";

        const titulo = document.createElement("h3");

        titulo.textContent = area;

        const resumo = document.createElement("p");

        resumo.className = "resumo-desempenho-questoes";

        resumo.textContent =
            `${dadosArea.questoes} respostas · ` +
            `${dadosArea.acertos} acertos · ` +
            `${dadosArea.erros} erros`;

        const porcentagem = document.createElement("p");

        porcentagem.className = "porcentagem-desempenho-questoes";

        porcentagem.textContent =
            `${dadosArea.porcentagem.toFixed(1)}% de acerto`;

        const barra = document.createElement("div");

        barra.className = "barra-desempenho-questoes";

        const progresso = document.createElement("div");

        progresso.className = "progresso-desempenho-questoes";

        progresso.style.width =
            `${Math.min(100, Math.max(0, dadosArea.porcentagem))}%`;

        barra.appendChild(progresso);

        cartao.append(
            titulo,
            resumo,
            porcentagem,
            barra
        );

        container.appendChild(cartao);
    });
}



async function carregarEvolucao() {

    const ano =
        dataGraficoEstudos.getFullYear();

    const mes =
        dataGraficoEstudos.getMonth() + 1;


    try {

        const resposta = await fetch(
            `/estatisticas/evolucao?ano=${ano}&mes=${mes}`
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar a evolução dos estudos."
            );

        }


        const dados =
            await resposta.json();


        atualizarTituloMes(
            ano,
            mes
        );


        renderizarGraficoEstudos(
            dados
        );


    } catch (erro) {

        console.error(
            "Erro ao carregar evolução:",
            erro
        );

    }

}

function atualizarTituloMes(ano, mes) {

    const elemento =
        document.querySelector(
            "#mes-atual-grafico"
        );


    if (!elemento) {
        return;
    }


    const data =
        new Date(
            ano,
            mes - 1,
            1
        );


    elemento.textContent =
        data.toLocaleDateString(
            "pt-BR",
            {
                month: "long",
                year: "numeric"
            }
        );
}


async function carregarDesempenhoAreas() {

    try {

        const resposta = await fetch(
            "/estatisticas/areas"
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar o desempenho por área."
            );

        }


        const dados = await resposta.json();


        renderizarDesempenhoAreas(
            dados
        );


        renderizarAnalise(
            dados
        );


    } catch (erro) {

        console.error(
            "Erro ao carregar desempenho por área:",
            erro
        );

    }

}


async function carregarProvas() {

    try {

        const resposta = await fetch(
            "/estatisticas/provas"
        );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar o histórico de provas."
            );

        }


        const dados = await resposta.json();


        renderizarProvas(
            dados
        );


    } catch (erro) {

        console.error(
            "Erro ao carregar provas:",
            erro
        );

    }

}


/* =========================================================
   FORMATAÇÃO
========================================================= */

function formatarDuracao(segundos) {

    segundos =
        Number(segundos) || 0;


    const horas =
        Math.floor(
            segundos / 3600
        );


    const minutos =
        Math.floor(
            (segundos % 3600) / 60
        );


    return `${horas}h ${String(minutos).padStart(2, "0")}min`;

}


function formatarDataGrafico(data) {

    if (!data) {
        return "";
    }


    const partes =
        data.split("-");


    return `${partes[2]}/${partes[1]}`;

}


function formatarDataProva(data) {

    if (!data) {
        return "";
    }


    const dataObj =
        new Date(data);


    return dataObj.toLocaleDateString(
        "pt-BR"
    );

}


function converterSegundosParaMinutos(segundos) {

    return Math.round(
        Number(segundos) / 60
    );

}


/* =========================================================
   RESUMO
========================================================= */

function renderizarResumo(resumo) {

    const horas =
        document.querySelector(
            "#estatisticas-horas-estudadas"
        );


    const questoes =
        document.querySelector(
            "#estatisticas-questoes-resolvidas"
        );


    const taxa =
        document.querySelector(
            "#estatisticas-taxa-acerto"
        );


    const provas =
        document.querySelector(
            "#estatisticas-provas-realizadas"
        );


    if (horas) {

        horas.textContent =
            formatarDuracao(
                resumo.horasEstudadas
            );

    }


    if (questoes) {

        questoes.textContent =
            Number(
                resumo.questoesResolvidas
            ).toLocaleString("pt-BR");

    }


    if (taxa) {

        taxa.textContent =
            `${Number(
                resumo.taxaAcerto
            ).toLocaleString("pt-BR")}%`;

    }


    if (provas) {

        provas.textContent =
            Number(
                resumo.provasRealizadas
            ).toLocaleString("pt-BR");

    }

}


/* =========================================================
   GRÁFICO
========================================================= */

function renderizarGraficoEstudos(dados) {

    const canvas =
        document.querySelector(
            "#grafico-estatisticas-estudos"
        );


    if (!canvas) {
        return;
    }


    const labels =
        dados.map(
            item =>
                formatarDataGrafico(
                    item.data
                )
        );


    const valores =
        dados.map(
            item =>
                converterSegundosParaMinutos(
                    item.duracao
                )
        );


    if (graficoEstudos) {

        graficoEstudos.destroy();

    }


    graficoEstudos =
        new Chart(
            canvas,
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Tempo estudado",

                            data:
                                valores,

                            tension:
                                0.3,

                            fill:
                                true,

                            pointRadius:
                                3

                        }

                    ]

                },


                options: {

                    responsive:
                        true,

                    maintainAspectRatio:
                        false,


                    plugins: {

                        legend: {

                            display:
                                false

                        }

                    },


                    scales: {

                        y: {

                            beginAtZero:
                                true,

                            title: {

                                display:
                                    true,

                                text:
                                    "Minutos"

                            }

                        },


                        x: {

                            grid: {

                                display:
                                    false

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   QUESTÕES
========================================================= */

function renderizarQuestoes(questoes) {

    const total =
        document.querySelector(
            "#estatisticas-total-questoes"
        );


    const acertos =
        document.querySelector(
            "#estatisticas-total-acertos"
        );


    const erros =
        document.querySelector(
            "#estatisticas-total-erros"
        );


    const aproveitamento =
        document.querySelector(
            "#estatisticas-aproveitamento"
        );


    if (total) {

        total.textContent =
            Number(
                questoes.resolvidas
            ).toLocaleString("pt-BR");

    }


    if (acertos) {

        acertos.textContent =
            Number(
                questoes.acertos
            ).toLocaleString("pt-BR");

    }


    if (erros) {

        erros.textContent =
            Number(
                questoes.erros
            ).toLocaleString("pt-BR");

    }


    if (aproveitamento) {

        aproveitamento.textContent =
            `${Number(
                questoes.aproveitamento
            ).toLocaleString("pt-BR")}%`;

    }


    renderizarDistribuicaoQuestoes(
        questoes
    );

}


/* =========================================================
   DISTRIBUIÇÃO DAS QUESTÕES
========================================================= */

function renderizarDistribuicaoQuestoes(questoes) {

    const total =
        Number(questoes.acertos) +
        Number(questoes.erros) +
        Number(questoes.naoRespondidas);


    if (total === 0) {
        return;
    }


    const porcentagemAcertos =
        (
            Number(questoes.acertos) /
            total
        ) * 100;


    const porcentagemErros =
        (
            Number(questoes.erros) /
            total
        ) * 100;


    const porcentagemNaoRespondidas =
        (
            Number(questoes.naoRespondidas) /
            total
        ) * 100;


    const barraAcertos =
        document.querySelector(
            "#estatisticas-barra-acertos"
        );


    const barraErros =
        document.querySelector(
            "#estatisticas-barra-erros"
        );


    const barraNaoRespondidas =
        document.querySelector(
            "#estatisticas-barra-nao-respondidas"
        );


    if (barraAcertos) {

        barraAcertos.style.width =
            `${porcentagemAcertos}%`;

    }


    if (barraErros) {

        barraErros.style.width =
            `${porcentagemErros}%`;

    }


    if (barraNaoRespondidas) {

        barraNaoRespondidas.style.width =
            `${porcentagemNaoRespondidas}%`;

    }

}


/* =========================================================
   DESEMPENHO POR ÁREA
========================================================= */

function renderizarDesempenhoAreas(dados) {

    const container =
        document.querySelector(
            "#estatisticas-desempenho-areas"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    const areas =
        Object.entries(dados);


    if (areas.length === 0) {

        container.innerHTML = `

            <p class="estado-vazio">

                Ainda não há questões suficientes
                para calcular seu desempenho.

            </p>

        `;

        return;
    }


    areas.forEach(
        ([area, dadosArea]) => {

            const elemento =
                document.createElement(
                    "div"
                );


            elemento.className =
                "item-desempenho-area";


            const porcentagem =
                Number(
                    dadosArea.porcentagem
                );


            const acertos =
                Number(
                    dadosArea.acertos
                );


            const questoes =
                Number(
                    dadosArea.questoes
                );


            elemento.innerHTML = `

                <div class="cabecalho-area">

                    <span class="nome-area"></span>

                    <strong class="porcentagem-area"></strong>

                </div>


                <div class="barra-desempenho">

                    <div
                        class="progresso-desempenho"
                    ></div>

                </div>


                <span class="detalhes-area"></span>

            `;


            const nomeArea =
                elemento.querySelector(
                    ".nome-area"
                );


            const porcentagemElemento =
                elemento.querySelector(
                    ".porcentagem-area"
                );


            const progresso =
                elemento.querySelector(
                    ".progresso-desempenho"
                );


            const detalhes =
                elemento.querySelector(
                    ".detalhes-area"
                );


            nomeArea.textContent =
                area;


            porcentagemElemento.textContent =
                `${porcentagem}%`;


            progresso.style.width =
                `${porcentagem}%`;


            detalhes.textContent =
                `${acertos} acertos de ${questoes} questões`;


            container.appendChild(
                elemento
            );

        }
    );

}



/* =========================================================
   PROVAS
========================================================= */

function renderizarProvas(provas) {

    const container = document.querySelector(
        "#estatisticas-historico-provas"
    );

    if (!container) {
        return;
    }

    container.replaceChildren();

    if (!provas || provas.length === 0) {

        const mensagem = document.createElement("div");

        mensagem.className = "historico-vazio";

        mensagem.innerHTML = `
            <i class="bi bi-clipboard"></i>
            <p>Nenhuma prova realizada ainda.</p>
        `;

        container.appendChild(mensagem);

        return;
    }

    const limiteVisivel = 3;

    const provasOcultas = provas.length > limiteVisivel;

    // Contêiner exclusivo dos cartões.
    const lista = document.createElement("div");

    lista.className = "lista-provas-estatisticas";

    // Criar os cartões de todas as provas.
    provas.forEach((prova, indice) => {

        const elemento = document.createElement("div");

        elemento.className = "prova-estatistica";

        const porcentagem = Number(prova.porcentagem) || 0;
        const acertos = Number(prova.acertos) || 0;
        const total = Number(prova.total) || 0;

        const classeResultado =
            porcentagem >= 70
                ? "resultado-bom"
                : porcentagem >= 50
                    ? "resultado-medio"
                    : "resultado-baixo";


        // Ocultar inicialmente as provas a partir da quarta.
        if (indice >= limiteVisivel) {
            elemento.classList.add("prova-estatistica-oculta");
            elemento.hidden = true;
        }



        const informacoes = document.createElement("div");

        informacoes.className = "prova-estatistica-info";

        const nome = document.createElement("strong");

        nome.className = "nome-prova";

        nome.textContent = `${prova.nome} — ${prova.dia}`;

        const data = document.createElement("span");

        data.className = "data-prova";

        data.textContent = prova.data || "";

        informacoes.append(nome, data);

        const resultado = document.createElement("div");

        resultado.className =
            `prova-estatistica-resultado ${classeResultado}`;

        const percentual = document.createElement("strong");

        percentual.className = "porcentagem-prova";

        percentual.textContent =
            `${porcentagem.toLocaleString("pt-BR")}%`;

        const resumo = document.createElement("span");

        resumo.className = "resultado-prova";

        resumo.textContent = `${acertos}/${total} acertos`;

        resultado.append(percentual, resumo);

        elemento.append(informacoes, resultado);

        lista.appendChild(elemento);

    });

    container.appendChild(lista);

    // Não criar botão quando todas as provas já estão visíveis.
    if (!provasOcultas) {
        return;
    }

    // Botão para expandir ou recolher o histórico.
    const botao = document.createElement("button");

    botao.type = "button";

    botao.className = "botao-historico-provas";

    botao.setAttribute("aria-expanded", "false");

    botao.setAttribute(
        "aria-label",
        "Mostrar provas anteriores"
    );

    const icone = document.createElement("i");

    icone.className = "bi bi-three-dots";

    icone.setAttribute("aria-hidden", "true");

    const texto = document.createElement("span");

    texto.textContent = "Mostrar provas anteriores";

    botao.append(icone, texto);

    botao.addEventListener("click", () => {

        const expandido =
            botao.getAttribute("aria-expanded") === "true";

        const novoEstado = !expandido;

        // Mostrar ou ocultar as provas a partir da quarta.
        lista.querySelectorAll(
            ".prova-estatistica-oculta"
        ).forEach(prova => {

            prova.hidden = !novoEstado;

        });

        botao.setAttribute(
            "aria-expanded",
            String(novoEstado)
        );

        botao.setAttribute(
            "aria-label",
            novoEstado
                ? "Ocultar provas anteriores"
                : "Mostrar provas anteriores"
        );

        icone.className = novoEstado
            ? "bi bi-chevron-up"
            : "bi bi-three-dots";

        texto.textContent = novoEstado
            ? "Ocultar provas anteriores"
            : "Mostrar provas anteriores";

    });

    container.appendChild(botao);

}


/* =========================================================
   ANÁLISE
========================================================= */

function renderizarAnalise(dados) {

    const container =
        document.querySelector(
            "#estatisticas-analise-desempenho"
        );


    if (!container) {
        return;
    }


    const areas =
        Object.entries(dados);


    if (areas.length === 0) {

        container.innerHTML = `

            <div class="analise-vazia">

                <i class="bi bi-bar-chart"></i>

                <p>

                    Ainda não há dados suficientes
                    para analisar seu desempenho.

                </p>

            </div>

        `;

        return;
    }


    const areasOrdenadas =
        [...areas].sort(
            (a, b) =>
                Number(b[1].porcentagem) -
                Number(a[1].porcentagem)
        );


    const melhor =
        areasOrdenadas[0];


    const pior =
        areasOrdenadas[
            areasOrdenadas.length - 1
        ];


    const porcentagemMelhor =
        Number(
            melhor[1].porcentagem
        );


    const porcentagemPior =
        Number(
            pior[1].porcentagem
        );


    container.innerHTML = `

        <div class="card-analise">

            <div class="icone-analise">

                <i class="bi bi-arrow-up-circle"></i>

            </div>


            <div>

                <h3>
                    Ponto forte
                </h3>


                <p class="texto-melhor-area"></p>

            </div>

        </div>


        <div class="card-analise">

            <div class="icone-analise">

                <i class="bi bi-exclamation-circle"></i>

            </div>


            <div>

                <h3>
                    Área de atenção
                </h3>


                <p class="texto-pior-area"></p>

            </div>

        </div>

    `;


    const textoMelhor =
        container.querySelector(
            ".texto-melhor-area"
        );


    const textoPior =
        container.querySelector(
            ".texto-pior-area"
        );


    textoMelhor.textContent =
        `${melhor[0]} apresenta seu melhor ` +
        `aproveitamento, com ` +
        `${porcentagemMelhor}% de acertos.`;


    textoPior.textContent =
        `${pior[0]} apresenta seu menor ` +
        `aproveitamento, com ` +
        `${porcentagemPior}% de acertos.`;

}

