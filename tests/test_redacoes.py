from concurrent.futures import ThreadPoolExecutor
import re

import pytest

import worker_correcao_discursiva as worker
from database.conexao import conectar
from database.fila_redacoes_repository import encerrar_redacao, reivindicar_redacao
from database.dados_repository import limpar_historico
from services.redacoes_service import estimar_notas
from tests.app_de_teste import app


def preparar_envio(cliente, caminho, **campos):
    pagina = cliente.get(caminho).get_data(as_text=True)
    chave = re.search(r'name="chave_envio" value="([^"]+)"', pagina)[1]
    return {"chave_envio": chave, **campos}


def processar_envio(caminho):
    envio_id = int(caminho.rsplit("/", 1)[-1])
    envio = reivindicar_redacao(envio_id)
    assert envio
    worker.processar_redacao(envio)



@pytest.mark.parametrize("resposta", ["[40, 80]", "[41,80,120,160,200]", "[true,80,120,160,200]", "{}"])
def test_rejeita_nota_invalida(resposta):
    with pytest.raises(ValueError):
        estimar_notas(lambda _: resposta, "Tema", "Texto")


def test_redacao_salva_antes_da_estimativa_e_aparece_no_historico(monkeypatch, dados_discursivos):
    usuario, outro = dados_discursivos["usuarios"]
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)

    def indisponivel(_):
        raise RuntimeError("Falha simulada")

    monkeypatch.setattr(worker, "enviar_mensagem", indisponivel)
    with app.test_client() as cliente:
        assert cliente.get("/redacoes").status_code == 302
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        lista = cliente.get("/redacoes").get_data(as_text=True)
        assert '<body class="sidebar-toggle"' in lista
        folha = cliente.get("/redacoes/tema/sus-2026").get_data(as_text=True)
        assert '<body class="sidebar-toggle"' in folha
        assert 'id="aviso-linhas" class="redacoes-aviso"' in folha
        assert folha.index("30 pautas") < folha.index("Folha de redação")
        tema = "/redacoes/tema/sus-2026"
        dados = preparar_envio(cliente, tema, texto="Minha redação.")
        assert cliente.post(tema, data={**dados, "texto": " "}).status_code == 422
        envio = cliente.post(tema, data=dados)
        assert envio.status_code == 303
        caminho = envio.location
        assert cliente.post(tema, data=dados).location == caminho
        assert "fila de processamento" in cliente.get(caminho).get_data(as_text=True)
        assert "primeira correção" in cliente.get("/redacoes").get_data(as_text=True)
        processar_envio(caminho)
        assert "agendada" in cliente.get(caminho).get_data(as_text=True)
        assert "agendada" in cliente.post(caminho + "/corrigir", follow_redirects=True).get_data(as_text=True)

        with conectar() as conexao:
            conexao.execute(
                "UPDATE redacoes SET correcao_tentar_apos = CURRENT_TIMESTAMP WHERE id = %s",
                (int(caminho.rsplit("/", 1)[-1]),),
            )
        monkeypatch.setattr(worker, "enviar_mensagem", lambda _: "[40, 80, 120, 160, 200]")
        processar_envio(caminho)
        resposta = cliente.get(caminho).get_data(as_text=True)
        assert '<body class="sidebar-toggle"' in resposta
        assert resposta.count('<meter min="0" max="200"') == 5
        assert "600 / 1000" in resposta
        assert "Minha redação." in resposta
        assert "600,0 / 1000" in cliente.get("/redacoes").get_data(as_text=True)
        outro_tema = "/redacoes/tema/teatro-2025"
        outro_envio = cliente.post(outro_tema, data=preparar_envio(cliente, outro_tema, texto="Outro texto."))
        assert outro_envio.status_code == 303
        assert caminho in cliente.get("/provas/historico").get_data(as_text=True)

        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = outro
        assert cliente.get(caminho).status_code == 404
        assert cliente.post(caminho + "/corrigir").status_code == 404
        assert caminho not in cliente.get("/provas/historico").get_data(as_text=True)

        limpar_historico(usuario)
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        assert cliente.get(caminho).status_code == 404


