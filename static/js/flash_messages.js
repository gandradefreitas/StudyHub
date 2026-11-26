document.querySelectorAll(".mensagens-flash").forEach(grupo => {
    const mensagens = grupo.querySelectorAll(".flash-mensagem");
    if (!mensagens.length) return;

    window.setTimeout(() => {
        mensagens.forEach(mensagem => mensagem.classList.add("flash-saindo"));
    }, 2700);

    window.setTimeout(() => grupo.remove(), 3000);
});
