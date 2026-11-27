from io import BytesIO
import re

from PIL import Image

from database.conexao import conectar
from database.rank_repository import ranking_nivel, ranking_questoes, ranking_tempo
from tests.app_de_teste import app


def test_rank_compara_atividade_e_serve_apenas_fotos_autorizadas(dados_discursivos):
    primeiro, segundo = dados_discursivos["usuarios"]
    foto = BytesIO()
    Image.new("RGB", (64, 64), "blue").save(foto, format="JPEG")
    with conectar() as banco:
        banco.execute("""
            INSERT INTO respostas_questoes (usuario_id, questao_numero, resposta, correta)
            VALUES (%s, 1, 'A', 1), (%s, 1, 'B', 0)
        """, (primeiro, segundo))
        banco.execute("""
            INSERT INTO resultados_provas (usuario_id, prova_id, acertos, erros, nao_respondidas, total, tempo_gasto, porcentagem)
            VALUES (%s, 1, 10, 0, 80, 90, '00:01:30', 11.1),
                   (%s, 1, 9, 1, 80, 90, '00:01:00', 10.0)
        """, (primeiro, segundo))
        banco.execute("""
            INSERT INTO estudos (usuario_id, inicio, duracao, ativa) VALUES (%s, LOCALTIMESTAMP, 600, 0)
        """, (segundo,))
        banco.execute("""
            UPDATE tentativas_provas_discursivas
            SET status = 'finalizada', data_finalizacao = data_inicio + INTERVAL '2 minutes'
            WHERE usuario_id = %s
        """, (segundo,))
        banco.execute("""
            INSERT INTO redacoes (usuario_id, tema, ano, texto, tempo_segundos)
            VALUES (%s, 'Treino', 0, 'Texto', 60)
        """, (segundo,))
        banco.execute("INSERT INTO fotos_perfil (usuario_id, imagem) VALUES (%s, %s)", (segundo, foto.getvalue()))

    try:
        questoes = [p for p in ranking_questoes() if p["id"] in (primeiro, segundo)]
        assert [p["id"] for p in questoes] == [primeiro, segundo]
        assert [p["resolvidas"] for p in questoes] == [11, 11]
        assert questoes[0]["aproveitamento"] == 100

        tempo = [p for p in ranking_tempo() if p["id"] in (primeiro, segundo)]
        assert [(p["id"], p["segundos"]) for p in tempo] == [(segundo, 840), (primeiro, 90)]
        with app.test_client() as cliente:
            assert cliente.get("/rank").status_code == 302
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = primeiro
            pagina = cliente.get("/rank?criterio=tempo")
            assert pagina.status_code == 200
            html = pagina.get_data(as_text=True)
            assert "14min" in html
            assert "rank-coroado" in html
            assert "@example.invalid" not in html
            src = re.search(r'<img src="(/rank/foto/[^"]+)"', html)[1]
            assert cliente.get(src).data == foto.getvalue()
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = segundo
            assert cliente.get(src).status_code == 404
    finally:
        with conectar() as banco:
            for id_usuario in (primeiro, segundo):
                banco.execute("DELETE FROM resultados_provas WHERE usuario_id = %s", (id_usuario,))
            banco.execute("DELETE FROM estudos WHERE usuario_id = %s", (segundo,))


def test_ranking_exibe_somente_50_posicoes(dados_discursivos, monkeypatch):
    from controllers import rank_controller

    colocados = [
        {"id": n, "nome": f"Estudante {n}", "tem_foto": False, "resolvidas": 55-n, "aproveitamento": 50}
        for n in range(1, 51)
    ]
    monkeypatch.setattr(rank_controller, "ranking_questoes", lambda: colocados)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = dados_discursivos["usuarios"][0]
        html = cliente.get("/rank").get_data(as_text=True)
        assert html.count('class="rank-linha"') == 50
        assert html.count('class="rank-podio-cartao') == 3
        assert ">#50<" in html
        assert ">#51<" not in html



def test_rank_nivel_ordena_por_exp_e_exibe_nivel(dados_discursivos):
    primeiro, segundo = dados_discursivos["usuarios"]

    with conectar() as banco:
        banco.execute("""
            INSERT INTO experiencia_atividades (usuario_id, origem, referencia, exp_decimos)
            VALUES (%s, 'teste', 'a', 4000), (%s, 'teste', 'a', 4000), (%s, 'teste', 'b', 251)
        """, (primeiro, segundo, segundo))

    colocados = [p for p in ranking_nivel() if p["id"] in (primeiro, segundo)]
    assert [(p["id"], p["exp_decimos"]) for p in colocados] == [(segundo, 4251), (primeiro, 4000)]

    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = primeiro
        pagina = cliente.get("/rank?criterio=nivel")
        assert pagina.status_code == 200
        html = pagina.get_data(as_text=True)
        assert '<option value="nivel" selected>Nível</option>' in html
        assert "Nível 1" in html
        assert "425,1 EXP" in html
        assert html.index("425,1 EXP") < html.index("400 EXP")
