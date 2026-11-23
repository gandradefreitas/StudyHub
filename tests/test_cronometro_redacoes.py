from database import redacoes_surpresa_repository as cronometro


def tentativa(**estado):
    return {
        "segundos": 0,
        "ativo_desde": None,
        "texto": "Rascunho salvo",
        "titulo": "Título salvo",
        **estado,
    }


def test_cronometro_para_contagem_apos_fechamento_abrupto(monkeypatch):
    monkeypatch.setattr(cronometro, "time", lambda: 200)
    estado = cronometro.estado_atual(
        tentativa(segundos=40, ativo_desde=100), 60, "pausar", "Texto", "Título",
    )

    assert estado["segundos"] == 40 + cronometro.JANELA_ATIVA
    assert estado["ativo_desde"] is None


def test_cronometro_congela_ultimo_rascunho_ao_chegar_ao_limite(monkeypatch):
    monkeypatch.setattr(cronometro, "time", lambda: 103)
    estado = cronometro.estado_atual(
        tentativa(segundos=58, ativo_desde=100), 60, "ativo", "Texto atrasado", "Título atrasado",
    )

    assert estado == {
        "segundos": 60,
        "ativo_desde": None,
        "texto": "Rascunho salvo",
        "titulo": "Título salvo",
    }



def test_cronometro_renova_token_csrf_sem_alterar_tentativa(dados_discursivos, monkeypatch):
    import re

    from tests.app_de_teste import app

    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = dados_discursivos["usuarios"][0]
        rota = "/redacoes/surpresa/ENEM"
        pagina = cliente.get(rota).get_data(as_text=True)
        chave = re.search(r'name="chave" value="([a-f0-9]+)"', pagina)[1]
        token = cliente.get(rota + "/tempo")
        assert token.status_code == 200
        assert token.cache_control.no_store
        dados = {"acao": "ativo", "revisao": "1", "chave": chave,
                 "csrf_token": token.json["csrf_token"], "texto": "Rascunho"}
        resposta = cliente.post(rota + "/tempo", data=dados)
        assert resposta.status_code == 200
        assert resposta.json["texto"] == "Rascunho"
        dados.update(acao="pausar", revisao="2", csrf_token=resposta.json["csrf_token"])
        assert cliente.post(rota + "/tempo", data=dados).status_code == 200
