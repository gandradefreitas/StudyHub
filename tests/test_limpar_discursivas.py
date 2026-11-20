import pytest
from tests.app_de_teste import app
from database.conexao import conectar


@pytest.mark.parametrize("status", ["corrigida", "finalizada", "em_andamento"])
def test_limpar_historico_das_discursivas(dados_discursivos, monkeypatch, status):
    usuario, outro = dados_discursivos["usuarios"]
    tentativa, tentativa_outro = dados_discursivos["tentativas"]

    with conectar() as conexao:
        conexao.execute("""
            UPDATE tentativas_provas_discursivas
            SET status = %s, data_finalizacao = CURRENT_TIMESTAMP,
                nota_total = 87, nota_maxima = 100
            WHERE id = ANY(%s)
            """, (status, [tentativa, tentativa_outro]))
        conexao.execute("""
            INSERT INTO respostas_discursivas (tentativa_id, questao_numero, item_letra, resposta)
            VALUES (%s, 1, 'a', 'minha resposta'), (%s, 1, 'a', 'outra resposta')
            """, (tentativa, tentativa_outro))

    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario

        historico = cliente.get("/provas/historico")
        assert b"Matem" in historico.data
        if status != "em_andamento":
            assert b"87/100" in cliente.get("/notas").data

        for _ in range(2):
            resposta = cliente.post("/configuracoes/dados/limpar")
            assert resposta.status_code == 302

        assert b"Matem" not in cliente.get("/provas/historico").data
        assert b"87/100" not in cliente.get("/notas").data
        assert cliente.get(f"/provas/ita/2025/segunda-fase/resultado/{tentativa}").status_code == 404

    with conectar() as conexao:
        assert conexao.execute("""
            SELECT id FROM tentativas_provas_discursivas WHERE id = ANY(%s)
            """, ([tentativa, tentativa_outro],)).fetchall() == [{"id": tentativa_outro}]
        assert conexao.execute("""
            SELECT resposta FROM respostas_discursivas WHERE tentativa_id = ANY(%s)
            """, ([tentativa, tentativa_outro],)).fetchall() == [{"resposta": "outra resposta"}]
