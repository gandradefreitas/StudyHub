const csrfToken =
    document.querySelector(
        'meta[name="csrf-token"]'
    ).getAttribute("content");

/* =========================================================
   ELEMENTOS DO CALENDÁRIO
========================================================= */

const elementoMesAtual =
    document.getElementById("calendario-mes-atual");

const elementoDiasCalendario =
    document.getElementById("calendario-dias");

const botaoMesAnterior =
    document.getElementById("calendario-mes-anterior");

const botaoMesProximo =
    document.getElementById("calendario-mes-proximo");

const painelDetalhesDia =
    document.querySelector(".calendario-detalhes-dia");


/* =========================================================
   ESTADO
========================================================= */

const dataInicial = new Date();

let mesAtual =
    dataInicial.getMonth();

let anoAtual =
    dataInicial.getFullYear();

let diaSelecionado = null;

let mesSelecionado = null;

let anoSelecionado = null;

let identificadorSelecao = 0;

let indicadoresMes = {};


let dadosDia = {

    estudos: [],

    tarefas: [],

    provas: [],

    anotacao: null

};


/* =========================================================
   MESES
========================================================= */

const nomesMeses = [

    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"

];


/* =========================================================
   RENDERIZA ATIVIDADES DO DIA
========================================================= */

function renderizarAtividades() {

    const atividades =
        document.querySelector(
            ".calendario-detalhes-dia .atividades-dia"
        );


    if (!atividades) {

        return;

    }


    let html = "";


    /* =====================================================
       ESTUDOS
    ===================================================== */

    if (dadosDia.estudos.length > 0) {

        html += `

            <div class="atividade-secao">

                <div class="titulo-atividade">

                    <i class="bi bi-clock-history"></i>

                    <span>
                        Estudos
                    </span>

                </div>


                <div class="lista-atividade">

        `;


        dadosDia.estudos.forEach((estudo) => {

            html += `

                <div class="item-atividade">

                    <span>

                        <i class="bi bi-clock"></i>

                        ${formatarDuracao(
                            estudo.duracao
                        )}

                    </span>

                </div>

            `;

        });


        html += `

                </div>

            </div>

        `;

    }


    /* =====================================================
       TAREFAS
    ===================================================== */

    if (dadosDia.tarefas.length > 0) {

        html += `

            <div class="atividade-secao">

                <div class="titulo-atividade">

                    <i class="bi bi-check2-square"></i>

                    <span>
                        Tarefas concluídas
                    </span>

                </div>


                <div class="lista-atividade">

        `;


        dadosDia.tarefas.forEach((tarefa) => {

            html += `

                <div class="item-atividade">

                    <span>

                        <i class="bi bi-check-circle-fill"></i>

                        ${tarefa.descricao}

                    </span>

                </div>

            `;

        });


        html += `

                </div>

            </div>

        `;

    }


    /* =====================================================
       PROVAS
    ===================================================== */

    if (dadosDia.provas.length > 0) {

        html += `

            <div class="atividade-secao">

                <div class="titulo-atividade">

                    <i class="bi bi-file-earmark-text"></i>

                    <span>
                        Provas realizadas
                    </span>

                </div>


                <div class="lista-atividade">

        `;


        dadosDia.provas.forEach((prova) => {

            html += `

                <div class="prova-calendario">

                    <div class="prova-calendario-info">

                        <strong>

                            ${prova.nome}
                            — ${prova.dia}

                        </strong>


                        <span>

                            ${prova.acertos}/${prova.total}
                            acertos

                        </span>

                    </div>


                    <div class="prova-calendario-porcentagem">

                        ${Number(
                            prova.porcentagem
                        ).toFixed(1)}%

                    </div>

                </div>

            `;

        });


        html += `

                </div>

            </div>

        `;

    }


    /* =====================================================
       ANOTAÇÃO
    ===================================================== */

    html += `

        <div class="atividade-secao">

            <div class="titulo-atividade">

                <i class="bi bi-journal-text"></i>

                <span>
                    Anotação do dia
                </span>

            </div>


            <textarea
                class="campo-anotacao"
                placeholder="Escreva algo sobre seu dia..."
            >${dadosDia.anotacao || ""}</textarea>


            <button
                type="button"
                class="botao-salvar-anotacao"
                id="botao-salvar-anotacao"
            >

                <i class="bi bi-check2"></i>

                Salvar anotação

            </button>


            <div
                class="mensagem-anotacao"
                id="mensagem-anotacao"
            ></div>

        </div>

    `;


    atividades.innerHTML = html;


    /*
        O botão é criado dinamicamente,
        então precisamos adicionar o evento
        depois que ele existir no DOM.
    */

    const botaoSalvar =
        document.getElementById(
            "botao-salvar-anotacao"
        );


    if (botaoSalvar) {

        botaoSalvar.addEventListener(
            "click",
            salvarAnotacao
        );

    }

}


