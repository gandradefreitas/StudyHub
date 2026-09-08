document.addEventListener("DOMContentLoaded", () => {

    const cronometro = document.querySelector(
        "#cronometro-estudos, #cronometro-questoes"
    );

    if (!cronometro) {
        return;
    }

    const valorInicio = cronometro.dataset.inicio;

    if (!valorInicio) {
        cronometro.textContent = "00:00:00";
        return;
    }

    const inicio = Date.parse(
        valorInicio.replace(" ", "T") + "Z"
    );

    if (!Number.isFinite(inicio)) {

        console.error(
            "Data de início inválida:",
            valorInicio
        );

        return;
    }

    function atualizarCronometro() {

        const diferenca = Math.max(
            0,
            Math.floor(
                (Date.now() - inicio) / 1000
            )
        );

        const horas = Math.floor(
            diferenca / 3600
        );

        const minutos = Math.floor(
            (diferenca % 3600) / 60
        );

        const segundos = diferenca % 60;

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