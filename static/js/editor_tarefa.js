const editorTarefa = document.querySelector('#editor-tarefa');
const formularioTarefa = document.querySelector('#formulario-editor-tarefa');
document.querySelectorAll('[data-abrir-tarefa]').forEach(link => {
    link.addEventListener('click', evento => {
        if (evento.ctrlKey || evento.metaKey || evento.shiftKey || evento.altKey) return;
        evento.preventDefault();
        formularioTarefa.action = link.href;
        formularioTarefa.elements.descricao.value = link.dataset.descricao ?? '';
        editorTarefa.querySelector('h2').textContent = 'descricao' in link.dataset ? 'Editar tarefa' : 'Nova tarefa';
        editorTarefa.showModal();
    });
});
document.querySelector('#cancelar-editor-tarefa').addEventListener('click', () => editorTarefa.close());
