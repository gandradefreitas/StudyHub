from flask import Blueprint, jsonify, request, session

from database.experiencia_repository import equipar_moldura, obter_nivel

niveis = Blueprint("niveis", __name__, url_prefix="/nivel")


@niveis.post("/progresso")
def progresso():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify(erro="Usuário não autenticado."), 401
    return jsonify(obter_nivel(usuario_id, notificar=True))


@niveis.post("/moldura")
def atualizar_moldura():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify(erro="Usuário não autenticado."), 401
    dados = request.get_json(silent=True)
    marco = dados.get("nivel") if isinstance(dados, dict) else None
    if not equipar_moldura(usuario_id, marco):
        return jsonify(erro="Escolha uma moldura que você já conquistou."), 400
    return jsonify(moldura_equipada=marco)
