const CHAVE_PROVA = `prova_${prova.id}`;

let questaoAtual = Number(
    localStorage.getItem(`${CHAVE_PROVA}_questao`)
) || 0;


const respostas = JSON.parse(
    localStorage.getItem(CHAVE_PROVA)
) || {};


let revisao = [];
let tempoRestante;
let intervaloCronometro;


let linguaEscolhida =
    localStorage.getItem(
        `${CHAVE_PROVA}_lingua`
    );

let questoesProva = [];


function atualizarQuestoesProva() {

    questoesProva =
        questoes.filter(questao => {

            // Questões normais
            if (!questao.lingua) {
                return true;
            }

            // Questões de língua estrangeira
            return questao.lingua === linguaEscolhida;

        });

}

function selecionarLingua() {

    const opcoes =
        document.querySelectorAll(
            'input[name="lingua"]'
        );

    const botao =
        document.getElementById(
            "confirmar-lingua"
        );

    if (!botao || opcoes.length === 0) {
        return;
    }

    opcoes.forEach(opcao => {

        opcao.addEventListener(
            "change",
            () => {

                botao.disabled = false;

            }
        );

    });

    botao.addEventListener(
        "click",
        () => {

            const selecionada =
                document.querySelector(
                    'input[name="lingua"]:checked'
                );

            if (!selecionada) {
                return;
            }

            linguaEscolhida =
                selecionada.value;

            localStorage.setItem(
                `${CHAVE_PROVA}_lingua`,
                linguaEscolhida
            );

            iniciarProva();

        }
    );
}

function iniciarProva() {

    atualizarQuestoesProva();

    const selecaoLingua =
        document.getElementById("selecao-lingua");

    if (selecaoLingua) {
        selecaoLingua.style.display = "none";
    }

    document
        .querySelector(".conteudo-prova")
        .classList.remove("prova-oculta");

    document
        .querySelector(".painel-lateral")
        .classList.remove("prova-oculta");

    document.getElementById(
        "total-questoes"
    ).textContent =
        questoesProva.length;

    carregarQuestoesGrade();

    carregarQuestao();

    iniciarCronometro();
}

function carregarQuestoesGrade() {

    const grade =
        document.getElementById("grade-questoes");


    if (!grade) {

        console.error(
            "Elemento #grade-questoes não encontrado."
        );

        return;
    }


    grade.innerHTML = "";


    questoesProva.forEach(
        (questao, indice) => {

            const botao =
                document.createElement("button");


            botao.className =
                "numero-questao";


            botao.dataset.questao =
                indice + 1;


            botao.id =
                `questao-${indice + 1}`;


            botao.textContent =
                indice + 1;


            botao.addEventListener(
                "click",
                () => {

                    selecionarQuestao(
                        indice + 1
                    );

                }
            );


            grade.appendChild(botao);

        }
    );

    atualizarEstadoQuestoes();

    atualizarQuestoesRespondidas();

    atualizarQuestaoAtual();


}

function ehImagem(valor) {

    if (typeof valor !== "string") {
        return false;
    }

    return /\.(png|jpg|jpeg|webp|gif)$/i.test(
        limparCaminhoImagem(valor)
    );

}


function limparCaminhoImagem(valor) {

    return valor.replace(/^"|"$/g, "");

}


function carregarConteudoQuestao(questao) {

    const container =
        document.getElementById("conteudo-questao");

    console.log("QUESTÃO ATUAL:", questao);
    console.log("PERGUNTA:", questao.pergunta);
    container.innerHTML = "";


    // ENUNCIADO

    const enunciado =
        document.createElement("p");

    enunciado.className =
        "enunciado";

    enunciado.innerHTML =
        questao.enunciado;

    container.appendChild(enunciado);


    // IMAGEM

    if (questao.imagem) {

        const containerImagem =
            document.createElement("div");

        containerImagem.className =
            "container-imagem";


        const imagem =
            document.createElement("img");

        imagem.className =
            "imagem-questao";

        imagem.src =
            STATIC_URL + questao.imagem;

        imagem.alt =
            `Imagem da questão ${questao.numero}`;


        containerImagem.appendChild(imagem);

        container.appendChild(containerImagem);

    }


    // PERGUNTA

    if (questao.pergunta) {

        const pergunta =
            document.createElement("p");

        pergunta.className =
            "pergunta";

        pergunta.innerHTML =
            questao.pergunta;

        container.appendChild(pergunta);

    }

}

function obterEstatisticas(){

    let acertos = 0;
    let respondidas = 0;
    let questoesErradas = [];


    questoesProva.forEach((questao, indice)=>{


        if(respostas[indice] !== undefined){

            respondidas++;


            if(respostas[indice] === questao.resposta){

                acertos++;

            } else {


                questoesErradas.push({

                    numero: questao.numero,

                    enunciado: questao.enunciado,

                    alternativas: questao.alternativas,

                    respostaUsuario: respostas[indice],

                    respostaCorreta: questao.resposta,

                    comentario: questao.comentario

                });


            }

        }


    });


    return {

        acertos: acertos,

        erros: respondidas - acertos,

        naoRespondidas: questoesProva.length - respondidas,

        total: questoesProva.length,

        questoesErradas: questoesErradas

    };

}
function converterTempo(tempo){

    const partes = tempo.split(":");

    const horas = Number(partes[0]);
    const minutos = Number(partes[1]);
    const segundos = Number(partes[2]);


    return (horas * 3600) + (minutos * 60) + segundos;

}

