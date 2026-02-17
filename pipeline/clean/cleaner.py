import re

def clean_text_block(text: str) -> str:
    """
    Limpia artefactos, símbolos y ruido común en catálogos.
    """
    # Quitar basura típica
    text = re.sub(r"[•●■□▪▫►◄◆◇◆◆]+", "", text)
    text = re.sub(r"[|]{2,}", " ", text)
    text = re.sub(r"[-]{3,}", " ", text)

    # Quitar páginas numeradas tipo "Pág. 5"
    text = re.sub(r"P[aá]g\.?\s*\d+", "", text, flags=re.I)

    # Quitar separadores genéricos
    text = re.sub(r"_{2,}", " ", text)

    # Arreglar espacios alrededor de símbolos
    text = re.sub(r"\s+([$%])", r" \1", text)

    # Remover múltiples espacios
    text = re.sub(r"[ ]{2,}", " ", text)

    return text.strip()
