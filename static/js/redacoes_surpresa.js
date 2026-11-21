(() => {
    const form = document.querySelector('[data-registrar-tempo]');
    if (!form) return;

    const descartar = document.querySelector('#descartar-surpresa');
    const cronometro = document.querySelector('#cronometro-redacao');
    const estado = document.querySelector('#estado-cronometro');
    const texto = form.elements.texto;
    const titulo = form.elements.titulo;
    const botao = form.querySelector('button[type="submit"]');
    const campos = titulo ? [texto, titulo] : [texto];
    let restante = Number(form.dataset.restante);
    let inicio = null;
    let revisao = Number(form.dataset.revisao);
    let ocupado = false;
    let enviando = false;
    let substituida = false;
    let atualizacaoPendente = false;
    let terminou = false;

    function tempoRestante() {
        return Math.max(0, restante - (inicio === null ? 0 : (performance.now() - inicio) / 1000));
    }

    function mostrar() {
        const segundos = Math.ceil(tempoRestante());
        const minutos = String(Math.floor(segundos / 60)).padStart(2, '0');
        const unidade = String(segundos % 60).padStart(2, '0');
        cronometro.textContent = `${minutos}:${unidade}`;
        if (!substituida && segundos === 0) {
            campos.forEach(campo => { campo.readOnly = true; });
            estado.textContent = 'Tempo encerrado. Envie o texto que ficou salvo.';
        }
    }

    function dados(acao) {
        const corpo = new FormData(form);
        corpo.set('acao', acao);
        corpo.set('revisao', String(++revisao));
        return corpo;
    }

    function pausar() {
        if (enviando || substituida || terminou) return;
        restante = tempoRestante();
        inicio = null;
        navigator.sendBeacon(form.dataset.registrarTempo, dados('pausar'));
        estado.textContent = 'Cronômetro pausado.';
        mostrar();
    }

    async function sincronizar() {
        if (document.hidden || enviando || substituida || terminou) return;
        if (ocupado) {
            atualizacaoPendente = true;
            return;
        }
        ocupado = true;
        const corpo = dados('ativo');
        const versao = revisao;
        try {
            const resposta = await fetch(form.dataset.registrarTempo, { method: 'POST', body: corpo });
            if (versao !== revisao) return;
            if (resposta.status === 409) {
                substituida = true;
                inicio = null;
                campos.forEach(campo => { campo.readOnly = true; });
                botao.disabled = true;
                descartar.hidden = true;
                estado.textContent = 'Tentativa aberta em outra aba. Recarregue para continuar aqui.';
                return;
            }
            if (!resposta.ok) throw new Error('Falha ao salvar');
            const dadosSalvos = await resposta.json();
            if (versao !== revisao) return;
            restante = dadosSalvos.restante;
            if (restante <= 0) {
                terminou = true;
                descartar.hidden = false;
                texto.value = dadosSalvos.texto;
                if (titulo) titulo.value = dadosSalvos.titulo;
            }
            inicio = restante > 0 ? performance.now() : null;
            campos.forEach(campo => { campo.readOnly = restante <= 0; });
            botao.disabled = false;
            estado.textContent = 'Rascunho salvo.';
        } catch {
            if (versao === revisao) estado.textContent = 'Reconectando. Mantenha esta página aberta para salvar o rascunho.';
        } finally {
            ocupado = false;
            mostrar();
            if (atualizacaoPendente) {
                atualizacaoPendente = false;
                sincronizar();
            }
        }
    }

    form.addEventListener('submit', evento => {
        if (!texto.value.trim() || (titulo && !titulo.value.trim())) {
            evento.preventDefault();
            estado.textContent = 'Preencha a redação e, quando solicitado, o título.';
            return;
        }
        enviando = true;
    });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) pausar();
        else sincronizar();
    });
    window.addEventListener('pagehide', pausar);
    window.addEventListener('pageshow', evento => {
        if (evento.persisted) sincronizar();
    });
    setInterval(sincronizar, 3000);
    setInterval(mostrar, 250);
    mostrar();
    sincronizar();
})();
