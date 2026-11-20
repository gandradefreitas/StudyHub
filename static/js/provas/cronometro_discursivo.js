document.addEventListener("DOMContentLoaded", () => {
    const cronometro = document.getElementById(
        "cronometro-prova-discursiva"
    );
    const tempoExibido = document.getElementById(
        "tempo-restante-discursiva"
    );
    const formulario = document.getElementById(
        "form-prova-discursiva"
    );
    const botaoFinalizar = document.getElementById(
        "botao-finalizar-prova-discursiva"
    );
    const statusSalvamento = document.getElementById(
        "status-salvamento-prova"
    );
    const modalFinalizacao = document.getElementById(
        "modal-finalizacao-prova"
    );
    const botaoCancelarFinalizacao = document.getElementById(
        "cancelar-finalizacao-prova"
    );
    const botaoConfirmarFinalizacao = document.getElementById(
        "confirmar-finalizacao-prova"
    );
    const avisoTempo = document.getElementById(
        "aviso-tempo-esgotado"
    );

    if (!cronometro || !tempoExibido || !formulario || !botaoFinalizar) {
        return;
    }

    const segundosIniciais = Number(
        cronometro.dataset.segundosRestantes
    );
    const prazoFinal = Date.now() + Math.max(0, segundosIniciais) * 1000;
    let intervalo;
    let finalizacaoAutomatica = false;
    let finalizacaoSolicitada = false;
    let salvandoAntesDeFinalizar = false;
    let salvamentoConfirmado = false;
    let confirmacaoAceita = false;

    function formatarTempo(segundos) {
        const horas = Math.floor(segundos / 3600);
        const minutos = Math.floor((segundos % 3600) / 60);
        const segundosRestantes = segundos % 60;

        return [horas, minutos, segundosRestantes]
            .map(valor => String(valor).padStart(2, "0"))
            .join(":");
    }

    function finalizarAoAcabarTempo() {
        if (finalizacaoSolicitada) {
            return;
        }

        finalizacaoSolicitada = true;
        finalizacaoAutomatica = true;
        if (modalFinalizacao && modalFinalizacao.open) {
            modalFinalizacao.close();
        }
        window.clearInterval(intervalo);
        tempoExibido.textContent = "00:00:00";
        cronometro.classList.add("tempo-esgotado");

        if (avisoTempo) {
            avisoTempo.hidden = false;
        }

        if (typeof formulario.requestSubmit === "function") {
            formulario.requestSubmit(botaoFinalizar);
            return;
        }

        formulario.action = botaoFinalizar.formAction;
        formulario.submit();
    }

    function atualizarCronometro() {
        const segundos = Math.max(
            0,
            Math.ceil((prazoFinal - Date.now()) / 1000)
        );

        tempoExibido.textContent = formatarTempo(segundos);

        if (segundos === 0) {
            finalizarAoAcabarTempo();
        }
    }

    formulario.addEventListener("submit", evento => {
        if (evento.submitter !== botaoFinalizar) {
            return;
        }

        if (salvamentoConfirmado) {
            salvamentoConfirmado = false;
            botaoFinalizar.disabled = true;
            return;
        }

        if (!finalizacaoAutomatica && !confirmacaoAceita) {
            evento.preventDefault();
            if (modalFinalizacao && !modalFinalizacao.open) {
                modalFinalizacao.showModal();
            }
            return;
        }
        confirmacaoAceita = false;

        evento.preventDefault();
        if (salvandoAntesDeFinalizar) {
            return;
        }

        salvandoAntesDeFinalizar = true;
        botaoFinalizar.disabled = true;
        if (statusSalvamento) {
            statusSalvamento.hidden = false;
            statusSalvamento.textContent = finalizacaoAutomatica
                ? "Salvando suas respostas antes de finalizar automaticamente..."
                : "Salvando suas respostas antes de finalizar...";
        }

        fetch(formulario.action, {
            method: "POST",
            body: new FormData(formulario),
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
            .then(async resposta => {
                if (!resposta.ok) {
                    throw new Error("O servidor não confirmou o salvamento.");
                }

                const dados = await resposta.json();
                if (dados.status !== "ok") {
                    throw new Error("O servidor não confirmou o salvamento.");
                }
            })
            .then(() => {
                salvandoAntesDeFinalizar = false;
                salvamentoConfirmado = true;
                botaoFinalizar.disabled = false;
                formulario.requestSubmit(botaoFinalizar);
            })
            .catch(erro => {
                console.error("Não foi possível salvar antes de finalizar:", erro);
                salvandoAntesDeFinalizar = false;
                botaoFinalizar.disabled = false;
                if (statusSalvamento) {
                    statusSalvamento.hidden = false;
                    statusSalvamento.textContent =
                        "Não foi possível salvar as respostas. " +
                        "A prova continua aberta; tente salvar ou finalizar novamente.";
                }
                if (avisoTempo && finalizacaoAutomatica) {
                    avisoTempo.textContent =
                        "O tempo terminou, mas o salvamento falhou. " +
                        "Verifique sua conexão e tente finalizar novamente.";
                }
            });
    });

    if (botaoCancelarFinalizacao && modalFinalizacao) {
        botaoCancelarFinalizacao.addEventListener("click", () => {
            modalFinalizacao.close();
            botaoFinalizar.focus();
        });
    }

    if (botaoConfirmarFinalizacao && modalFinalizacao) {
        botaoConfirmarFinalizacao.addEventListener("click", () => {
            confirmacaoAceita = true;
            modalFinalizacao.close();
            formulario.requestSubmit(botaoFinalizar);
        });
    }

    atualizarCronometro();
    if (!finalizacaoSolicitada) {
        intervalo = window.setInterval(atualizarCronometro, 1000);
    }
});
