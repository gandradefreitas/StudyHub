document.addEventListener("DOMContentLoaded", () => {

    inicializarModalExcluirConta();

    inicializarModalLimparHistorico();

});


/* =========================================================
   MODAL — EXCLUIR CONTA
========================================================= */

function inicializarModalExcluirConta() {

    const botaoAbrir =
        document.getElementById(
            "botao-excluir-conta"
        );

    const botaoCancelar =
        document.getElementById(
            "botao-cancelar-exclusao"
        );

    const modal =
        document.getElementById(
            "modal-excluir-conta"
        );

    const campoSenha =
        document.getElementById(
            "senha-exclusao"
        );


    if (!botaoAbrir || !modal) {
        return;
    }


    /* Abrir */

    botaoAbrir.addEventListener(
        "click",
        () => {

            modal.hidden = false;


            if (campoSenha) {

                campoSenha.focus();

            }

        }
    );


    /* Cancelar */

    if (botaoCancelar) {

        botaoCancelar.addEventListener(
            "click",
            () => {

                fecharModalExcluirConta(
                    modal,
                    campoSenha
                );

            }
        );

    }


    /* Clicar no fundo do modal */

    modal.addEventListener(
        "click",
        (evento) => {

            if (evento.target === modal) {

                fecharModalExcluirConta(
                    modal,
                    campoSenha
                );

            }

        }
    );


    /* Tecla Escape */

    document.addEventListener(
        "keydown",
        (evento) => {

            if (
                evento.key === "Escape" &&
                !modal.hidden
            ) {

                fecharModalExcluirConta(
                    modal,
                    campoSenha
                );

            }

        }
    );

}


/* Fechar modal de exclusão */

function fecharModalExcluirConta(
    modal,
    campoSenha
) {

    modal.hidden = true;


    if (campoSenha) {

        campoSenha.value = "";

    }

}


/* =========================================================
   MODAL — LIMPAR HISTÓRICO
========================================================= */

function inicializarModalLimparHistorico() {

    const botaoAbrir =
        document.getElementById(
            "botao-limpar-historico"
        );

    const botaoCancelar =
        document.getElementById(
            "botao-cancelar-historico"
        );

    const modal =
        document.getElementById(
            "modal-limpar-historico"
        );


    if (!botaoAbrir || !modal) {
        return;
    }


    /* Abrir */

    botaoAbrir.addEventListener(
        "click",
        () => {

            modal.hidden = false;

        }
    );


    /* Cancelar */

    if (botaoCancelar) {

        botaoCancelar.addEventListener(
            "click",
            () => {

                fecharModal(
                    modal
                );

            }
        );

    }


    /* Clicar no fundo */

    modal.addEventListener(
        "click",
        (evento) => {

            if (evento.target === modal) {

                fecharModal(
                    modal
                );

            }

        }
    );


    /* Escape */

    document.addEventListener(
        "keydown",
        (evento) => {

            if (
                evento.key === "Escape" &&
                !modal.hidden
            ) {

                fecharModal(
                    modal
                );

            }

        }
    );

}


/* Fechar modal */

function fecharModal(modal) {

    modal.hidden = true;

}