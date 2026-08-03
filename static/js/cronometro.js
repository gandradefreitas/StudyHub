const cronometro = document.getElementById("cronometro");

if (cronometro) {

    const inicio = new Date(cronometro.dataset.inicio);

    function atualizarCronometro() {

        const agora = new Date();

        const diferenca = Math.floor((agora - inicio) / 1000);

        const horas = Math.floor(diferenca / 3600);
        const minutos = Math.floor((diferenca % 3600) / 60);
        const segundos = diferenca % 60;

        cronometro.textContent =
            String(horas).padStart(2, "0") + ":" +
            String(minutos).padStart(2, "0") + ":" +
            String(segundos).padStart(2, "0");
    }

    atualizarCronometro();

    setInterval(atualizarCronometro, 1000);
}