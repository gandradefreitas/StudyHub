from collections import Counter
from datetime import date, timedelta

import pytest

from database.conexao import conectar
from services.idiomas_service import DIFICULDADES, TEXTOS, montar_estatisticas
from tests.app_de_teste import app


def test_catalogo_tem_tres_leituras_por_idioma_e_dificuldade_progressiva():
    assert Counter(t["idioma"] for t in TEXTOS.values()) == {"en": 3, "es": 3}
    for texto in TEXTOS.values():
        assert texto["palavras"] > 100
        assert tuple(q["dificuldade"] for q in texto["questoes"]) == DIFICULDADES
        for questao in texto["questoes"]:
            assert len(set(questao["opcoes"])) == 4
            assert 0 <= questao["correta"] <= 3


def test_estatisticas_agrupam_por_dia_e_mantem_total_de_todos_os_meses():
    hoje = date(2024, 3, 1)
    leituras = [
        {"concluido_em": date(2024, 2, 29), "palavras": 100},
        {"concluido_em": date(2024, 2, 29), "palavras": 120},
        {"concluido_em": hoje, "palavras": 150},
    ]
    fevereiro = montar_estatisticas(leituras, hoje, "2024-02")
    assert fevereiro["anterior"] == "2024-01"
    assert fevereiro["seguinte"] == "2024-03"
    assert fevereiro["dias"] == [0] * 28 + [220]
    assert fevereiro["total_mes"] == 220
    assert fevereiro["hoje"] == 150
    assert fevereiro["total"] == 370
    for mes in ("inválido", "2024-04", "2024-0301"):
        assert montar_estatisticas(leituras, hoje, mes)["mes"] == "2024-03"


@pytest.mark.parametrize("texto_id", ["the-library-of-things", "un-mapa-para-volver"])
def test_progresso_de_leitura_por_usuario_sem_contagem_duplicada(
    monkeypatch, dados_discursivos, texto_id,
):
    monkeypatch.setitem(app.config, "TESTING", True)
    usuario_id, outro_id = dados_discursivos["usuarios"]
    texto = TEXTOS[texto_id]
    caminho = f"/idiomas/{texto['id']}"

    with app.test_client() as cliente:
        assert cliente.get("/idiomas").status_code == 302
        assert cliente.get(caminho).status_code == 302
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario_id

        lista = cliente.get("/idiomas").get_data(as_text=True)
        assert lista.count('class="idiomas-grupo"') == 2
        assert lista.count('class="idiomas-texto"') == 6
        assert "Já lido" not in lista
        pagina = cliente.get(caminho).get_data(as_text=True)
        assert pagina.count('type="radio"') == 40
        assert cliente.get("/idiomas/texto-inexistente").status_code == 404
        assert cliente.post(caminho, data={"questao-1": "0"}).status_code == 400
        monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
        respostas = {f"questao-{n}": str(q["correta"]) for n, q in enumerate(texto["questoes"], 1)}
        incompleto = {campo: valor for campo, valor in respostas.items() if campo != "questao-10"}
        assert cliente.post(caminho, data=incompleto).status_code == 422
        for resposta in ("-1", ["0", "1"]):
            assert cliente.post(caminho, data=respostas | {"questao-10": resposta}).status_code == 422
        with conectar() as conexao:
            assert not conexao.execute(
                "SELECT 1 FROM leituras_idiomas WHERE usuario_id = %s", (usuario_id,)
            ).fetchone()

        resposta = cliente.post(caminho, data=respostas, follow_redirects=True)
        assert resposta.history[0].status_code == 303
        assert resposta.history[0].location.endswith("#resultado")
        assert "10 de 10" in resposta.get_data(as_text=True)
        lista = cliente.get("/idiomas").get_data(as_text=True)
        assert 'idiomas-texto idiomas-lido' in lista
        assert "Já lido" in lista
        assert f"<dt>Hoje</dt><dd>{texto['palavras']}</dd>" in lista
        assert f"<dt>Total acumulado</dt><dd>{texto['palavras']}</dd>" in lista

        assert 'type="radio"' not in resposta.get_data(as_text=True)
        repetida = cliente.post(caminho, data=respostas)
        assert repetida.status_code == 429
        assert 1 <= int(repetida.headers["Retry-After"]) <= 600
        assert "10 de 10" in repetida.get_data(as_text=True)
        outro_texto = next(chave for chave in TEXTOS if chave != texto["id"])
        assert 'type="radio"' in cliente.get(f"/idiomas/{outro_texto}").get_data(as_text=True)

        with conectar() as conexao:
            primeira = conexao.execute("""
                SELECT concluido_em FROM leituras_idiomas WHERE usuario_id = %s
            """, (usuario_id,)).fetchone()["concluido_em"]
            anterior = primeira.replace(day=1) - timedelta(days=1)
            conexao.execute("""
                UPDATE leituras_idiomas
                SET concluido_em = %s, ultimo_envio_em = CURRENT_TIMESTAMP - INTERVAL '10 minutes'
                WHERE usuario_id = %s
            """, (anterior, usuario_id))

        respostas["questao-1"] = str((int(respostas["questao-1"]) + 1) % 4)
        resposta = cliente.post(caminho, data=respostas, follow_redirects=True)
        assert "9 de 10" in resposta.get_data(as_text=True)
        lista = cliente.get(f"/idiomas?mes={anterior:%Y-%m}").get_data(as_text=True)
        assert "Próximo mês" in lista
        assert "<dt>Hoje</dt><dd>0</dd>" in lista
        assert f"<dt>Total acumulado</dt><dd>{texto['palavras']}</dd>" in lista
        assert f"<dt>Mês selecionado</dt><dd>{texto['palavras']}</dd>" in lista
        assert f'<th scope="row">{anterior.day}</th><td>{texto["palavras"]}</td>' in lista

        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = outro_id
        lista = cliente.get("/idiomas").get_data(as_text=True)
        assert "Já lido" not in lista
        assert "<dt>Total acumulado</dt><dd>0</dd>" in lista
