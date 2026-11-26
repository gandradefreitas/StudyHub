MOLDURAS = {
    1: "Iniciante",
    3: "Em Ritmo",
    5: "Constante",
    10: "Focado",
    15: "Estrategista",
    20: "Veterano",
    25: "Mestre de Rota",
    30: "Lenda do Hub",
    35: "Titânio",
    40: "Soberano",
    45: "Aurora",
    50: "Transcendente",
}


def proxima_moldura(nivel):
    return next((marco for marco in MOLDURAS if marco > nivel), None)
