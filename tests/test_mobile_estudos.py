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