/* =========================================================
   CARREGAR INDICADORES DO MÊS
========================================================= */

async function carregarIndicadoresMes() {

    try {

        const resposta =
            await fetch(
                `/calendario/indicadores?mes=${mesAtual + 1}&ano=${anoAtual}`
            );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar os indicadores."
            );

        }


        indicadoresMes =
            await resposta.json();


    } catch (erro) {

        console.error(
            "Erro ao carregar indicadores:",
            erro
        );

        indicadoresMes = {};

    }

}


/* =========================================================
   RENDERIZAR CALENDÁRIO
========================================================= */

function renderizarCalendario() {

    if (
        !elementoDiasCalendario ||
        !elementoMesAtual
    ) {

        return;

    }


    elementoDiasCalendario.innerHTML = "";


    elementoMesAtual.textContent =
        `${nomesMeses[mesAtual]} ${anoAtual}`;


    const primeiroDia =
        new Date(
            anoAtual,
            mesAtual,
            1
        );


    const ultimoDia =
        new Date(
            anoAtual,
            mesAtual + 1,
            0
        );


    let diaSemana =
        primeiroDia.getDay();


    /*
        JavaScript:

        Domingo = 0
        Segunda = 1
        ...
        Sábado = 6

        Nosso calendário começa na segunda.
    */

    if (diaSemana === 0) {

        diaSemana = 6;

    } else {

        diaSemana -= 1;

    }


    const quantidadeDias =
        ultimoDia.getDate();


    /* =====================================================
       DIAS VAZIOS DO MÊS ANTERIOR
    ===================================================== */

    for (
        let i = 0;
        i < diaSemana;
        i++
    ) {

        const diaVazio =
            document.createElement("div");


        diaVazio.classList.add(
            "dia",
            "dia-outro-mes"
        );


        elementoDiasCalendario.appendChild(
            diaVazio
        );

    }


    /* =====================================================
       DIAS DO MÊS
    ===================================================== */

    for (
        let dia = 1;
        dia <= quantidadeDias;
        dia++
    ) {

        const dataISO =
            `${anoAtual}-${String(
                mesAtual + 1
            ).padStart(2, "0")}-${String(
                dia
            ).padStart(2, "0")}`;


        const indicadores =
            indicadoresMes[dataISO] || {};


        const elementoDia =
            document.createElement("button");


        elementoDia.type = "button";


        elementoDia.classList.add(
            "dia"
        );


        elementoDia.innerHTML = `

            <span class="numero-dia">
                ${dia}
            </span>

            <span class="indicadores-dia"></span>

        `;


        /* =================================================
           DIA ATUAL
        ================================================= */

        const hoje =
            new Date();


        if (

            dia === hoje.getDate() &&

            mesAtual === hoje.getMonth() &&

            anoAtual === hoje.getFullYear()

        ) {

            elementoDia.classList.add(
                "dia-hoje"
            );

        }


        /* =================================================
           DIA SELECIONADO
        ================================================= */

        if (

            dia === diaSelecionado &&

            mesAtual === mesSelecionado &&

            anoAtual === anoSelecionado

        ) {

            elementoDia.classList.add(
                "dia-selecionado"
            );

        }


        /* =================================================
           INDICADORES
        ================================================= */

        const containerIndicadores =
            elementoDia.querySelector(
                ".indicadores-dia"
            );


        if (indicadores.estudo) {

            adicionarIndicador(
                containerIndicadores,
                "indicador-estudo"
            );

        }


        if (indicadores.tarefa) {

            adicionarIndicador(
                containerIndicadores,
                "indicador-tarefa"
            );

        }


        if (indicadores.prova) {

            adicionarIndicador(
                containerIndicadores,
                "indicador-prova"
            );

        }


        if (indicadores.anotacao) {

            adicionarIndicador(
                containerIndicadores,
                "indicador-anotacao"
            );

        }


        /* =================================================
           SELEÇÃO
        ================================================= */

        elementoDia.addEventListener(
            "click",
            () => {

                selecionarDia(
                    dia,
                    elementoDia
                );

            }
        );


        elementoDiasCalendario.appendChild(
            elementoDia
        );

    }

}