def test_temas_enem_usam_instrucoes_compartilhadas(monkeypatch, dados_discursivos):
    monkeypatch.setitem(app.config, "TESTING", True)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = dados_discursivos["usuarios"][0]
        for tema in ("sus-2026", "envelhecimento-2025", "teatro-2025"):
            pagina = cliente.get(f"/redacoes/tema/{tema}").get_data(as_text=True)
            assert pagina.count('id="instrucoes-redacao"') == 1
            assert pagina.index('id="instrucoes-redacao"') < pagina.index('id="aviso-linhas"')
            assert 'class="redacoes-voltar"' in pagina
            if tema == "envelhecimento-2025":
                assert "Material provisório" not in pagina
                assert "<h3>Texto IV</h3>" in pagina
                assert "expectativas sociais" in pagina


def test_ita_usa_titulo_rubrica_e_escala_proprios(monkeypatch, dados_discursivos):
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)

    def corrigir(prompt):
        assert "Modalidade escrita" in prompt
        assert "Meu título" in prompt
        return "[20, 18, 16, 15, 17]"

    monkeypatch.setattr(worker, "enviar_mensagem", corrigir)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = dados_discursivos["usuarios"][0]
        lista = cliente.get("/redacoes").get_data(as_text=True)
        assert "<summary>ITA</summary>" in lista
        assert "Tema autoral de treino" in lista
        caminho = "/redacoes/tema/soberania-tecnologica-ita-2027"
        pagina = cliente.get(caminho).get_data(as_text=True)
        assert "<h3>Texto VI</h3>" in pagina
        assert "Critérios de avaliação do ITA 2027" not in pagina
        assert "25 a 35 linhas" in pagina
        assert 'style="--linhas: 35"' in pagina
        dados = preparar_envio(cliente, caminho, texto="Um argumento.")
        assert cliente.post(caminho, data=dados).status_code == 422
        resultado = cliente.post(caminho, data={**dados, "titulo": "Meu título"})
        processar_envio(resultado.location)
        resposta = cliente.get(resultado.location).get_data(as_text=True)
        assert "8,6 / 10" in resposta
        assert "1,8 / 2" in resposta
        assert "Meu título" in resposta
        assert "8,6 / 10" in cliente.get("/redacoes").get_data(as_text=True)
        assert "8,6 / 10" in cliente.get("/provas/historico").get_data(as_text=True)


