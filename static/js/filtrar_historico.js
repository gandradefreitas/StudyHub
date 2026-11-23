const filtrosHistorico = document.querySelector('#filtro-historico');
if (filtrosHistorico) {
    filtrosHistorico.addEventListener('change', () => {
        const filtro = filtrosHistorico.value;
        let total = 0;
        document.querySelectorAll('[data-modalidade-historico]').forEach(linha => {
            linha.hidden = filtro !== 'todas' && linha.dataset.modalidadeHistorico !== filtro;
            if (!linha.hidden) total++;
        });
        const simulados = document.querySelector('#historico-simulados');
        if (simulados) simulados.hidden = !total;
        const redacoes = document.querySelector('#historico-redacoes');
        if (redacoes) {
            redacoes.hidden = !['todas', 'redacao'].includes(filtro);
            if (!redacoes.hidden) total += redacoes.querySelectorAll('tbody tr').length;
        }
        document.querySelector('#estado-filtro-historico').textContent =
            total ? '' : 'Nenhum registro neste filtro.';
    });
}
