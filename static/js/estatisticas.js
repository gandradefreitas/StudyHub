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


            elemento.innerHTML = `

                <div class="cabecalho-area">

                    <span class="nome-area">
                        ${area}
                    </span>

                    <strong>
                        ${dadosArea.porcentagem}%
                    </strong>

                </div>


                <div class="barra-desempenho">

                    <div
                        class="progresso-desempenho"
                        style="width: ${dadosArea.porcentagem}%"
                    ></div>

                </div>


                <span class="detalhes-area">

                    ${dadosArea.acertos}
                    acertos de
                    ${dadosArea.questoes}
                    questões

                </span>

            `;


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

    const container =
        document.querySelector(
            "#estatisticas-historico-provas"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (provas.length === 0) {

        container.innerHTML = `

            <div class="historico-vazio">

                <i class="bi bi-clipboard"></i>

                <p>
                    Nenhuma prova realizada ainda.
                </p>

            </div>

        `;

        return;
    }


    provas.forEach(
        prova => {

            const elemento =
                document.createElement(
                    "div"
                );


            elemento.className =
                "prova-estatistica";


            const porcentagem =
                Number(
                    prova.porcentagem
                );


            const classeResultado =
                porcentagem >= 70
                    ? "resultado-bom"
                    : porcentagem >= 50
                        ? "resultado-medio"
                        : "resultado-baixo";


            elemento.innerHTML = `

                <div class="prova-estatistica-info">

                    <strong>

                        ${prova.nome}
                        — ${prova.dia}

                    </strong>


                    <span>

                        ${formatarDataProva(
                            prova.data
                        )}

                    </span>

                </div>


                <div
                    class="
                        prova-estatistica-resultado
                        ${classeResultado}
                    "
                >

                    <strong>

                        ${porcentagem.toLocaleString(
                            "pt-BR"
                        )}%

                    </strong>


                    <span>

                        ${prova.acertos}/${prova.total}
                        acertos

                    </span>

                </div>

            `;


            container.appendChild(
                elemento
            );

        }
    );

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


    container.innerHTML = `

        <div class="card-analise">

            <div class="icone-analise">

                <i class="bi bi-arrow-up-circle"></i>

            </div>


            <div>

                <h3>
                    Ponto forte
                </h3>


                <p>

                    ${melhor[0]}
                    apresenta seu melhor
                    aproveitamento, com
                    ${melhor[1].porcentagem}%
                    de acertos.

                </p>

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


                <p>

                    ${pior[0]}
                    apresenta seu menor
                    aproveitamento, com
                    ${pior[1].porcentagem}%
                    de acertos.

                </p>

            </div>

        </div>

    `;

}