function iniciarCronometro() {

    const chaveCronometro =
        `${CHAVE_PROVA}_fim`;

    let fimProva =
        localStorage.getItem(chaveCronometro);


    if (!fimProva) {

        fimProva =
            Date.now() +
            converterTempo(tempoProva) * 1000;

        localStorage.setItem(
            chaveCronometro,
            fimProva
        );

    } else {

        fimProva = Number(fimProva);

    }


    function contarTempo() {

        const agora = Date.now();


        tempoRestante =
            Math.max(
                0,
                Math.ceil(
                    (fimProva - agora) / 1000
                )
            );


        atualizarCronometro();


        if (tempoRestante <= 0) {

            clearInterval(
                intervaloCronometro
            );

            alert(
                "Tempo encerrado! A prova será finalizada."
            );

            finalizarProva();

        }

    }


    contarTempo();


    intervaloCronometro =
        setInterval(
            contarTempo,
            1000
        );
}

function finalizarProva() {

    const resultado =
        obterEstatisticas();


    const dadosResultado = {

        prova_id:
            prova.id,

        questoes:
            questoesProva,

        acertos:
            resultado.acertos,

        erros:
            resultado.erros,

        questoesErradas:
            resultado.questoesErradas,

        naoRespondidas:
            resultado.naoRespondidas,

        respostas:
            respostas,

        tempoGasto:
            converterTempoGasto(),

        total:
            resultado.total

    };


    console.log(
        "================================"
    );

    console.log(
        "ENVIANDO RESULTADO PARA O FLASK"
    );

    console.log(
        dadosResultado
    );

    console.log(
        "================================"
    );


    fetch(
        "/provas/resultado",
        {

            method: "POST",

            headers: {

                "Content-Type":
                    "application/json"

            },

            body:
                JSON.stringify(
                    dadosResultado
                )

        }
    )

    .then(response => {

        console.log(
            "Status da resposta:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `Servidor respondeu com ${response.status}`
            );

        }


        return response.json();

    })

    .then(dados => {

        console.log(
            "Resposta recebida do Flask:",
            dados
        );


        if (
            dados.status !== "ok"
        ) {

            throw new Error(
                "O servidor não confirmou o resultado."
            );

        }


        /*
            Somente depois de o servidor
            confirmar que recebeu os dados,
            limpamos o localStorage.
        */

        localStorage.removeItem(
            CHAVE_PROVA
        );

        localStorage.removeItem(
            `${CHAVE_PROVA}_questao`
        );

        localStorage.removeItem(
            `${CHAVE_PROVA}_lingua`
        );

        localStorage.removeItem(
            `${CHAVE_PROVA}_fim`
        );


        window.location.href =
            "/provas/resultado";

    })

    .catch(erro => {

        console.error(
            "ERRO AO ENVIAR RESULTADO:",
            erro
        );


        alert(
            "Não foi possível enviar o resultado da prova."
        );

    });

}
function atualizarCronometro(){

    const horas =
        Math.floor(tempoRestante / 3600);


    const minutos =
        Math.floor((tempoRestante % 3600) / 60);


    const segundos =
        tempoRestante % 60;


    document.querySelector(".cronometro").innerHTML =

        `${String(horas).padStart(2,"0")}:` +
        `${String(minutos).padStart(2,"0")}:` +
        `${String(segundos).padStart(2,"0")}`;

}
function converterTempoGasto(){

    const tempoUtilizado =
        converterTempo(tempoProva) - tempoRestante;

    const horas =
        Math.floor(tempoUtilizado / 3600);

    const minutos =
        Math.floor((tempoUtilizado % 3600) / 60);

    const segundos =
        tempoUtilizado % 60;

    return (
        String(horas).padStart(2,"0") + ":" +
        String(minutos).padStart(2,"0") + ":" +
        String(segundos).padStart(2,"0")
    );

}

