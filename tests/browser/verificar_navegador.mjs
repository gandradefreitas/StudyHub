import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { once } from "node:events";

const [python, chrome, repositorio] = process.argv.slice(2);
const servidor = spawn(python, [join(dirname(import.meta.filename), "servidor_navegador.py")], {
    cwd: repositorio,
    env: { ...process.env, PYTHONPATH: repositorio, PYTHONDONTWRITEBYTECODE: "1" },
    stdio: ["pipe", "pipe", "inherit"],
});
const servidorFim = once(servidor, "exit");
const perfil = await mkdtemp(join(tmpdir(), "studyhub-chrome-"));
let navegador;
let navegadorFim;
let ws;
const pausa = ms => new Promise(resolve => setTimeout(resolve, ms));

async function aguardar(ler, descricao) {
    for (let i = 0; i < 100; i++) {
        const resultado = await ler();
        if (resultado) return resultado;
        await pausa(100);
    }
    throw new Error("Tempo esgotado: " + descricao);
}

try {
    let saida = "";
    servidor.stdout.on("data", parte => { saida += parte; });
    const info = await aguardar(() => saida.includes("\n") && JSON.parse(saida.split("\n")[0]), "servidor");
    const url = `http://127.0.0.1:${info.porta}`;
    navegador = spawn(chrome, ["--headless", "--disable-gpu", "--no-first-run",
        "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0",
        `--user-data-dir=${perfil}`, "about:blank"], { stdio: "ignore" });
    navegadorFim = once(navegador, "exit");
    const porta = await aguardar(async () => {
        try { return (await readFile(join(perfil, "DevToolsActivePort"), "utf8")).split("\n")[0]; }
        catch { return null; }
    }, "Chrome");
    const alvos = await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json();
    ws = new WebSocket(alvos.find(alvo => alvo.type === "page").webSocketDebuggerUrl);
    await once(ws, "open");
    let numero = 0;
    const comandos = new Map();
    ws.addEventListener("message", evento => {
        const mensagem = JSON.parse(evento.data);
        const callback = comandos.get(mensagem.id);
        if (callback) {
            comandos.delete(mensagem.id);
            if (mensagem.error) callback.reject(new Error(mensagem.error.message));
            else callback.resolve(mensagem.result);
        }
    });
    function cdp(method, params = {}) {
        return new Promise((resolve, reject) => {
            const id = ++numero;
            comandos.set(id, { resolve, reject });
            ws.send(JSON.stringify({ id, method, params }));
        });
    }
    async function executar(expression) {
        const resultado = await cdp("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
        if (resultado.exceptionDetails) throw new Error(resultado.exceptionDetails.exception?.description ?? expression);
        return resultado.result.value;
    }
    async function abrir(path, seletor) {
        await cdp("Page.navigate", {url: url + path});
        await aguardar(() => executar(
            `location.pathname === ${JSON.stringify(path)} && document.readyState === 'complete' && !!document.querySelector(${JSON.stringify(seletor)})`,
        ).catch(() => false), path).catch(async erro => { throw new Error(erro.message + " (" + await executar("location.href + ' | ' + document.title") + ")"); });
    }
    async function tecla(key, code) {
        const params = {key, code: key, windowsVirtualKeyCode: code, nativeVirtualKeyCode: code};
        await cdp("Input.dispatchKeyEvent", {type: "keyDown", ...params, text: key === "Enter" ? "\r" : ""});
        await cdp("Input.dispatchKeyEvent", {type: "keyUp", ...params});
    }
    await cdp("Page.enable");
    await cdp("Network.enable");
    await cdp("Network.setBlockedURLs", {urls: ["https://www.googletagmanager.com/*", "https://*.google-analytics.com/*", "https://cdn.jsdelivr.net/*"]});
    assert.equal((await cdp("Network.setCookie", {name: "session", value: info.sessao, url, httpOnly: true})).success, true);

    await abrir("/dashboard", "#btn-menu");
    assert.equal(await executar("document.querySelector('#sidebar').inert"), true);
    await executar("document.querySelector('#btn-menu').focus()");
    await tecla("Enter", 13);
    assert.equal(await executar("document.querySelector('#btn-menu').getAttribute('aria-expanded')"), "true");
    assert.equal(await executar("document.activeElement.closest('#sidebar') !== null"), true);
    await tecla("Escape", 27);
    assert.equal(await executar("document.activeElement.id"), "btn-menu");

    const cor = () => executar("getComputedStyle(document.querySelector('.sh-atalhos a')).backgroundColor");
    await cdp("Emulation.setEmulatedMedia", {features: [{name: "prefers-color-scheme", value: "light"}]});
    const clara = await cor();
    await cdp("Emulation.setEmulatedMedia", {features: [{name: "prefers-color-scheme", value: "dark"}]});
    const escura = await cor();
    assert.notEqual(clara, escura);
    await executar("document.body.dataset.tema = 'claro'");
    assert.equal(await cor(), clara);
    await executar("document.body.dataset.tema = 'escuro'");
    assert.equal(await cor(), escura);
    console.log("Menu por teclado e temas claro, escuro e automático OK");

    await abrir("/tarefas", "#editor-tarefa");
    await executar("document.querySelector('[data-abrir-tarefa]').focus()");
    await tecla("Enter", 13);
    assert.equal(await executar("document.activeElement.id"), "descricao-editor-tarefa");
    await executar("document.activeElement.value = 'Criada no navegador'; document.querySelector('#formulario-editor-tarefa').requestSubmit()");
    await aguardar(() => executar("document.readyState === 'complete' && document.querySelector('[data-descricao]')?.dataset.descricao === 'Criada no navegador'").catch(() => false), "criação da tarefa");
    await executar("document.querySelector('[data-descricao]').focus()");
    await tecla("Enter", 13);
    assert.equal(await executar("document.activeElement.value"), "Criada no navegador");
    await executar("document.activeElement.value = 'Editada no navegador'; document.querySelector('#formulario-editor-tarefa').requestSubmit()");
    await aguardar(() => executar("document.readyState === 'complete' && document.querySelector('[data-descricao]')?.dataset.descricao === 'Editada no navegador'").catch(() => false), "edição da tarefa");
    await executar("document.querySelector('[data-descricao]').focus()");
    await tecla("Enter", 13);
    await tecla("Escape", 27);
    assert.equal(await executar("document.querySelector('#editor-tarefa').open"), false);
    console.log("Tarefas criadas e editadas na janela com CSRF e teclado OK");

    await abrir("/idiomas", ".sh-grafico-dia");
    assert.match(await executar("document.querySelector('.sh-grafico-dia').getAttribute('aria-label')"), /135 palavras/);
    await executar("document.querySelector('.idiomas-dados summary').focus()");
    await tecla("Enter", 13);
    assert.equal(await executar("document.querySelector('.idiomas-dados').open"), true);
    assert.equal(await executar("document.querySelector('.idiomas-dados tbody').textContent.includes('135')"), true);

    await abrir("/estatisticas", "#evolucao-tabela-dias");
    await aguardar(() => executar("document.querySelector('#evolucao-tabela-dias').rows.length >= 28"), "dados de evolução");
    await executar("document.querySelector('.sh-dados-evolucao summary').focus()");
    await tecla("Enter", 13);
    assert.equal(await executar("document.querySelector('.sh-dados-evolucao').open"), true);
    console.log("Idiomas e Estatísticas com dados acessíveis por teclado OK");

    await cdp("Emulation.setDeviceMetricsOverride", {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
    await abrir("/provas/historico", "#historico-simulados .tabela-wrapper");
    const medidas = await executar(`(() => {
        const tabela = document.querySelector("#historico-simulados .tabela-wrapper");
        return {largura: tabela.clientWidth, rolagem: tabela.scrollWidth, foco: tabela.tabIndex};
    })()`);
    assert.ok(medidas.rolagem > medidas.largura && medidas.foco === 0, JSON.stringify(medidas));
    console.log("Histórico móvel com tabela rolável e focável OK");
} finally {
    ws?.close();
    navegador?.kill();
    servidor.stdin.end();
    const [codigoServidor] = await servidorFim;
    if (navegadorFim) await navegadorFim;
    assert.equal(dirname(perfil), tmpdir(), "perfil criado dentro da pasta temporária");
    await rm(perfil, {recursive: true, force: true, maxRetries: 4, retryDelay: 150});
    assert.equal(codigoServidor, 0, "servidor de teste e limpeza");
}


