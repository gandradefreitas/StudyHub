document.addEventListener("DOMContentLoaded", () => {


    /* =====================================================
       ELEMENTOS
    ===================================================== */

    const card =
        document.querySelector(".questoes-card");

    if (!card) {
        return;
    }


    const botaoIniciarEstudo =
        document.querySelector(
            "#botao-iniciar-estudo"
        );


    const botaoFinalizarEstudo =
        document.querySelector(
            "#botao-finalizar-estudo"
        );


    const cronometroEstudos =
        document.querySelector(
            "#cronometro-questoes"
        );


    const numeroQuestao =
        card.dataset.questao;

    const respostaUsuario =
        card.dataset.respostaUsuario;

    const respostaCorreta =
        card.dataset.respostaCorreta;

    const comentario =
        card.dataset.comentario || "";

    const questaoBloqueada =
        card.dataset.bloqueada === "true";

    const proximaTentativa =
        card.dataset.proximaTentativa;


    const alternativas =
        document.querySelectorAll(
            ".questoes-alternativa input"
        );


    const botaoResponder =
        document.querySelector(
            "#botao-responder"
        );


    const resultado =
        document.querySelector(
            "#resultado-questao"
        );


    const bloqueio =
        document.querySelector(
            "#bloqueio-questao"
        );

    if (
        !numeroQuestao ||
        !alternativas.length ||
        !botaoResponder ||
        !resultado ||
        !bloqueio
    ) {

        return;

    }


    /* =====================================================
       CRONÔMETRO DE ESTUDO
    ===================================================== */

    if (botaoIniciarEstudo) {

        botaoIniciarEstudo.addEventListener(
            "click",
            () => {

                console.log(
                    "CLIQUE NO BOTÃO INICIAR"
                );


                botaoIniciarEstudo.disabled = true;

                botaoIniciarEstudo.textContent =
                    "Iniciando...";


                fetch(
                    "/estudos/iniciar-ajax",
                    {
                        method: "POST"
                    }
                )
                .then(
                    resposta => {

                        if (!resposta.ok) {

                            throw new Error(
                                "Não foi possível iniciar o estudo."
                            );

                        }

                        return resposta.json();

                    }
                )
                .then(
                    dados => {

                        if (!dados.sucesso) {

                            throw new Error(
                                dados.erro ||
                                "Erro ao iniciar estudo."
                            );

                        }


                        window.location.reload();

                    }
                )
                .catch(
                    erro => {

                        console.error(
                            erro
                        );

                        botaoIniciarEstudo.disabled = false;

                        botaoIniciarEstudo.textContent =
                            "Iniciar estudo";

                        alert(
                            erro.message
                        );

                    }
                );

            }
        );

    }


    if (botaoFinalizarEstudo) {

        botaoFinalizarEstudo.addEventListener(
            "click",
            () => {

                botaoFinalizarEstudo.disabled = true;

                botaoFinalizarEstudo.textContent =
                    "Finalizando...";


                fetch(
                    "/estudos/finalizar-ajax",
                    {
                        method: "POST"
                    }
                )
                .then(
                    resposta => {

                        if (!resposta.ok) {

                            throw new Error(
                                "Não foi possível finalizar o estudo."
                            );

                        }

                        return resposta.json();

                    }
                )
                .then(
                    dados => {

                        if (!dados.sucesso) {

                            throw new Error(
                                dados.erro ||
                                "Erro ao finalizar estudo."
                            );

                        }


                        window.location.reload();

                    }
                )
                .catch(
                    erro => {

                        console.error(
                            erro
                        );

                        botaoFinalizarEstudo.disabled = false;

                        botaoFinalizarEstudo.textContent =
                            "Finalizar estudo";

                        alert(
                            erro.message
                        );

                    }
                );

            }
        );

    }

    /* =====================================================
       CRONÔMETRO VISUAL
    ===================================================== */

    if (
        cronometroEstudos &&
        cronometroEstudos.dataset.inicio
    ) {

        const inicio =
            new Date(
                cronometroEstudos.dataset.inicio
            );


        function atualizarCronometroEstudo() {

            const agora =
                new Date();


            const diferenca =
                Math.floor(
                    (agora - inicio) / 1000
                );


            const horas =
                Math.floor(
                    diferenca / 3600
                );


            const minutos =
                Math.floor(
                    (diferenca % 3600) / 60
                );


            const segundos =
                diferenca % 60;


            cronometroEstudos.textContent =
                String(horas).padStart(2, "0")
                + ":"
                + String(minutos).padStart(2, "0")
                + ":"
                + String(segundos).padStart(2, "0");

        }


        atualizarCronometroEstudo();

        setInterval(
            atualizarCronometroEstudo,
            1000
        );

    }
    /* =====================================================
       VERIFICAR BLOQUEIO
    ====================================================== */

    if (
        questaoBloqueada &&
        proximaTentativa
    ) {

        const data =
            new Date(
                proximaTentativa
            ).getTime();


        if (!isNaN(data)) {

            mostrarBloqueio(data);

            return;

        }

    }

    /* =====================================================
       RESPONDER QUESTÃO
    ====================================================== */

    botaoResponder.addEventListener(
        "click",
        () => {


            const selecionada =
                document.querySelector(
                    ".questoes-alternativa input:checked"
                );


            /* =============================================
               NENHUMA ALTERNATIVA
            ============================================= */

            if (!selecionada) {

                alert(
                    "Selecione uma alternativa antes de responder."
                );

                return;

            }


            const respostaEscolhida =
                selecionada.value;


            /* =============================================
               DESABILITAR BOTÃO DURANTE ENVIO
            ============================================= */

            botaoResponder.disabled = true;


            botaoResponder.textContent =
                "Enviando...";


            /* =============================================
               ENVIAR PARA O SERVIDOR
            ============================================= */

            fetch(
                "/questoes/responder",
                {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({

                        questao_numero:
                            numeroQuestao,

                        resposta:
                            respostaEscolhida

                    })

                }
            )
            .then(
                resposta => {

                    if (!resposta.ok) {

                        throw new Error(
                            "Erro ao enviar resposta."
                        );

                    }

                    return resposta.json();

                }
            )
            .then(
                dados => {

                    console.log(
                        "Resposta recebida do servidor:",
                        dados
                    );


                    /* =============================================
                       VERIFICAR SUCESSO
                    ============================================= */

                    if (!dados.sucesso) {

                        throw new Error(
                            dados.erro ||
                            "Não foi possível registrar a resposta."
                        );

                    }

                    /* =============================================
                       BLOQUEAR ALTERNATIVAS
                    ============================================= */

                    alternativas.forEach(
                        alternativa => {

                            alternativa.disabled = true;

                        }
                    );


                    /* =============================================
                       CORREÇÃO
                    ============================================= */

                    if (dados.correta) {

                        resultado.className =
                            "questoes-resultado questoes-resultado-correto";

                        resultado.innerHTML = `
                    
                            <p class="questoes-resultado-titulo">
                                ✓ Resposta correta!
                            </p>
                    
                            <p class="questoes-resultado-texto">
                    
                                Você selecionou a alternativa
                                <strong>${dados.resposta_usuario}</strong>.
                    
                            </p>
                    
                            <p class="questoes-resultado-comentario">
                    
                                ${card.dataset.comentario || "Não há comentário disponível."}
                    
                            </p>
                    
                        `;

                    } else {

                        resultado.className =
                            "questoes-resultado questoes-resultado-incorreto";

                        resultado.innerHTML = `
                    
                            <p class="questoes-resultado-titulo">
                                ✕ Resposta incorreta.
                            </p>
                    
                            <p class="questoes-resultado-texto">
                    
                                Você marcou a alternativa
                                <strong>${dados.resposta_usuario}</strong>.
                    
                                A resposta correta é
                                <strong>${dados.resposta_correta}</strong>.
                    
                            </p>
                    
                            <p class="questoes-resultado-comentario">
                    
                                ${card.dataset.comentario || "Não há comentário disponível."}
                    
                            </p>
                    
                        `;

                    }


                    /* =============================================
                       MOSTRAR RESULTADO
                    ============================================= */

                    resultado.hidden = false;


                    /* =============================================
                       INICIAR BLOQUEIO
                    ============================================= */

                    const dataBloqueio =
                        new Date(
                            dados.proxima_tentativa
                        ).getTime();


                    if (!isNaN(dataBloqueio)) {

                        mostrarBloqueio(dataBloqueio);

                    }


                    /* =============================================
                       BLOQUEAR BOTÃO
                    ============================================= */

                    botaoResponder.disabled = true;

                    botaoResponder.textContent =
                        "Questão respondida";

                }
            )
            .catch(
                erro => {

                    console.error(
                        "Erro:",
                        erro
                    );


                    /* =============================================
                       RESTAURAR BOTÃO EM CASO DE ERRO
                    ============================================= */

                    botaoResponder.disabled = false;

                    botaoResponder.textContent =
                        "Responder";


                    alert(
                        "Não foi possível registrar sua resposta."
                    );

                }
            );

        }
    );


    /* =====================================================
       FUNÇÃO DE BLOQUEIO
    ====================================================== */

    function mostrarBloqueio(
        proximaTentativa
    ) {

        /* =====================================================
           BLOQUEAR ALTERNATIVAS
        ====================================================== */

        alternativas.forEach(
            alternativa => {

                alternativa.disabled = true;

            }
        );


        /* =====================================================
           BLOQUEAR BOTÃO
        ====================================================== */

        botaoResponder.disabled = true;

        botaoResponder.textContent =
            "Questão bloqueada";


        /* =====================================================
           MOSTRAR BLOQUEIO
        ====================================================== */

        bloqueio.className =
            "questoes-bloqueio";


        bloqueio.innerHTML = `
    
            <p class="questoes-bloqueio-titulo">
                🔒 Questão bloqueada
            </p>
    
    
            <p class="questoes-bloqueio-texto">
    
                Nova tentativa disponível em:
    
            </p>
    
    
            <strong
                id="contador-bloqueio"
                class="questoes-contador-bloqueio"
            >
                Calculando...
            </strong>
    
        `;


        bloqueio.hidden = false;


        /* =====================================================
           CONTADOR
        ====================================================== */

        const contador =
            document.querySelector(
                "#contador-bloqueio"
            );


        let intervalo = null;


        function atualizarContador() {

            const agora =
                Date.now();


            const restante =
                Number(proximaTentativa) -
                agora;


            /* =============================================
               BLOQUEIO TERMINOU
            ============================================= */

            if (restante <= 0) {

                clearInterval(
                    intervalo
                );


                /*
                 * O servidor é responsável pelo bloqueio.
                 *
                 * Recarregamos a página para que o Flask
                 * consulte novamente o banco.
                 */

                window.location.reload();

                return;

            }


            /* =============================================
               CONVERSÃO DO TEMPO
            ============================================= */

            const segundosTotais =
                Math.floor(
                    restante / 1000
                );


            const dias =
                Math.floor(
                    segundosTotais / 86400
                );


            const horas =
                Math.floor(
                    (segundosTotais % 86400) / 3600
                );


            const minutos =
                Math.floor(
                    (segundosTotais % 3600) / 60
                );


            const segundos =
                segundosTotais % 60;


            /* =============================================
               FORMATAR
            ============================================= */

            let texto = "";


            if (dias > 0) {

                texto +=
                    `${dias} ${dias === 1 ? "dia" : "dias"} `;

            }


            if (
                horas > 0 ||
                dias > 0
            ) {

                texto +=
                    `${String(horas).padStart(2, "0")}h `;

            }


            texto +=
                `${String(minutos).padStart(2, "0")}min `;


            texto +=
                `${String(segundos).padStart(2, "0")}s`;


            contador.textContent =
                texto;

        }


        /* =====================================================
           ATUALIZAR IMEDIATAMENTE
        ====================================================== */

        atualizarContador();


        /* =====================================================
           ATUALIZAR A CADA SEGUNDO
        ====================================================== */

        intervalo =
            setInterval(
                atualizarContador,
                1000
            );

    }


});