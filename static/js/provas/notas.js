const numeroNota = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
});

for (const cartao of document.querySelectorAll("[data-notas-enem]")) {
    const redacao = cartao.querySelector("[data-redacao]");
    const media = cartao.querySelector("[data-media]");
    const setores = cartao.querySelectorAll("[data-notas-dia]");

    function atualizarMedia() {
        const faixas = [];
        for (const setor of setores) {
            const seletor = setor.querySelector("[data-selecionar-tentativa]");
            for (const tentativa of setor.querySelectorAll("[data-tentativa]")) {
                tentativa.hidden = tentativa.dataset.tentativa !== seletor.value;
                if (!tentativa.hidden) {
                    for (const area of tentativa.querySelectorAll("[data-faixa]")) {
                        faixas.push(JSON.parse(area.dataset.faixa));
                    }
                }
            }
        }

        if (faixas.length !== 4) {
            media.textContent = "Selecione tentativas com notas nas quatro áreas.";
            return;
        }
        if (redacao.validity.badInput || !redacao.checkValidity()) {
            media.textContent = "Digite uma nota de redação entre 0 e 1000.";
            return;
        }
        if (redacao.value === "") {
            media.textContent = "Digite a nota da redação.";
            return;
        }

        const totais = [redacao.valueAsNumber, redacao.valueAsNumber, redacao.valueAsNumber];
        for (const faixa of faixas) {
            faixa.forEach((nota, indice) => { totais[indice] += nota; });
        }
        const [minima, esperada, maxima] = totais.map(nota => numeroNota.format(nota / 5));
        media.textContent = `${esperada} · Faixa ${minima}–${maxima}`;
    }

    cartao.addEventListener("change", atualizarMedia);
    redacao.addEventListener("input", atualizarMedia);
    atualizarMedia();
}