function carregarQuestao() {

    if (
        questaoAtual < 0 ||
        questaoAtual >= questoesProva.length
    ) {
        questaoAtual = 0;

        localStorage.setItem(
            `${CHAVE_PROVA}_questao`,
            questaoAtual
        );
    }

    const questao =
        questoesProva[questaoAtual];

    document.getElementById(
        "contador-questao"
    ).textContent = questaoAtual + 1;


    // Número da questão

    document.getElementById("numero-questao").innerHTML =
        `Questão ${questao.numero}`;


    // Conteúdo da questão

    carregarConteudoQuestao(questao);


    // Alternativas

    const areaAlternativas =
        document.getElementById("alternativas");


    areaAlternativas.innerHTML = "";


    questao.alternativas.forEach(
        (alternativa, indice) => {

            let conteudoAlternativa;


            // Verifica se a alternativa é uma imagem

            if (ehImagem(alternativa)) {

                const caminhoImagem =
                    limparCaminhoImagem(alternativa);


                conteudoAlternativa = `

                    <img
                        class="imagem-alternativa"
                        src="${STATIC_URL}${caminhoImagem}"
                        alt="Alternativa ${"ABCDE"[indice]}"
                    >

                `;

            } else {

                // Alternativa normal de texto

                conteudoAlternativa =
                    alternativa;

            }


            areaAlternativas.innerHTML += `

                <label class="alternativa">

                    <input
                        type="radio"
                        name="questao"
                        value="${indice}"
                        ${
                            respostas[questaoAtual] == indice
                                ? "checked"
                                : ""
                        }
                    >

                    <span class="letra-alternativa">
                        ${"ABCDE"[indice]})
                    </span>

                    <span class="conteudo-alternativa">
                        ${conteudoAlternativa}
                    </span>

                </label>

            `;

        }
    );


    // Eventos dos radio buttons

    const radios =
        document.querySelectorAll(
            'input[name="questao"]'
        );


    radios.forEach(radio => {

        radio.addEventListener(
            "change",
            () => {

                respostas[questaoAtual] =
                    Number(radio.value);


                // Ao responder, remove automaticamente
                // a questão da revisão

                const numero =
                    questaoAtual + 1;


                revisao =
                    revisao.filter(
                        q => q !== numero
                    );


                localStorage.setItem(
                    CHAVE_PROVA,
                    JSON.stringify(respostas)
                );


                atualizarEstadoQuestoes();


                console.log(respostas);

            }
        );

    });


    // Atualiza estado da interface
    atualizarEstadoQuestoes();

    atualizarQuestoesRespondidas();

    atualizarQuestaoAtual();



}



function proximaQuestao() {

    if (
        questaoAtual <
        questoesProva.length - 1
    ) {

        questaoAtual++;


        localStorage.setItem(
            `${CHAVE_PROVA}_questao`,
            questaoAtual
        );


        carregarQuestao();

    }
}

function voltarQuestao() {

    if (questaoAtual > 0) {

        questaoAtual--;


        localStorage.setItem(
            `${CHAVE_PROVA}_questao`,
            questaoAtual
        );


        carregarQuestao();

    }
}

function selecionarQuestao(numero){

    questaoAtual = numero - 1;

    localStorage.setItem(
        `${CHAVE_PROVA}_questao`,
        questaoAtual
    );

    carregarQuestao();

}
function atualizarQuestaoAtual(){

    const botoes =
        document.querySelectorAll(
            ".numero-questao"
        );


    botoes.forEach(botao => {

        botao.classList.remove(
            "questao-atual"
        );

    });


    const botaoAtual =
        document.getElementById(
            `questao-${questaoAtual + 1}`
        );


    if (botaoAtual) {

        botaoAtual.classList.add(
            "questao-atual"
        );

    }

}
function atualizarQuestoesRespondidas(){

    const botoes =
        document.querySelectorAll(".numero-questao");


    botoes.forEach(botao => {

        const numero =
            Number(botao.dataset.questao);


        if(respostas[numero - 1] !== undefined){

            botao.classList.add("questao-respondida");

        } else {

            botao.classList.remove("questao-respondida");

        }

    });

}

function marcarRevisao() {

    const numero =
        questaoAtual + 1;


    if (revisao.includes(numero)) {

        // Remove da revisão

        revisao =
            revisao.filter(
                q => q !== numero
            );

    } else {

        // Adiciona à revisão

        revisao.push(numero);

    }


    // Atualiza imediatamente a grade

    atualizarEstadoQuestoes();

}

function atualizarEstadoQuestoes() {

    const botoes =
        document.querySelectorAll(
            ".numero-questao"
        );


    botoes.forEach(botao => {

        const numero =
            Number(botao.dataset.questao);


        // Remove os estados anteriores

        botao.classList.remove(
            "questao-respondida",
            "questao-revisao",
            "questao-atual"
        );


        // Questão respondida

        if (
            respostas[numero - 1] !== undefined
        ) {

            botao.classList.add(
                "questao-respondida"
            );

        }


        // Questão marcada para revisão

        if (
            revisao.includes(numero)
        ) {

            botao.classList.add(
                "questao-revisao"
            );

        }


        // Questão atual

        if (
            numero === questaoAtual + 1
        ) {

            botao.classList.add(
                "questao-atual"
            );

        }

    });

}




document
    .getElementById("proxima")
    .addEventListener("click", proximaQuestao);


document
    .getElementById("anterior")
    .addEventListener("click", voltarQuestao);

document
    .getElementById("marcar-revisao")
    .addEventListener("click", marcarRevisao);

document
    .getElementById("finalizar")
    .addEventListener("click", finalizarProva);


if (prova.dia === "Primeiro Dia") {

    if (linguaEscolhida) {

        iniciarProva();

    } else {

        selecionarLingua();

    }

} else {

    iniciarProva();

}