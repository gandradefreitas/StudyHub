(() => {
    const dialogo = document.getElementById("parabens-nivel");
    if (!dialogo) return;

    const perfil = document.querySelector("[data-progresso-nivel]");
    const formatador = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
    const molduras = document.querySelector("[data-molduras-perfil]");
    const seletor = molduras?.querySelector("[data-escolher-moldura]");
    const aplicar = molduras?.querySelector("[data-equipar-perfil]");
    const conquista = dialogo.querySelector("[data-conquista-moldura]");
    const equiparAgora = conquista.querySelector("[data-equipar-conquista]");
    const mensagem = dialogo.querySelector("[data-mensagem-nivel]");
    let equipada = Number(seletor?.value ?? 0);
    let equipando = false;
    let consultando = false;
    let timer;

    function atualizarPerfil(dados) {
        if (!perfil) return;
        perfil.querySelector("[data-nivel-atual]").textContent = "Nível " + dados.nivel;
        perfil.querySelector("[data-nivel-proximo]").textContent = "Nível " + dados.proximo;
        const barra = perfil.querySelector("progress");
        barra.max = dados.necessario;
        barra.value = dados.progresso;
        perfil.querySelector("[data-nivel-exp]").textContent =
            formatador.format(dados.progresso / 10) + " / " +
            formatador.format(dados.necessario / 10) + " EXP";
    }

    function atualizarMolduras(dados) {
        if (!molduras) return;
        for (const opcao of seletor.options) {
            opcao.disabled = Number(opcao.value) > dados.nivel;
            opcao.hidden = opcao.disabled;
        }
        const meta = molduras.querySelector("[data-proxima-moldura]");
        const amostra = molduras.querySelector("[data-proxima-amostra]");
        const proxima = dados.proxima_moldura;
        amostra.hidden = proxima === null;
        amostra.dataset.avatarMoldura = proxima ?? 0;
        if (proxima === null) {
            meta.textContent = "Você conquistou todas as molduras.";
        } else {
            const nome = seletor.querySelector(`[value="${proxima}"]`).dataset.nome;
            const faltam = proxima - dados.nivel;
            const distancia = faltam === 1 ? "Falta 1 nível." : `Faltam ${faltam} níveis.`;
            meta.textContent = `Próxima moldura: ${nome} no nível ${proxima}. ${distancia}`;
        }
    }

    function atualizarBotaoPerfil() {
        if (aplicar) aplicar.disabled = equipando || Number(seletor.value) === equipada;
    }

    async function equipar(nivel, status) {
        if (equipando) return;
        equipando = true;
        atualizarBotaoPerfil();
        equiparAgora.disabled = true;
        if (seletor) seletor.disabled = true;
        status.textContent = "";
        try {
            const resposta = await fetch(dialogo.dataset.urlMoldura, {
                method: "POST",
                headers: {"X-CSRFToken": dialogo.dataset.csrf, "Content-Type": "application/json"},
                body: JSON.stringify({nivel}),
            });
            const dados = await resposta.json();
            if (!resposta.ok) throw new Error(dados.erro);
            equipada = dados.moldura_equipada;
            if (seletor) {
                seletor.value = equipada;
                document.querySelectorAll(".avatar[data-avatar-moldura]").forEach(avatar => {
                    avatar.dataset.avatarMoldura = equipada;
                });
            }
            status.textContent = equipada ? "Moldura equipada." : "Moldura removida.";
        } catch (erro) {
            status.textContent = erro.message === "Escolha uma moldura que você já conquistou."
                ? erro.message : "Não foi possível aplicar a moldura. Tente novamente.";
        } finally {
            equipando = false;
            if (seletor) seletor.disabled = false;
            atualizarBotaoPerfil();
            equiparAgora.disabled = equipada === Number(equiparAgora.dataset.nivel);
        }
    }

    function comemorar(dados) {
        const ultimas = dados.molduras_conquistadas;
        const nova = ultimas.at(-1);
        if (!nova && dialogo.open && !conquista.hidden) return;

        dialogo.querySelector("h2").textContent = "Parabéns por chegar ao nível " + dados.nivel + "!";
        mensagem.textContent = nova
            ? "Molduras conquistadas: " + ultimas.map(moldura => moldura.nome).join(", ") + "."
            : "Continue praticando e evoluindo no StudyHub.";
        if (ultimas.length === 1) mensagem.textContent = "Moldura conquistada: " + nova.nome + ".";
        conquista.hidden = !nova;
        window.clearTimeout(timer);
        if (nova) {
            conquista.querySelector("[data-moldura-conquistada]").dataset.avatarMoldura = nova.nivel;
            conquista.querySelector("[data-conquista-status]").textContent =
                equipada === nova.nivel ? "Moldura equipada." : "";
            equiparAgora.dataset.nivel = nova.nivel;
            equiparAgora.disabled = equipando || equipada === nova.nivel;
            equiparAgora.setAttribute("aria-label", "Equipar agora: " + nova.nome);
        }
        if (!dialogo.open) dialogo.showModal();
        if (!nova) timer = window.setTimeout(() => dialogo.close(), 3000);
    }

    seletor?.addEventListener("change", atualizarBotaoPerfil);
    aplicar?.addEventListener("click", () => {
        equipar(Number(seletor.value), molduras.querySelector("[data-moldura-status]"));
    });
    equiparAgora.addEventListener("click", () => {
        equipar(Number(equiparAgora.dataset.nivel), conquista.querySelector("[data-conquista-status]"));
    });
    conquista.querySelector("[data-fechar-conquista]").addEventListener("click", () => dialogo.close());

    async function atualizar() {
        if (consultando || document.hidden) return;
        consultando = true;
        try {
            const resposta = await fetch(dialogo.dataset.url, {
                method: "POST",
                headers: {"X-CSRFToken": dialogo.dataset.csrf},
                cache: "no-store",
            });
            if (!resposta.ok) return;
            const dados = await resposta.json();
            atualizarPerfil(dados);
            atualizarMolduras(dados);
            if (dados.celebrar) comemorar(dados);
        } catch {
            // A próxima consulta tenta novamente quando a conexão voltar.
        } finally {
            consultando = false;
        }
    }

    atualizar();
    window.setInterval(atualizar, 20000);
    document.addEventListener("visibilitychange", atualizar);
    document.addEventListener("studyhub:experiencia", atualizar);
})();