/* =========================================================
   ADICIONAR INDICADOR
========================================================= */

function adicionarIndicador(
    container,
    classe
) {

    if (!container) {

        return;

    }


    const indicador =
        document.createElement("span");


    indicador.classList.add(
        "indicador",
        classe
    );


    container.appendChild(
        indicador
    );

}


/* =========================================================
   SELECIONAR DIA
========================================================= */

async function selecionarDia(
    dia,
    elementoDia
) {

    diaSelecionado = dia;

    mesSelecionado = mesAtual;

    anoSelecionado = anoAtual;


    const minhaSelecao =
        ++identificadorSelecao;


    document
        .querySelectorAll(
            ".calendario-detalhes-dia .dia-selecionado"
        )
        .forEach((elemento) => {

            elemento.classList.remove(
                "dia-selecionado"
            );

        });


    elementoDia.classList.add(
        "dia-selecionado"
    );


    const dataSelecionada =
        new Date(
            anoAtual,
            mesAtual,
            dia
        );


    const dataISO =
        `${anoAtual}-${String(
            mesAtual + 1
        ).padStart(2, "0")}-${String(
            dia
        ).padStart(2, "0")}`;


    const nomeDia =
        dataSelecionada.toLocaleDateString(
            "pt-BR",
            {
                weekday: "long"
            }
        );


    const dataFormatada =
        dataSelecionada.toLocaleDateString(
            "pt-BR",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );


    if (!painelDetalhesDia) {

        return;

    }


    painelDetalhesDia.innerHTML = `

        <div class="detalhes-dia-conteudo">

            <span class="subtitulo-calendario">
                ${nomeDia}
            </span>


            <h2>
                ${dataFormatada}
            </h2>


            <div class="atividades-dia">

                <p>
                    Carregando atividades...
                </p>

            </div>

        </div>

    `;


    /* =====================================================
       LIMPAR DADOS ANTERIORES
    ===================================================== */

    dadosDia = {

        estudos: [],

        tarefas: [],

        provas: [],

        anotacao: null

    };


    /* =====================================================
       CARREGAR DADOS
    ===================================================== */

    await Promise.all([

        carregarEstudos(dataISO),

        carregarTarefas(dataISO),

        carregarProvas(dataISO),

        carregarAnotacao(dataISO)

    ]);


    /*
        Impede uma requisição antiga de
        sobrescrever uma seleção nova.
    */

    if (
        minhaSelecao !== identificadorSelecao
    ) {

        return;

    }


    renderizarAtividades();

    renderizarResumoDia();

}


/* =========================================================
   LIMPAR DETALHES
========================================================= */

function limparDetalhesDia() {

    if (!painelDetalhesDia) {

        return;

    }


    painelDetalhesDia.innerHTML = `

        <div class="calendario-detalhes-vazio">

            <i class="bi bi-calendar3"></i>


            <h2>
                Selecione um dia
            </h2>


            <p>
                Selecione uma data no calendário
                para visualizar suas atividades.
            </p>

        </div>

    `;

}


/* =========================================================
   FORMATAR DURAÇÃO
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


    if (horas > 0) {

        return `${horas}h ${minutos}min`;

    }


    return `${minutos}min`;

}


/* =========================================================
   CARREGAR ESTUDOS
========================================================= */

async function carregarEstudos(data) {

    try {

        const resposta =
            await fetch(
                `/calendario/estudos?data=${data}`
            );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar os estudos."
            );

        }


        dadosDia.estudos =
            await resposta.json();


    } catch (erro) {

        console.error(
            "Erro ao carregar estudos:",
            erro
        );

        dadosDia.estudos = [];

    }

}


