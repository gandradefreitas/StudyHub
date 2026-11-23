const botaoMenu = document.getElementById("btn-menu");
const sidebar = document.getElementById("sidebar");

if (botaoMenu && sidebar && !document.body.classList.contains("sidebar-fixa")) {
    function mostrarMenu(aberto, devolverFoco = false) {
        sidebar.inert = !aberto;
        sidebar.classList.toggle("ativo", aberto);
        botaoMenu.setAttribute("aria-expanded", String(aberto));
        if (aberto) sidebar.querySelector("a")?.focus();
        if (devolverFoco) botaoMenu.focus();
    }

    mostrarMenu(false);
    botaoMenu.addEventListener("click", () => {
        mostrarMenu(!sidebar.classList.contains("ativo"));
    });
    document.addEventListener("click", evento => {
        if (!sidebar.contains(evento.target) && !botaoMenu.contains(evento.target)) {
            mostrarMenu(false);
        }
    });
    document.addEventListener("keydown", evento => {
        if (evento.key === "Escape" && sidebar.classList.contains("ativo") && !document.querySelector("dialog[open]")) {
            mostrarMenu(false, true);
        }
    });
}
