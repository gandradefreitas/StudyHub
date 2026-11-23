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
    const intervaloSincronizacao = 3000;
    const prazoResposta = 4500;
    const renovarDepois = 45 * 60 * 1000;
    let tokenAtualizadoEm = Date.now();
    let restante = Number(form.dataset.restante);
    let inicio = null;
    let revisao = Number(form.dataset.revisao);
    let pausaEmCurso = null;
    let pausado = document.hidden;
    let ocupado = false;
    let enviando = false;
    let substituida = false;
    let atualizacaoPendente = false;
    let terminou = false;

    function tempoRestante() {
        return Math.max(0, restante - (inicio === null ? 0 : (performance.now() - inicio) / 1000));
    }

    function bloquearEdicao(mensagem) {
        campos.forEach(campo => { campo.readOnly = true; });
        botao.disabled = true;
        estado.textContent = mensagem;
    }

    function congelar(mensagem) {
        restante = tempoRestante();
        inicio = null;
        bloquearEdicao(mensagem);
    }

    function mostrar() {
        const segundos = Math.ceil(tempoRestante());
        const minutos = String(Math.floor(segundos / 60)).padStart(2, '0');
        const unidade = String(segundos % 60).padStart(2, '0');
        cronometro.textContent = `${minutos}:${unidade}`;
        if (segundos === 0 && inicio !== null && !terminou) {
            bloquearEdicao('Confirmando o término do tempo…');
        }
    }

    function dados(acao) {
        const corpo = new FormData(form);
        corpo.set('acao', acao);
        corpo.set('revisao', String(++revisao));
        return corpo;
    }

    async function requisitar(opcoes) {
        const controle = new AbortController();
        const expirar = setTimeout(() => controle.abort(), prazoResposta);
        try {
            return await fetch(form.dataset.registrarTempo, { ...opcoes, signal: controle.signal });
        } finally {
            clearTimeout(expirar);
        }
    }

    function enviar(corpo, keepalive = false) {
        return requisitar({ method: 'POST', body: corpo, keepalive });
    }

    function atualizarToken(token) {
        if (!token) return;
        form.elements.csrf_token.value = token;
        descartar.elements.csrf_token.value = token;
        tokenAtualizadoEm = Date.now();
    }

    async function renovarToken() {
        const resposta = await requisitar({ method: 'GET', cache: 'no-store' });
        if (!resposta.ok) throw new Error('Falha ao renovar o formulário');
        const dados = await resposta.json();
        if (!dados.csrf_token) throw new Error('Formulário não renovado');
        atualizarToken(dados.csrf_token);
    }

    function pausar(aoSair = false) {
        if (pausado || enviando || substituida || terminou) return;
        pausado = true;
        congelar('Cronômetro pausado.');
        mostrar();
        const corpo = dados('pausar');
        if (aoSair && navigator.sendBeacon?.(form.dataset.registrarTempo, corpo)) return;
        pausaEmCurso = enviar(corpo, true).catch(() => {}).finally(() => {
            pausaEmCurso = null;
            sincronizar();
        });
    }

    async function sincronizar() {
        if (document.hidden || pausado || enviando || substituida || terminou || pausaEmCurso) return;
        if (ocupado) {
            atualizacaoPendente = true;
            return;
        }
        ocupado = true;
        let versao = revisao;
        try {
            if (Date.now() - tokenAtualizadoEm > renovarDepois) await renovarToken();
            if (versao !== revisao || pausado || enviando) return;
            const corpo = dados('ativo');
            versao = revisao;
            const resposta = await enviar(corpo);
            if (versao !== revisao || pausado || enviando) return;
            if (resposta.status === 409) {
                substituida = true;
                congelar('Tentativa aberta em outra aba. Recarregue para continuar aqui.');
                descartar.hidden = true;
                return;
            }
            if (resposta.status === 400 && Date.now() - tokenAtualizadoEm > intervaloSincronizacao) {
                await renovarToken();
                atualizacaoPendente = true;
                return;
            }
            if (!resposta.ok) throw new Error('Falha ao salvar');
            const dadosSalvos = await resposta.json();
            if (versao !== revisao || pausado || enviando) return;
            atualizarToken(dadosSalvos.csrf_token);
            restante = dadosSalvos.restante;
            terminou = restante <= 0;
            if (terminou) {
                descartar.hidden = false;
                texto.value = dadosSalvos.texto;
                if (titulo) titulo.value = dadosSalvos.titulo;
            }
            inicio = terminou ? null : performance.now();
            campos.forEach(campo => { campo.readOnly = terminou; });
            botao.disabled = false;
            estado.textContent = terminou ? 'Tempo encerrado. Envie o texto que ficou salvo.' : 'Rascunho salvo.';
        } catch {
            if (versao === revisao && !pausado && !enviando) {
                congelar('Conexão indisponível. Aguarde para continuar.');
            }
        } finally {
            ocupado = false;
            mostrar();
            if (atualizacaoPendente) {
                atualizacaoPendente = false;
                sincronizar();
            }
        }
    }

    function retomar() {
        pausado = false;
        sincronizar();
    }

    async function concluir(evento) {
        if (enviando || substituida || pausado) {
            evento.preventDefault();
            return;
        }
        enviando = true;
        if (Date.now() - tokenAtualizadoEm <= renovarDepois) return;
        evento.preventDefault();
        try {
            await renovarToken();
            evento.target.submit();
        } catch {
            enviando = false;
            estado.textContent = 'Não foi possível renovar o formulário. Tente enviar novamente.';
        }
    }

    form.addEventListener('submit', evento => {
        if (substituida || pausado || (!terminou && (inicio === null || tempoRestante() === 0))) {
            evento.preventDefault();
            return;
        }
        if (!texto.value.trim() || (titulo && !titulo.value.trim())) {
            evento.preventDefault();
            estado.textContent = 'Preencha a redação e, quando solicitado, o título.';
            return;
        }
        concluir(evento);
    });
    descartar.addEventListener('submit', concluir);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) pausar();
        else retomar();
    });
    window.addEventListener('pagehide', () => pausar(true));
    window.addEventListener('pageshow', evento => {
        if (evento.persisted) retomar();
    });
    window.addEventListener('offline', () => {
        if (!pausado && !terminou && !substituida) {
            ++revisao;
            congelar('Conexão indisponível. Aguarde para continuar.');
        }
    });
    window.addEventListener('online', retomar);
    setInterval(sincronizar, intervaloSincronizacao);
    setInterval(mostrar, 250);
    mostrar();
    sincronizar();
})();
