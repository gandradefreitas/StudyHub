const botaoMenu = document.getElementById("btn-menu");
const sidebar = document.getElementById("sidebar");

if (botaoMenu && sidebar) {

    botaoMenu.addEventListener("click", (evento) => {
        evento.stopPropagation();
        sidebar.classList.toggle("ativo");
    });

    document.addEventListener("click", (evento) => {
        if (!sidebar.contains(evento.target)) {
            sidebar.classList.remove("ativo");
        }
    });

    sidebar.addEventListener("click", (evento) => {
        evento.stopPropagation();
    });

    const links = sidebar.querySelectorAll("a");

    links.forEach((link) => {
        link.addEventListener("click", () => {
            sidebar.classList.remove("ativo");
        });
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") {
            sidebar.classList.remove("ativo");
        }
    });

}