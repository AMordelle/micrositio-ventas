import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Normaliza el texto:
    - Quita acentos inconsistentes
    - Convierte a NFC
    - Reemplaza espacios múltiples
    """
    # Normalización unicode
    text = unicodedata.normalize("NFC", text)

    # Quitar espacios extra
    text = re.sub(r"[ \t]+", " ", text)

    # Normalizar saltos dobles
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
