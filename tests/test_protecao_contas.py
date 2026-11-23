from concurrent.futures import ThreadPoolExecutor
import json
import re
from uuid import uuid4

from flask import Flask, request
from database.conexao import conectar
from security.limite_login import LIMITE_TENTATIVAS, limpar_tentativas, reservar_tentativa
from security.respostas import configurar_protecao_http
from services.provas_service import obter_prova
from tests.app_de_teste import app


def identificar_tentativa(pagina):
    return re.search(r'id: "([0-9a-f-]{36})"', pagina.get_data(as_text=True))[1]


def test_reserva_de_login_limita_concorrencia_e_expira():
    chave = f"teste-limite-{uuid4().hex}"
    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            reservas = list(executor.map(reservar_tentativa, [chave] * 8))
        assert sum(reservas) == LIMITE_TENTATIVAS
        assert not reservar_tentativa(chave)
        with conectar() as conexao:
            conexao.execute("""
                UPDATE tentativas_login
                SET primeira_tentativa = CURRENT_TIMESTAMP - INTERVAL '11 minutes',
                    bloqueado_ate = CURRENT_TIMESTAMP - INTERVAL '1 minute'
                WHERE chave = %s
            """, (chave,))
        assert reservar_tentativa(chave)
        with conectar() as conexao:
            registro = conexao.execute("""
                SELECT tentativas, bloqueado_ate FROM tentativas_login WHERE chave = %s
            """, (chave,)).fetchone()
        assert registro == {"tentativas": 1, "bloqueado_ate": None}
    finally:
        limpar_tentativas(chave)


def test_rascunho_objetivo_reabre_tentativa_e_separa_contas(dados_discursivos, monkeypatch):
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    usuario, outro = dados_discursivos["usuarios"]
    prova_id = 3
    prova = obter_prova(prova_id)
    try:
        with app.test_client() as cliente:
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = usuario
            pagina = cliente.get(f"/provas/{prova_id}")
            questoes = json.loads(re.search(
                r"const questoes = (.+?);\n", pagina.get_data(as_text=True)
            )[1])
            assert len(questoes) == len(prova.questoes)
            assert all("resposta" not in questao and "comentario" not in questao for questao in questoes)
            primeira = identificar_tentativa(pagina)
            assert primeira == identificar_tentativa(cliente.get(f"/provas/{prova_id}"))
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = outro
            segunda = identificar_tentativa(cliente.get(f"/provas/{prova_id}"))
            assert primeira != segunda
            envio = {"prova_id": prova_id, "tentativa_id": primeira, "respostas": {},
                     "questoes": [{"numero": q.numero} for q in prova.questoes]}
            assert cliente.post("/provas/resultado", json=envio).status_code == 409
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = usuario
            assert cliente.post("/provas/resultado", json=envio).status_code == 200
            assert cliente.post("/provas/resultado", json=envio).status_code == 409
            nova = identificar_tentativa(cliente.get(f"/provas/{prova_id}"))
            assert nova != primeira
        with conectar() as conexao:
            resultado = conexao.execute("""
                SELECT COUNT(*) AS total FROM resultados_provas WHERE usuario_id = %s
            """, (usuario,)).fetchone()
        assert resultado["total"] == 1
    finally:
        with conectar() as conexao:
            conexao.execute("DELETE FROM resultados_provas WHERE usuario_id = %s", (usuario,))


def test_csp_de_autenticacao_usa_nonce_distinto_por_resposta():
    with app.test_client() as cliente:
        respostas = [cliente.get("/login"), cliente.get("/login")]
    nonces = []
    for resposta in respostas:
        diretiva = resposta.headers["Content-Security-Policy"].split("script-src ", 1)[1].split(";", 1)[0]
        nonce = re.search(r"'nonce-([^']+)'", diretiva)[1]
        assert "'unsafe-inline'" not in diretiva
        assert f'<script nonce="{nonce}">' in resposta.get_data(as_text=True)
        nonces.append(nonce)
    assert nonces[0] != nonces[1]


def test_https_do_proxy_exige_opt_in(monkeypatch):
    for opcao in ("0", "1"):
        monkeypatch.setenv("STUDYHUB_PROXY_HTTPS", opcao)
        local = Flask(__name__)
        local.add_url_rule("/", view_func=lambda: request.remote_addr)
        configurar_protecao_http(local)
        resposta = local.test_client().get("/", headers={
            "X-Forwarded-Proto": "https",
            "X-Forwarded-For": "192.0.2.1",
        })
        assert resposta.get_data(as_text=True) == "127.0.0.1"
        assert ("Strict-Transport-Security" in resposta.headers) == (opcao == "1")



def test_senha_ausente_invalida_ou_longa_nao_interrompe_autenticacao():
    from security.hash import gerar_hash, verificar_senha
    from security.validacoes import validar_senha

    senha = "Senha!Valida123"
    assert verificar_senha(senha, gerar_hash(senha))
    assert not verificar_senha(senha, None)
    assert not verificar_senha(senha, "hash-invalido")
    assert not validar_senha("Áé" * 30 + "1!")[0]
