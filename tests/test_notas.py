from collections import Counter

import pytest
from tests.app_de_teste import app
from database.conexao import conectar
from services.notas_service import AREAS_ITA, avaliar_ita, faixa_enem
from services.provas_service import obter_prova


@pytest.mark.parametrize(("quantidades", "eliminado", "disciplinas", "acertos"), [
    ((6, 6, 6, 5), False, [], 18),
    ((9, 9, 9, 4), True, ["Inglês"], 27),
    ((5, 5, 5, 5), True, [], 15),
    ((4, 5, 5, 4), True, ["Matemática", "Inglês"], 14),
    ((12, 12, 12, 12), False, [], 36),
])
def test_ita_minimos(quantidades, eliminado, disciplinas, acertos):
    avaliacao = avaliar_ita(dict(zip(AREAS_ITA, quantidades)))
    assert avaliacao["eliminado"] is eliminado
    assert avaliacao["disciplinas_abaixo"] == disciplinas
    assert avaliacao["ciencias"] == acertos
    assert avaliacao["nota"] == pytest.approx(acertos * 10 / 36)


@pytest.mark.parametrize(("area", "total", "maximo"), [
    ("Linguagens", 47, 45), ("Ciências Humanas", 43, 45),
    ("Ciências da Natureza", 45, 43), ("Matemática", 45, 44),
])
def test_enem_faixas(area, total, maximo):
    for acertos in range(total + 1):
        (p10, mediana, p90), equivalente, referencia = faixa_enem(area, acertos, total)
        assert 0 <= equivalente <= maximo == referencia
        assert 0 <= p10 <= mediana <= p90
    assert faixa_enem(area, total, total)[1] == maximo


def concluir(cliente, prova_id, limites, idioma=None):
    prova = obter_prova(prova_id)
    assert cliente.get(f"/provas/{prova_id}").status_code == 200
    questoes = [q for q in prova.questoes if idioma is None or not q.lingua or q.lingua == idioma]
    acertos = Counter()
    respostas = {}
    for questao in questoes:
        if acertos[questao.area] < limites[questao.area]:
            respostas[str(questao.numero)] = questao.resposta
            acertos[questao.area] += 1

    resposta = cliente.post("/provas/resultado", json={
        "prova_id": prova_id, "questoes": [{"numero": q.numero} for q in questoes],
        "respostas": respostas, "lingua": idioma,
    })
    assert resposta.status_code == 200, resposta.json
    assert cliente.get("/provas/resultado").status_code == 200


def test_pagina_notas_usa_tentativas_proprias(app_de_teste, dados_discursivos):
    usuario, outro = dados_discursivos["usuarios"]
    tentativa = dados_discursivos["tentativas"][0]
    with conectar() as conexao:
        conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET status = 'corrigida', nota_total = 87, nota_maxima = 100,
                data_finalizacao = CURRENT_TIMESTAMP
            WHERE id = %s
            """, (tentativa,))
    with app.test_client() as cliente:
        assert cliente.get("/notas").status_code == 302
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        try:
            concluir(cliente, 1, {"Linguagens": 35, "Humanas": 30}, "ingles")
            concluir(cliente, 2, {"Natureza": 31, "Matematica": 32})
            concluir(cliente, 3, dict(zip(AREAS_ITA, (6, 6, 6, 5))))
            concluir(cliente, 3, dict(zip(AREAS_ITA, (4, 5, 5, 4))))
            resposta = cliente.get("/notas")
            assert resposta.status_code == 200
            html = resposta.get_data(as_text=True)
            for trecho in ("35/47", "30/43", "31/45", "32/45", "Nota da redação",
                           ">5</strong>", "Eliminado", "Matemática, Inglês",
                           "de 18 necessários", "87/100", 'aria-current="page"'):
                assert trecho in html
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = outro
            html = cliente.get("/notas").get_data(as_text=True)
            assert "35/47" not in html
            assert "87/100" not in html
        finally:
            with conectar() as conexao:
                conexao.execute("DELETE FROM respostas_provas WHERE usuario_id = %s", (usuario,))
                conexao.execute("DELETE FROM resultados_provas WHERE usuario_id = %s", (usuario,))


@pytest.fixture
def app_de_teste(monkeypatch):
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    return app
