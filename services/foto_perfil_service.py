from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

LIMITE_FOTO = 2 * 1024 * 1024
FORMATOS = ("JPEG", "PNG", "WEBP")


def preparar_foto(arquivo):
    dados = arquivo.read(LIMITE_FOTO + 1)
    if len(dados) > LIMITE_FOTO:
        raise ValueError("Escolha uma foto de até 2 MB.")

    try:
        with Image.open(BytesIO(dados), formats=FORMATOS) as original:
            if original.width * original.height > 20_000_000:
                raise ValueError("Escolha uma foto com resolução de até 20 megapixels.")
            orientada = ImageOps.exif_transpose(original).convert("RGBA")
            foto = ImageOps.fit(orientada, (256, 256), method=Image.Resampling.LANCZOS)
            fundo = Image.new("RGB", foto.size, "white")
            fundo.paste(foto, mask=foto.getchannel("A"))
            saida = BytesIO()
            fundo.save(saida, format="JPEG", quality=88, optimize=True)
            return saida.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as erro:
        raise ValueError("Selecione uma foto JPEG, PNG ou WebP válida.") from erro
