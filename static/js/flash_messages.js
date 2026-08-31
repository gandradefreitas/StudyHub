document.addEventListener("DOMContentLoaded", () => {

    const mensagens =
        document.querySelectorAll(".flash-mensagem");


    mensagens.forEach((mensagem) => {

        setTimeout(() => {

            mensagem.classList.add("flash-saindo");


            setTimeout(() => {

                mensagem.remove();

            }, 300);

        }, 3000);

    });

});