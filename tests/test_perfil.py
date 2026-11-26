from io import BytesIO
from uuid import uuid4

from PIL import Image

from database.conexao import conectar
from tests.app_de_teste import app


def test_perfil_edita_dados_e_foto_somente_da_conta(dados_discursivos):
    usuario, outro = dados_discursivos["usuarios"]
    email = f"perfil-{uuid4().hex}@example.invalid"
    foto = BytesIO()
    Image.new("RGB", (450, 320), "blue").save(foto, format="PNG")
    foto.seek(0)

    with app.test_client() as cliente:
        assert cliente.get("/perfil/foto").status_code == 404
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario
        pagina = cliente.get("/dashboard").get_data(as_text=True)
        assert 'aria-controls="janela-perfil"' in pagina
        assert '<dialog id="janela-perfil"' in pagina
        assert 'enctype="multipart/form-data"' in pagina
        from re import search
        token = search(r'name="csrf_token"\s+value="([^"]+)"', pagina)[1]
        resp = cliente.post("/perfil", data={
            "nome": "Nome Editado",
            "email": email,
            "foto": (foto, "teste.png"),
            "csrf_token": token,
        })
        assert resp.status_code == 303
        avatar = cliente.get("/perfil/foto")
        assert avatar.status_code == 200
        assert avatar.mimetype == "image/jpeg"
        assert avatar.cache_control.no_store
        with Image.open(BytesIO(avatar.data)) as salva:
            assert salva.size == (256, 256)
        assert email in cliente.get("/dashboard").get_data(as_text=True)

        foto_invalida = cliente.post("/perfil", data={
            "nome": "Nome Não Gravado",
            "email": email,
            "foto": (BytesIO(b"texto"), "teste.png"),
            "csrf_token": token,
        }, follow_redirects=True)
        assert "Selecione uma foto" in foto_invalida.get_data(as_text=True)
        assert cliente.get("/perfil/foto").data == avatar.data
        titular = cliente.post("/perfil", data={"nome": "Nome Sem Foto", "email": email, "csrf_token": token})
        assert titular.status_code == 303
        assert cliente.get("/perfil/foto").data == avatar.data
        with cliente.session_transaction() as sessao:
            sessao["usuario_id"] = outro
        assert cliente.get("/perfil/foto").status_code == 404

    with conectar() as banco:
        perfil = banco.execute("SELECT nome, email FROM usuarios WHERE id = %s", (usuario,)).fetchone()
    assert perfil == {"nome": "Nome Sem Foto", "email": email}
