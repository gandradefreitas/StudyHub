
const grafico =
    document.getElementById("grafico");


if (grafico) {

    const destino =
        Number(
            grafico.dataset.porcentagem
        );


    let atual = 0;


    const valor =
        grafico.querySelector(
            ".valor-desempenho"
        );


    // =====================================================
    // RESULTADO 0%
    // =====================================================

    if (destino <= 0) {

        grafico.style.setProperty(
            "--porcentagem",
            0
        );


        if (valor) {

            valor.textContent = "0%";

        }

    } else {

        // =================================================
        // ANIMAÇÃO
        // =================================================

        const animacao =
            setInterval(() => {

                atual = Math.min(
                    atual + 0.5,
                    destino
                );


                grafico.style.setProperty(
                    "--porcentagem",
                    atual
                );


                if (valor) {

                    valor.textContent =
                        `${atual.toFixed(2)}%`;

                }


                if (atual >= destino) {

                    clearInterval(animacao);

                }

            }, 15);

    }

}

