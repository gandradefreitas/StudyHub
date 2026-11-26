from datetime import datetime, timezone

from database.conexao import conectar
from database.questoes_repository import obter_ordem_questoes
from tests.app_de_teste import app
from utils.horario import horario_studyhub


def test_horarios_render_e_locais(monkeypatch):
    monkeypatch.delenv("STUDYHUB_FUSO_REGISTROS", raising=False)
    monkeypatch.setenv("RENDER", "true")
    assert horario_studyhub(datetime(2026, 11, 24, 10)).hour == 7
    assert horario_studyhub(datetime(2026, 11, 24, 2, tzinfo=timezone.utc)).day == 23
    monkeypatch.delenv("RENDER")
    assert horario_studyhub(datetime(2026, 11, 24, 10)).hour == 10


def test_questoes_bloqueadas_dao_lugar_a_conclusao(dados_discursivos):
    usuario = dados_discursivos["usuarios"][0]
    try:
        with conectar() as banco:
            banco.execute("""
                INSERT INTO respostas_questoes (usuario_id, questao_numero, resposta, correta, proxima_tentativa)
                SELECT %s, numero, 'A', 1, LOCALTIMESTAMP + INTERVAL '3 days'
                FROM generate_series(1, 50) AS numero
            """, (usuario,))
        assert obter_ordem_questoes(usuario) == []
        with app.test_client() as cliente:
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = usuario
            resposta = cliente.get("/questoes", follow_redirects=True)
        assert resposta.status_code == 200
        assert "você chegou ao fim" in resposta.get_data(as_text=True)
        assert "https://res.cloudinary.com" in resposta.headers["Content-Security-Policy"].split("img-src", 1)[1].split(";")[0]
    finally:
        with conectar() as banco:
            banco.execute("DELETE FROM respostas_questoes WHERE usuario_id = %s", (usuario,))


def test_ordem_aleatoria_nao_muda_ao_responder(monkeypatch):
    import app as modulo

    disponiveis = list(range(1, 11))
    monkeypatch.setattr(modulo, "obter_ordem_questoes", lambda _: list(disponiveis))
    with app.test_request_context("/questoes"):
        primeira = modulo.questoes_em_ordem_aleatoria(1)
        assert sorted(primeira) == list(range(1, 11))
        assert primeira == modulo.questoes_em_ordem_aleatoria(1)
        escolhida = primeira[3]
        disponiveis.remove(escolhida)
        assert modulo.questoes_em_ordem_aleatoria(1) == [
            numero for numero in primeira if numero != escolhida
        ]


def test_revisao_abre_primeira_questao_filtrada_e_oculta_idioma_inexistente(dados_discursivos, monkeypatch):
    import app as modulo

    catalogo = modulo.obter_questoes_filtradas()
    sem_idioma = next(q for q in catalogo if not q.get("lingua") and q["area"] != "Linguagens")
    com_idioma = next(q for q in catalogo if q.get("lingua") and q["area"] != sem_idioma["area"])
    pendentes = [{"questao_numero": com_idioma["numero"]}, {"questao_numero": sem_idioma["numero"]}]
    monkeypatch.setattr(modulo, "obter_questoes_para_revisao", lambda _: pendentes)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = dados_discursivos["usuarios"][0]
        acesso = cliente.get("/questoes/revisar", query_string={"area": sem_idioma["area"]}, follow_redirects=True)
        assert acesso.status_code == 200
        assert len(acesso.history) == 1
        assert acesso.request.path == f"/questoes/{sem_idioma['numero']}"
        assert acesso.request.args["revisao"] == "1"
        assert acesso.request.args["area"] == sem_idioma["area"]
        html = acesso.get_data(as_text=True)
        assert '<span class="questoes-tag">None</span>' not in html
        assert "Voltar para questões" in html

        html = cliente.get("/questoes/revisar", follow_redirects=True).get_data(as_text=True)
        assert f'<span class="questoes-tag">{com_idioma["lingua"]}</span>' in html

        pendentes.clear()
        vazia = cliente.get("/questoes/revisar")
        assert vazia.status_code == 200
        assert "Todas as suas questões estão em dia." in vazia.get_data(as_text=True)
        assert "Começar revisão" not in vazia.get_data(as_text=True)
