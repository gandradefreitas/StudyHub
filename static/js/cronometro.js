document.addEventListener("DOMContentLoaded", () => {

    const cronometro = document.querySelector(
        "#cronometro-estudos, #cronometro-questoes"
    );

    if (!cronometro) {
        return;
    }

    const inicio = Number(cronometro.dataset.inicio);

    if (!Number.isFinite(inicio)) {

        console.error(
            "Timestamp de início inválido:",
            cronometro.dataset.inicio
        );

        return;
    }

    function atualizarCronometro() {

        const agora = Date.now();

        const diferenca = Math.floor(
            (agora - inicio) / 1000
        );

        const segundosTotais = Math.max(
            0,
            diferenca
        );

        const horas = Math.floor(
            segundosTotais / 3600
        );

        const minutos = Math.floor(
            (segundosTotais % 3600) / 60
        );

        const segundos = segundosTotais % 60;

        cronometro.textContent =
            String(horas).padStart(2, "0")
            + ":"
            + String(minutos).padStart(2, "0")
            + ":"
            + String(segundos).padStart(2, "0");
    }

    atualizarCronometro();

    setInterval(
        atualizarCronometro,
        1000
    );

});