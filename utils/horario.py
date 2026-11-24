import os
from datetime import datetime
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def horario_studyhub(valor):
    """Converte registros antigos sem fuso conforme o ambiente que os gravou."""
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor)
    if valor.tzinfo is None:
        padrao = "UTC" if os.getenv("RENDER", "").lower() == "true" else SAO_PAULO.key
        origem = ZoneInfo(os.getenv("STUDYHUB_FUSO_REGISTROS", padrao))
        valor = valor.replace(tzinfo=origem)
    return valor.astimezone(SAO_PAULO)
