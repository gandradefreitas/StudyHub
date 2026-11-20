const dialogoExclusao = document.getElementById("confirmar-exclusao-tarefa");
let formularioExclusao = null;

for (const botao of document.querySelectorAll("[data-confirmar-exclusao]")) {
    botao.addEventListener("click", () => {
        formularioExclusao = botao.form;
        dialogoExclusao.returnValue = "";
        dialogoExclusao.showModal();
    });
}

dialogoExclusao.addEventListener("close", () => {
    const formulario = formularioExclusao;
    formularioExclusao = null;
    if (dialogoExclusao.returnValue === "excluir") {
        formulario?.requestSubmit();
    }
});
