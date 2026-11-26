from datetime import datetime, timedelta
from types import SimpleNamespace

from database.conexao import conectar
from database.fila_redacoes_repository import encerrar_redacao, reivindicar_redacao
from database.idiomas_repository import registrar_leitura
from database.questoes_repository import registrar_resposta_questao
from database.resultados_repository import salvar_resultado_com_respostas
from services.experiencia_service import calcular_progresso, exp_questao, exp_redacao, total_para_nivel
from tests.app_de_teste import app


def test_faixas_e_curva_de_experiencia():
    assert [exp_questao(x) for x in ("Fácil", "Médio", "Média", "Difícil")] == [50, 100, 100, 200]
    faixas = (0, 100, 200, 350, 500, 700, 950, 1250, 1600, 2000)
    for indice, ganho in enumerate(faixas):
        assert exp_redacao(100 * indice + 1, "ENEM") == ganho
        assert exp_redacao(100 * (indice + 1), "ENEM") == ganho
        assert exp_redacao(10 * indice + 1, "ITA") == ganho
        assert exp_redacao(10 * (indice + 1), "ITA") == ganho
    assert exp_redacao(75, "ITA") == 1250
    for nivel in range(100):
        inicio = total_para_nivel(nivel)
        custo = 10 * (100 + 20 * nivel + 2 * nivel**2)
        assert calcular_progresso(inicio)["necessario"] == custo
        assert calcular_progresso(inicio + custo - 1)["nivel"] == nivel
        assert calcular_progresso(inicio + custo)["nivel"] == nivel + 1


def test_atividades_geram_experiencia_uma_vez_e_nivel_e_notificado(dados_discursivos, monkeypatch):
    usuario, outro = dados_discursivos["usuarios"]
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    data = datetime.now()
    questao = SimpleNamespace(numero=1, alternativas=["A", "B"], resposta=0, dificuldade="Difícil")
    resultado = {
        "usuario_id": usuario, "prova_id": 1, "acertos": 1, "erros": 0,
        "nao_respondidas": 0, "total": 1, "tempo_gasto": "00:00:14", "porcentagem": 100,
    }
    try:
        for tentativa in (1, 2):
            registrar_resposta_questao(
                usuario, 1, "B", 0, tentativa, 3, data, data + timedelta(days=3), exp_decimos=100,
            )
            salvar_resultado_com_respostas(resultado, [questao], {"1": 0})
        assert registrar_leitura(usuario, "leitura-teste", 301, 7)
        with conectar() as banco:
            banco.execute("""
                UPDATE leituras_idiomas SET ultimo_envio_em = CURRENT_TIMESTAMP - INTERVAL '11 minutes'
                WHERE usuario_id = %s AND texto_id = 'leitura-teste'
            """, (usuario,))
        assert registrar_leitura(usuario, "leitura-teste", 301, 9)
        with conectar() as banco:
            envio = banco.execute("""
                INSERT INTO redacoes (usuario_id, tema, ano, texto, instituicao)
                VALUES (%s, 'Treino', 2025, 'Texto para o teste', 'ITA') RETURNING id
            """, (usuario,)).fetchone()["id"]
        reserva = reivindicar_redacao(envio)
        assert encerrar_redacao(reserva, [15] * 5)
        assert not encerrar_redacao(reserva, [20] * 5)
        with conectar() as banco:
            eventos = banco.execute("""
                SELECT origem, exp_decimos FROM experiencia_atividades WHERE usuario_id = %s
            """, (usuario,)).fetchall()
            assert {item["origem"]: item["exp_decimos"] for item in eventos} == {
                "estudos": 100, "prova_objetiva": 200, "idiomas": 301, "redacao": 1250,
            }
            assert len(eventos) == 4
        with app.test_client() as cliente:
            assert cliente.post("/nivel/progresso").status_code == 401
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = usuario
            esperado = {
                "nivel": 1, "proximo": 2, "progresso": 851, "necessario": 1220, "celebrar": True,
            }
            assert cliente.post("/nivel/progresso").json == esperado | {
                "moldura_equipada": 0,
                "proxima_moldura": 3,
                "molduras_conquistadas": [{"nivel": 1, "nome": "Iniciante"}],
            }
            assert cliente.post("/nivel/progresso").json == esperado | {
                "celebrar": False,
                "moldura_equipada": 0,
                "proxima_moldura": 3,
                "molduras_conquistadas": [],
            }
            html = cliente.get("/dashboard").get_data(as_text=True)
            assert 'data-progresso-nivel' in html
            assert 'value="851" max="1220"' in html
            with cliente.session_transaction() as sessao:
                sessao["usuario_id"] = outro
            assert cliente.post("/nivel/progresso").json["nivel"] == 0
    finally:
        with conectar() as banco:
            banco.execute("DELETE FROM resultados_provas WHERE usuario_id = %s", (usuario,))


def test_molduras_respeitam_marcos_e_escolha_persistente(dados_discursivos, monkeypatch):
    usuario, outro = dados_discursivos["usuarios"]
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    with conectar() as banco:
        banco.execute("""
            INSERT INTO experiencia_atividades (usuario_id, origem, referencia, exp_decimos)
            VALUES (%s, 'teste', 'molduras', %s)
        """, (usuario, total_para_nivel(5)))

    with app.test_client() as cliente:
        assert cliente.post("/nivel/moldura", json={"nivel": 1}).status_code == 401
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        dados = cliente.post("/nivel/progresso").json
        assert dados["nivel"] == 5
        assert dados["proxima_moldura"] == 10
        assert [item["nivel"] for item in dados["molduras_conquistadas"]] == [1, 3, 5]
        assert cliente.post("/nivel/progresso").json["molduras_conquistadas"] == []

        for invalida in (2, 10, True, "1"):
            assert cliente.post("/nivel/moldura", json={"nivel": invalida}).status_code == 400
        for moldura in (5, 1, 0, 3):
            resposta = cliente.post("/nivel/moldura", json={"nivel": moldura})
            assert resposta.json == {"moldura_equipada": moldura}
            assert cliente.post("/nivel/progresso").json["moldura_equipada"] == moldura
        html = cliente.get("/dashboard").get_data(as_text=True)
        assert 'data-avatar-moldura="3"' in html
        assert "Próxima moldura: Focado no nível 10." in html

        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = outro
        assert cliente.post("/nivel/moldura", json={"nivel": 1}).status_code == 400
        assert cliente.post("/nivel/progresso").json["moldura_equipada"] == 0