/* =========================================================
   CARREGAR TAREFAS
========================================================= */

async function carregarTarefas(data) {

    try {

        const resposta =
            await fetch(
                `/calendario/tarefas?data=${data}`
            );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar as tarefas."
            );

        }


        dadosDia.tarefas =
            await resposta.json();


    } catch (erro) {

        console.error(
            "Erro ao carregar tarefas:",
            erro
        );

        dadosDia.tarefas = [];

    }

}


/* =========================================================
   CARREGAR PROVAS
========================================================= */

async function carregarProvas(data) {

    try {

        const resposta =
            await fetch(
                `/calendario/provas?data=${data}`
            );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar as provas."
            );

        }


        dadosDia.provas =
            await resposta.json();


    } catch (erro) {

        console.error(
            "Erro ao carregar provas:",
            erro
        );

        dadosDia.provas = [];

    }

}


/* =========================================================
   CARREGAR ANOTAÇÃO
========================================================= */

async function carregarAnotacao(data) {

    try {

        const resposta =
            await fetch(
                `/calendario/anotacao?data=${data}`
            );


        if (!resposta.ok) {

            throw new Error(
                "Não foi possível carregar a anotação."
            );

        }


        const anotacao =
            await resposta.json();


        dadosDia.anotacao =
            anotacao.texto || "";


    } catch (erro) {

        console.error(
            "Erro ao carregar anotação:",
            erro
        );

        dadosDia.anotacao = "";

    }

}


/* =========================================================
   SALVAR ANOTAÇÃO
========================================================= */

async function salvarAnotacao() {

    const campo =
        document.querySelector(
            ".calendario-detalhes-dia .campo-anotacao"
        );


    if (!campo) {

        return;

    }


    const texto =
        campo.value.trim();


    if (!texto) {

        alert(
            "Escreva alguma coisa antes de salvar."
        );

        return;

    }


    if (
        diaSelecionado === null ||
        mesSelecionado === null ||
        anoSelecionado === null
    ) {

        return;

    }


    const dataISO =
        `${anoSelecionado}-${String(
            mesSelecionado + 1
        ).padStart(2, "0")}-${String(
            diaSelecionado
        ).padStart(2, "0")}`;


    try {

        const resposta =
            await fetch(
                "/calendario/anotacao",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            csrfToken

                    },

                    body: JSON.stringify({

                        data: dataISO,

                        texto: texto

                    })

                }
            );


        const resultado =
            await resposta.json();


        if (!resposta.ok) {

            throw new Error(
                resultado.erro ||
                "Erro ao salvar anotação."
            );

        }


        dadosDia.anotacao =
            texto;


        mostrarMensagemAnotacao(
            "Anotação salva com sucesso."
        );


        /*
            Atualiza o indicador da anotação.
        */

        if (!indicadoresMes[dataISO]) {

            indicadoresMes[dataISO] = {};

        }


        indicadoresMes[dataISO].anotacao =
            true;


        renderizarCalendario();


        /*
            Recupera o dia selecionado
            depois de reconstruir o calendário.
        */

        const diaAtualizado =
            [...document.querySelectorAll(
                "#calendario-dias .dia"
            )]
                .find((elemento) => {

                    return elemento.querySelector(
                        ".numero-dia"
                    )?.textContent.trim() ===
                    String(diaSelecionado);

                });


        if (diaAtualizado) {

            diaAtualizado.classList.add(
                "dia-selecionado"
            );

        }

    } catch (erro) {

        console.error(
            "Erro ao salvar anotação:",
            erro
        );

        alert(
            "Não foi possível salvar a anotação."
        );

    }

}


/* =========================================================
   MENSAGEM DA ANOTAÇÃO
========================================================= */

function mostrarMensagemAnotacao(
    mensagem
) {

    const elemento =
        document.getElementById(
            "mensagem-anotacao"
        );


    if (!elemento) {

        return;

    }


    elemento.textContent =
        mensagem;


    elemento.classList.add(
        "mensagem-anotacao-visivel"
    );


    setTimeout(() => {

        elemento.classList.remove(
            "mensagem-anotacao-visivel"
        );

    }, 3000);

}


