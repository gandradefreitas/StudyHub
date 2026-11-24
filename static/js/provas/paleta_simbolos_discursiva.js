document.addEventListener("DOMContentLoaded", () => {
    const paleta = document.getElementById("paleta-simbolos-discursiva");
    const formulario = document.getElementById("form-prova-discursiva");
    const busca = document.getElementById("buscar-simbolo-discursivo");
    const status = document.getElementById("status-paleta-simbolos");

    if (!paleta || !formulario) {
        return;
    }

    let campoAtivo = null;

    function normalizar(valor) {
        return valor
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLocaleLowerCase("pt-BR");
    }

    function filtrarSimbolos() {
        if (!busca) {
            return;
        }

        const termo = normalizar(busca.value.trim());

        paleta.querySelectorAll(".paleta-categoria").forEach(categoria => {
            let possuiResultado = false;

            categoria.querySelectorAll(".paleta-simbolo").forEach(botao => {
                const conteudoBusca = normalizar(
                    `${botao.dataset.pesquisa || ""} ${botao.dataset.inserir || ""}`
                );
                const corresponde = !termo || conteudoBusca.includes(termo);
                botao.hidden = !corresponde;
                possuiResultado = possuiResultado || corresponde;
            });

            categoria.hidden = !possuiResultado;
        });
    }

    function inserirSimbolo(botao) {
        const campos = formulario.querySelectorAll("textarea[name^='resposta_']");
        const campo = campoAtivo || campos[0];
        const simbolo = botao.dataset.inserir || "";

        if (!campo || !simbolo) {
            if (status) {
                status.textContent = "Não há campo de resposta disponível.";
            }
            return;
        }

        const inicio = campo.selectionStart ?? campo.value.length;
        const fim = campo.selectionEnd ?? inicio;
        const novoTamanho = campo.value.length - (fim - inicio) + simbolo.length;

        if (novoTamanho > campo.maxLength) {
            if (status) {
                status.textContent = "O limite de caracteres da resposta seria ultrapassado.";
            }
            campo.focus();
            return;
        }

        campo.setRangeText(simbolo, inicio, fim, "end");
        const deslocamento = Number(botao.dataset.deslocamentoCursor || 0);
        const posicaoCursor = Math.max(
            inicio,
            Math.min(inicio + simbolo.length + deslocamento, campo.value.length)
        );
        if (window.matchMedia("(max-width: 640px)").matches) paleta.open = false;
        campo.focus();
        campo.setSelectionRange(posicaoCursor, posicaoCursor);
        campo.dispatchEvent(new Event("input", { bubbles: true }));
        campoAtivo = campo;

        if (status) {
            status.textContent = `${simbolo} inserido na resposta da questão.`;
        }
    }

    formulario.addEventListener("focusin", evento => {
        if (evento.target.matches("textarea[name^='resposta_']")) {
            campoAtivo = evento.target;
        }
    });

    paleta.addEventListener("click", evento => {
        const botao = evento.target.closest(".paleta-simbolo");
        if (botao) {
            inserirSimbolo(botao);
        }
    });

    if (busca) {
        busca.addEventListener("input", filtrarSimbolos);
    }
});
