from .normalizer import normalize_text
from .cleaner import clean_text_block
from .page_segmenter import segment_text

def clean_page_text(raw_page_text: str) -> list:
    """
    Aplica el pipeline completo:
    1. Normalización
    2. Limpieza avanzada
    3. Segmentación en bloques
    """
    # Normalizar
    normalized = normalize_text(raw_page_text)

    # Limpiar artefactos
    cleaned = clean_text_block(normalized)

    # Segmentar
    blocks = segment_text(cleaned)

    return blocks