@pytest.mark.parametrize(("prova", "limite", "notas", "media"), [
    ("ENEM", 3600, "[120, 120, 120, 120, 120]", "600,0 / 1000"),
    ("ITA", 3000, "[16, 16, 16, 16, 16]", "8,0 / 10"),
])
def test_surpresa_pausa_salva_e_alterna(prova, limite, notas, media, monkeypatch, dados_discursivos):
    from database import redacoes_surpresa_repository
    from database.tempo_provas_escritas import obter_duracao_provas_escritas_por_dia
    from services.redacoes_surpresa_service import TEMAS_SURPRESA

    usuario, outro = dados_discursivos["usuarios"]
    temas = TEMAS_SURPRESA[prova]
    agora = 100.0
    monkeypatch.setattr(redacoes_surpresa_repository, "time", lambda: agora)
    monkeypatch.setattr(worker, "enviar_mensagem", lambda _: notas)
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)

    def chave(html):
        return re.search(r'name="chave" value="([a-f0-9]+)"', html)[1]

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        caminho = f"/redacoes/surpresa/{prova}"
        lista = cliente.get("/redacoes").get_data(as_text=True)
        assert all(tema["titulo"] not in lista for tema in temas)
        resposta = cliente.get(caminho)
        assert resposta.cache_control.no_store
        pagina = resposta.get_data(as_text=True)
        assert temas[0]["titulo"] in pagina
        dados = {"chave": chave(pagina), "texto": "Meu rascunho", "titulo": "Meu título"}
        ativo = cliente.post(caminho + "/tempo", data=dict(dados, acao="ativo", revisao=1))
        assert ativo.json["restante"] == limite
        agora += 7
        pausa = cliente.post(caminho + "/tempo", data=dict(dados, acao="pausar", revisao=2))
        assert pausa.json["restante"] == limite - 7
        agora += 200
        pagina = cliente.get(caminho).get_data(as_text=True)
        assert "Meu rascunho" in pagina
        assert temas[0]["titulo"] in pagina
        assert f'data-restante="{limite - 7}.0"' in pagina
        assert cliente.post(caminho + "/tempo", data=dict(dados, acao="ativo", revisao=3)).status_code == 409
        dados["chave"] = chave(pagina)
        cliente.post(caminho + "/tempo", data=dict(dados, acao="ativo", revisao=3))
        agora += 5
        envio = cliente.post(caminho, data=dados)
        assert cliente.post(caminho, data=dados).location == envio.location
        processar_envio(envio.location)
        assert "00:12" in cliente.get(envio.location).get_data(as_text=True)
        assert temas[1]["titulo"] in cliente.get(caminho).get_data(as_text=True)
        assert media in cliente.get("/redacoes").get_data(as_text=True)
        assert "00:12" in cliente.get("/provas/historico").get_data(as_text=True)
        assert sum(d["duracao"] for d in obter_duracao_provas_escritas_por_dia(usuario, hoje=True)) == 12
        assert not obter_duracao_provas_escritas_por_dia(outro)


def test_reserva_redacao_expirada_nao_grava_resultado(monkeypatch, dados_discursivos):
    usuario = dados_discursivos["usuarios"][0]
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        tema = "/redacoes/tema/sus-2026"
        anterior = cliente.post(tema, data=preparar_envio(cliente, tema, texto="Um argumento."))
        envio_id = int(anterior.location.rsplit("/", 1)[-1])
        with ThreadPoolExecutor(max_workers=2) as executor:
            reservas = list(executor.map(reivindicar_redacao, (envio_id, envio_id)))
        unica = [reserva for reserva in reservas if reserva]
        assert len(unica) == 1

        with conectar() as conexao:
            conexao.execute("""
                UPDATE redacoes SET correcao_reivindicada_ate = CURRENT_TIMESTAMP - INTERVAL '1 second'
                WHERE id = %s
            """, (envio_id,))
        reserva_nova = reivindicar_redacao(envio_id)
        assert reserva_nova["correcao_tentativas"] == 2
        assert not encerrar_redacao(unica[0], [200] * 5)
        assert encerrar_redacao(reserva_nova, [120] * 5)
        assert "600 / 1000" in cliente.get(anterior.location).get_data(as_text=True)


def test_redacao_esgotada_pode_ser_reenfileirada(monkeypatch, dados_discursivos):
    usuario = dados_discursivos["usuarios"][0]
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        tema = "/redacoes/tema/sus-2026"
        anterior = cliente.post(tema, data=preparar_envio(cliente, tema, texto="Redação salva."))
        envio_id = int(anterior.location.rsplit("/", 1)[-1])
        with conectar() as conexao:
            conexao.execute("""
                UPDATE redacoes SET correcao_tentativas = %s,
                    correcao_reivindicada_ate = CURRENT_TIMESTAMP - INTERVAL '1 second'
                WHERE id = %s
            """, (worker.MAX_TENTATIVAS, envio_id))

        worker.recuperar_redacoes_esgotadas()
        assert not reivindicar_redacao(envio_id)
        assert "Tentar correção novamente" in cliente.get(anterior.location).get_data(as_text=True)
        assert {item["fila"] for item in worker.status_filas()} == {"discursivas", "redacoes"}
        assert cliente.post(anterior.location + "/corrigir").status_code == 303
        reserva = reivindicar_redacao(envio_id)
        assert reserva["texto"] == "Redação salva."
        assert reserva["correcao_tentativas"] == 1
