const gatilhoPerfil = document.getElementById("abrir-perfil");
const janelaPerfil = document.getElementById("janela-perfil");

if (gatilhoPerfil && janelaPerfil) {
    const arquivo = document.getElementById("perfil-foto");
    const foto = document.getElementById("perfil-foto-preview");
    const inicial = document.getElementById("perfil-inicial");
    const status = document.getElementById("perfil-status");
    const srcAtual = foto.getAttribute("src");

    gatilhoPerfil.addEventListener("click", () => janelaPerfil.showModal());
    janelaPerfil.querySelectorAll(".perfil-fechar, .perfil-cancelar").forEach(botao => {
        botao.addEventListener("click", () => janelaPerfil.close());
    });
    janelaPerfil.addEventListener("close", () => {
        janelaPerfil.querySelector("form").reset();
        if (srcAtual) foto.src = srcAtual;
        else foto.removeAttribute("src");
        foto.hidden = !srcAtual;
        inicial.hidden = !!srcAtual;
        status.hidden = true;
        gatilhoPerfil.focus();
    });
    if (janelaPerfil.hasAttribute("data-reabrir")) janelaPerfil.showModal();

    arquivo.addEventListener("change", () => {
        const selecionado = arquivo.files[0];
        if (!selecionado) return;
        if (selecionado.size > 2 * 1024 * 1024) {
            arquivo.value = "";
            if (srcAtual) foto.src = srcAtual;
            else foto.removeAttribute("src");
            foto.hidden = !srcAtual;
            inicial.hidden = !!srcAtual;
            status.hidden = false;
            status.textContent = "Escolha uma foto de até 2 MB.";
            return;
        }
        const leitor = new FileReader();
        leitor.addEventListener("load", () => {
            if (arquivo.files[0] !== selecionado) return;
            foto.src = leitor.result;
            foto.hidden = false;
            inicial.hidden = true;
            status.hidden = false;
            status.textContent = "Nova foto selecionada. Salve as alterações para aplicar.";
        });
        leitor.readAsDataURL(selecionado);
    });
}
