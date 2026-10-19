document.addEventListener("DOMContentLoaded", () => {
    const cronometro = document.getElementById(
        "cronometro-questoes"
    );

    const statusCronometro = document.getElementById(
        "status-cronometro-questoes"
    );

    const elementoCsrf = document.querySelector(
        'meta[name="csrf-token"]'
    );

    if (!cronometro || !statusCronometro) {
        return;
    }

    if (!elementoCsrf) {
        console.error("Token CSRF não encontrado.");
        statusCronometro.textContent =
            "Não foi possível iniciar o cronômetro.";

        return;
    }

    const tokenCsrf = elementoCsrf.content;

    const TEMPO_INATIVIDADE = 5 * 60 * 1000;
    const INTERVALO_HEARTBEAT = 15 * 1000;
    const INTERVALO_ATIVIDADE = 5 * 1000;

    let duracaoAcumulada = 0;
    let inicioContagemLocal = null;
    let ultimaAtividadeLocal = Date.now();

    let pausado = true;
    let encerrando = false;
    let requisicaoPendente = false;

    let ultimaAtividadeEnviada = 0;

    function formatarTempo(segundos) {
        segundos = Math.max(0, Math.floor(segundos));

        const horas = Math.floor(segundos / 3600);

        const minutos = Math.floor(
            (segundos % 3600) / 60
        );

        const segundosRestantes = segundos % 60;

        return [
            String(horas).padStart(2, "0"),
            String(minutos).padStart(2, "0"),
            String(segundosRestantes).padStart(2, "0")
        ].join(":");
    }

    function obterDuracaoAtual() {
        let duracao = duracaoAcumulada;

        if (!pausado && inicioContagemLocal !== null) {
            const agora = Date.now();

            const limiteLocal =
                ultimaAtividadeLocal + TEMPO_INATIVIDADE;

            const fimContagem = Math.min(
                agora,
                limiteLocal
            );

            const segundosAdicionais = Math.floor(
                Math.max(
                    0,
                    fimContagem - inicioContagemLocal
                ) / 1000
            );

            duracao += segundosAdicionais;
        }

        return duracao;
    }

    function atualizarExibicao() {
        if (!encerrando) {
            cronometro.textContent = formatarTempo(
                obterDuracaoAtual()
            );
        }
    }

    function atualizarEstadoLocal(dados) {
        duracaoAcumulada = Number(dados.duracao) || 0;

        pausado = Boolean(dados.pausado);

        if (pausado) {
            inicioContagemLocal = null;

            statusCronometro.textContent =
                "Cronômetro pausado por inatividade.";
        } else {
            inicioContagemLocal = Date.now();

            ultimaAtividadeLocal = Date.now();

            statusCronometro.textContent =
                "Tempo de estudo sendo contabilizado.";
        }

        atualizarExibicao();
    }

    async function enviarEvento(tipoEvento) {
        if (encerrando || requisicaoPendente) {
            return null;
        }

        requisicaoPendente = true;

        try {
            const resposta = await fetch(
                "/questoes/estudo/atividade",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": tokenCsrf
                    },

                    body: JSON.stringify({
                        tipo_evento: tipoEvento
                    }),

                    credentials: "same-origin"
                }
            );

            if (!resposta.ok) {
                throw new Error(
                    `Erro HTTP ${resposta.status}`
                );
            }

            const dados = await resposta.json();

            if (!dados.sucesso) {
                throw new Error(
                    dados.erro || "Erro ao atualizar cronômetro."
                );
            }

            duracaoAcumulada = Number(dados.duracao) || 0;

            pausado = Boolean(dados.pausado);

            if (pausado) {
                inicioContagemLocal = null;

                statusCronometro.textContent =
                    "Cronômetro pausado por inatividade.";
            } else {
                inicioContagemLocal = Date.now();

                statusCronometro.textContent =
                    "Tempo de estudo sendo contabilizado.";
            }

            atualizarExibicao();

            return dados;

        } catch (erro) {
            console.error(
                "Erro ao atualizar cronômetro:",
                erro
            );

            statusCronometro.textContent =
                "Reconectando cronômetro...";

            return null;

        } finally {
            requisicaoPendente = false;
        }
    }

    async function iniciarCronometro() {
        statusCronometro.textContent =
            "Iniciando cronômetro...";

        try {
            const resposta = await fetch(
                "/questoes/estudo/iniciar",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken": tokenCsrf
                    },

                    credentials: "same-origin"
                }
            );

            if (!resposta.ok) {
                throw new Error(
                    `Erro HTTP ${resposta.status}`
                );
            }

            const dados = await resposta.json();

            if (!dados.sucesso) {
                throw new Error(
                    dados.erro || "Não foi possível iniciar."
                );
            }

            duracaoAcumulada = Number(dados.duracao) || 0;

            pausado = Boolean(dados.pausado);

            ultimaAtividadeLocal = Date.now();

            if (pausado) {
                inicioContagemLocal = null;

                statusCronometro.textContent =
                    "Interaja com a página para retomar o cronômetro.";
            } else {
                inicioContagemLocal = Date.now();

                statusCronometro.textContent =
                    "Tempo de estudo sendo contabilizado.";
            }

            atualizarExibicao();

        } catch (erro) {
            console.error(
                "Erro ao iniciar cronômetro:",
                erro
            );

            statusCronometro.textContent =
                "Não foi possível iniciar o cronômetro. Recarregue a página.";
        }
    }

    function registrarAtividadeLocal() {
        if (encerrando) {
            return;
        }

        const agora = Date.now();

        ultimaAtividadeLocal = agora;

        if (pausado) {
            // Não retoma localmente até o servidor confirmar.
            enviarEvento("atividade");
            return;
        }

        if (
            agora - ultimaAtividadeEnviada >=
            INTERVALO_ATIVIDADE
        ) {
            ultimaAtividadeEnviada = agora;

            enviarEvento("atividade");
        }
    }

    function verificarInatividade() {
        if (encerrando || pausado) {
            return;
        }

        const agora = Date.now();

        if (
            agora - ultimaAtividadeLocal >=
            TEMPO_INATIVIDADE
        ) {
            // A exibição local deixa de avançar.
            // O heartbeat também reconciliará o estado no servidor.
            atualizarExibicao();

            enviarEvento("heartbeat");
        }
    }

    function finalizarAoSair() {
        if (encerrando) {
            return;
        }

        encerrando = true;

        statusCronometro.textContent =
            "Encerrando sessão de estudo...";

        const dados = new URLSearchParams();

        dados.append("csrf_token", tokenCsrf);

        // sendBeacon permite enviar a requisição durante a navegação.
        const enviado = navigator.sendBeacon(
            "/questoes/estudo/finalizar",
            dados
        );

        if (!enviado) {
            fetch("/questoes/estudo/finalizar", {
                method: "POST",

                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },

                body: dados.toString(),

                credentials: "same-origin",

                keepalive: true
            }).catch((erro) => {
                console.error(
                    "Não foi possível finalizar a sessão:",
                    erro
                );
            });
        }
    }

    // Inicia ou recupera a sessão ao entrar na página.
    iniciarCronometro();

    // Atualiza a exibição a cada segundo.
    setInterval(atualizarExibicao, 1000);

    // Confere o limite de inatividade.
    setInterval(
        verificarInatividade,
        1000
    );

    // Salva periodicamente o tempo acumulado no servidor.
    setInterval(() => {
        if (!encerrando) {
            enviarEvento("heartbeat");
        }
    }, INTERVALO_HEARTBEAT);

    // Eventos considerados interação do usuário.
    [
        "pointerdown",
        "keydown",
        "scroll",
        "touchstart"
    ].forEach((evento) => {
        document.addEventListener(
            evento,
            registrarAtividadeLocal,
            { passive: true }
        );
    });

    // Finaliza ao navegar por um link que saia da seção de questões.
    document.addEventListener("click", (evento) => {
        const link = evento.target.closest("a[href]");

        if (!link) {
            return;
        }

        if (
            evento.defaultPrevented ||
            evento.button !== 0 ||
            evento.ctrlKey ||
            evento.shiftKey ||
            evento.altKey ||
            evento.metaKey
        ) {
            return;
        }

        if (link.target && link.target !== "_self") {
            return;
        }

        const destino = new URL(
            link.href,
            window.location.href
        );

        if (destino.origin !== window.location.origin) {
            return;
        }

        if (!destino.pathname.startsWith("/questoes")) {
            finalizarAoSair();
        }
    });

    // Também considera formulários enviados para outras seções.
    document.addEventListener("submit", (evento) => {
        const formulario = evento.target;

        const destino = new URL(
            formulario.action || window.location.href,
            window.location.href
        );

        if (
            destino.origin === window.location.origin &&
            !destino.pathname.startsWith("/questoes")
        ) {
            finalizarAoSair();
        }
    });
});