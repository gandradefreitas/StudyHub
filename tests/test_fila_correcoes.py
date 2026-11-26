from database.conexao import conectar
from database.respostas_discursivas_repository import (
    obter_tentativa_discursiva_por_id,
    reivindicar_correcao_discursiva,
)
from tests.app_de_teste import app
import worker_correcao_discursiva as worker


def test_discursiva_na_fila_reagenda_falha_e_persiste_correcao(monkeypatch, dados_discursivos):
    usuario = dados_discursivos["usuarios"][0]
    tentativa = dados_discursivos["tentativas"][0]
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    caminho = "/provas/ita/2025/segunda-fase/matematica"

    def falhar(*args, **kwargs):
        raise RuntimeError("indisponível")

    monkeypatch.setattr(worker, "corrigir_tentativa_resposta_final", falhar)
    with app.test_client() as cliente:
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        envio = cliente.post(caminho + "/finalizar", data={"tentativa_id": tentativa})
        assert envio.status_code == 302
        assert "fila de correção" in cliente.get(envio.location).get_data(as_text=True)
        reserva = reivindicar_correcao_discursiva(tentativa, usuario)
        worker.processar_discursiva(reserva)
        agendada = obter_tentativa_discursiva_por_id(tentativa, usuario)
        assert agendada["resultado_correcao"]["status"] == "indisponivel"
        assert agendada["correcao_reivindicada_ate"] is None
        assert not reivindicar_correcao_discursiva(tentativa, usuario)

        with conectar() as conexao:
            conexao.execute("""
                UPDATE tentativas_provas_discursivas
                SET proxima_tentativa_correcao = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (tentativa,))

        monkeypatch.setattr(worker, "corrigir_tentativa_resposta_final",
                            lambda *args, **kwargs: {"status": "corrigida", "nota": 60, "nota_maxima": 100})
        nova_reserva = reivindicar_correcao_discursiva(tentativa, usuario)
        assert nova_reserva["tentativas_correcao"] == 2
        worker.processar_discursiva(nova_reserva)
        corrigida = obter_tentativa_discursiva_por_id(tentativa, usuario)
        assert corrigida["status"] == "corrigida"
        assert corrigida["nota_total"] == 60
        assert not reivindicar_correcao_discursiva(tentativa, usuario)


def test_supervisor_encerra_worker_se_web_falha(monkeypatch):
    import executar_local

    class Processo:
        def __init__(self, codigo):
            self.codigo = codigo
            self.encerrado = False

        def poll(self):
            return self.codigo

        def terminate(self):
            self.encerrado = True
            self.codigo = 0

        def wait(self, timeout=None):
            return self.codigo

    fila = Processo(None)
    web = Processo(3)
    processos = iter((fila, web))
    etapas = []

    def iniciar(*args, **kwargs):
        etapas.append("processo")
        return next(processos)

    monkeypatch.setattr(executar_local, "migrar_banco_local", lambda: etapas.append("migrar"))
    monkeypatch.setattr(executar_local, "Popen", iniciar)
    assert executar_local.executar() == 3
    assert etapas == ["migrar", "processo", "processo"]
    assert fila.encerrado
