window.avisoStudyHub = function (mensagem, aoFechar) {
    const janela = document.createElement('dialog');
    janela.className = 'studyhub-aviso';
    janela.setAttribute('aria-label', 'Aviso do StudyHub');
    const titulo = document.createElement('h2');
    titulo.textContent = 'Aviso do StudyHub';
    const texto = document.createElement('p');
    texto.textContent = mensagem;
    const form = document.createElement('form');
    form.method = 'dialog';
    const botao = document.createElement('button');
    botao.textContent = 'OK';
    botao.autofocus = true;
    form.append(botao);
    janela.append(titulo, texto, form);
    document.body.append(janela);
    janela.addEventListener('close', () => {
        janela.remove();
        aoFechar?.();
    }, { once: true });
    janela.showModal();
    if (aoFechar) {
        const limite = window.setTimeout(() => janela.close(), 5000);
        janela.addEventListener('close', () => window.clearTimeout(limite), { once: true });
    }
};