/* =========================================================
   RESUMO DO DIA
========================================================= */

function renderizarResumoDia() {

    const atividades =
        document.querySelector(
            ".calendario-detalhes-dia .atividades-dia"
        );


    if (!atividades) {

        return;

    }


    let resumo = [];


    /* =====================================================
       PROVA
    ===================================================== */

    if (dadosDia.provas.length > 0) {

        resumo.push(`

            <span
                class="resumo-item resumo-prova"
            >

                <i class="bi bi-file-earmark-text"></i>

                Prova realizada

            </span>

        `);

    }


    /* =====================================================
       TAREFAS
    ===================================================== */

    if (dadosDia.tarefas.length > 0) {

        const quantidade =
            dadosDia.tarefas.length;


        resumo.push(`

            <span
                class="resumo-item resumo-tarefa"
            >

                <i class="bi bi-check2-square"></i>

                ${quantidade}

                ${
                    quantidade === 1
                        ? "tarefa concluída"
                        : "tarefas concluídas"
                }

            </span>

        `);

    }


    /* =====================================================
       ESTUDOS
    ===================================================== */

    if (dadosDia.estudos.length > 0) {

        let totalSegundos = 0;


        dadosDia.estudos.forEach((estudo) => {

            totalSegundos +=
                Number(
                    estudo.duracao
                ) || 0;

        });


        if (totalSegundos > 0) {

            resumo.push(`

                <span
                    class="resumo-item resumo-estudo"
                >

                    <i class="bi bi-clock-history"></i>

                    ${formatarDuracao(
                        totalSegundos
                    )}

                    estudados

                </span>

            `);

        }

    }


    /* =====================================================
       ANOTAÇÃO
    ===================================================== */

    if (dadosDia.anotacao) {

        resumo.push(`

            <span
                class="resumo-item resumo-anotacao"
            >

                <i class="bi bi-journal-text"></i>

                Anotação registrada

            </span>

        `);

    }


    /* =====================================================
       NENHUMA ATIVIDADE
    ===================================================== */

    if (resumo.length === 0) {

        atividades.insertAdjacentHTML(

            "afterbegin",

            `

                <div class="resumo-dia">

                    <span class="resumo-dia-titulo">
                        Resumo do dia
                    </span>


                    <p class="resumo-vazio">

                        Nenhuma atividade registrada.

                    </p>

                </div>

            `

        );


        return;

    }


    /* =====================================================
       INSERIR RESUMO
    ===================================================== */

    atividades.insertAdjacentHTML(

        "afterbegin",

        `

            <div class="resumo-dia">

                <span class="resumo-dia-titulo">
                    Resumo do dia
                </span>


                <div class="resumo-lista">

                    ${resumo.join("")}

                </div>

            </div>

        `

    );

}


/* =========================================================
   MÊS ANTERIOR
========================================================= */

if (botaoMesAnterior) {

    botaoMesAnterior.addEventListener(
        "click",
        async () => {

            mesAtual--;


            if (mesAtual < 0) {

                mesAtual = 11;

                anoAtual--;

            }


            diaSelecionado = null;

            mesSelecionado = null;

            anoSelecionado = null;


            identificadorSelecao++;


            limparDetalhesDia();


            await carregarIndicadoresMes();

            renderizarCalendario();

        }
    );

}


/* =========================================================
   PRÓXIMO MÊS
========================================================= */

if (botaoMesProximo) {

    botaoMesProximo.addEventListener(
        "click",
        async () => {

            mesAtual++;


            if (mesAtual > 11) {

                mesAtual = 0;

                anoAtual++;

            }


            diaSelecionado = null;

            mesSelecionado = null;

            anoSelecionado = null;


            identificadorSelecao++;


            limparDetalhesDia();


            await carregarIndicadoresMes();

            renderizarCalendario();

        }
    );

}


/* =========================================================
   INICIALIZAÇÃO
========================================================= */

async function inicializarCalendario() {

    /*
        Verifica se estamos realmente
        na página do calendário.
    */

    if (
        !elementoMesAtual ||
        !elementoDiasCalendario
    ) {

        return;

    }


    await carregarIndicadoresMes();

    renderizarCalendario();

}


inicializarCalendario();