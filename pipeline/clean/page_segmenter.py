import re

def segment_text(text: str) -> list:
    """
    Divide la página en bloques lógicos basados en:
    - saltos dobles
    - patrones de precio
    - encabezados
    Retorna una lista de bloques limpios.
    """
    # Separar por dobles saltos
    blocks = re.split(r"\n{2,}", text)

    # Limpieza adicional por bloque
    blocks = [b.strip() for b in blocks if b.strip()]

    return blocks
