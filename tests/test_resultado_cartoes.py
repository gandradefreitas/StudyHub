from html import escape

import pytest
from tests.app_de_teste import modulo


@pytest.mark.parametrize("disciplina,slug", [
    ("Matemática", "matematica"),
    ("Física", "fisica"),
    ("Química", "quimica"),
])
def test_cartoes_usam_gabarito_cadastrado(monkeypatch, disciplina, slug):
    prova = modulo.carregar_prova_ita_segunda_fase(slug)
    gabarito = {
        f"Q{questao.numero}{str(item.letra or '').strip()}": item.resposta_esperada
        for questao in prova.questoes for item in questao.itens
    }
    letras = list(gabarito)[:4]
    itens = [
        {
            "letra": letra, "pontos_maximos": 3.3,
            "justificativa": "Justificativa redundante",
            "criterios": [{"evidencias": [{"trecho": "Evidência do aluno"}]}],
        }
        for letra in letras
    ]
    pontuacoes = [
        {"letra": letra, "nota": nota, "status": status}
        for letra, nota, status in zip(letras, [0, 1.1, 3.3, 0],
                                       ["avaliado", "avaliado", "avaliado", "provisorio"])
    ]
    tentativa = {
        "instituicao": "ITA", "ano": 2025, "fase": "Segunda Fase",
        "disciplina": disciplina, "status": "corrigida", "nota_total": 4.4,
        "nota_maxima": 100, "resultado_correcao": {
            "modo_correcao": "resposta_final", "status": "corrigida",
            "validacao": {}, "pontuacoes_itens": pontuacoes, "correcao": {
                "itens": itens, "resumo": {"pontos_a_melhorar": ["Resumo redundante"]},
            },
        },
    }
    monkeypatch.setattr(modulo, "obter_tentativa_discursiva_por_id", lambda **_: tentativa)
    monkeypatch.setattr(modulo, "obter_respostas", lambda _: {(1, "a"): "Resposta do estudante"})
    with modulo.app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = 1
        resposta = cliente.get("/provas/ita/2025/segunda-fase/resultado/1")
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    for letra, situacao in zip(letras, ["incorreta", "incompleta", "correta", None]):
        _, cartao = html.split(f"<h3>Questão {letra}</h3>", 1)
        cartao = cartao.split("</article>", 1)[0]
        assert "Pontuação:" in cartao
        assert "Resposta esperada:" in cartao
        assert escape(gabarito[letra]).replace("&#x27;", "&#39;").replace("&quot;", "&#34;") in cartao
        assert (f"Resposta final {situacao}." if situacao else "Comparação inconclusiva.") in cartao
        if situacao:
            assert f'resultado-resposta-final--{situacao}' in html
    for texto in ("Comparação das respostas finais", "Pontos a melhorar",
                 "Justificativa redundante", "Evidência do aluno"):
        assert texto not in html
    assert "Resposta do estudante" in html
