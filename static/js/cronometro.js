document.addEventListener("DOMContentLoaded", () => {

    const cronometro =
        document.querySelector(
            "#cronometro-estudos, #cronometro-questoes"
        );


    if (!cronometro) {

        return;

    }


    const inicio =
        cronometro.dataset.inicio;


    /* =====================================================
       NENHUMA SESSÃO ATIVA
    ====================================================== */

    if (!inicio) {

        cronometro.textContent =
            "00:00:00";

        return;

    }


    const dataInicio =
        new Date(inicio);


    if (isNaN(dataInicio.getTime())) {

        console.error(
            "Data de início inválida:",
            inicio
        );

        return;

    }


    /* =====================================================
       ATUALIZAR CRONÔMETRO
    ====================================================== */

    function atualizarCronometro() {

        const agora =
            new Date();


        const diferenca =
            Math.floor(
                (agora - dataInicio) / 1000
            );


        const segundosTotais =
            Math.max(
                0,
                diferenca
            );


        const horas =
            Math.floor(
                segundosTotais / 3600
            );


        const minutos =
            Math.floor(
                (segundosTotais % 3600) / 60
            );


        const segundos =
            segundosTotais % 60;


        cronometro.textContent =

            String(horas).padStart(2, "0")
            + ":"
            +
            String(minutos).padStart(2, "0")
            + ":"
            +
            String(segundos).padStart(2, "0");

    }


    /* =====================================================
       PRIMEIRA ATUALIZAÇÃO
    ====================================================== */

    atualizarCronometro();


    /* =====================================================
       ATUALIZAR A CADA SEGUNDO
    ====================================================== */

    setInterval(
        atualizarCronometro,
        1000
    );

});