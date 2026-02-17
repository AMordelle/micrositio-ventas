from .detect_pdf_type import detect_pdf_type
from .text_extractor import extract_text_from_pdf
from .ocr_extractor import extract_text_ocr

def extract_pdf(pdf_path: str) -> dict:
    """
    Detecta el tipo de PDF y extrae su contenido.
    Retorna: {page_number: text}
    """
    pdf_type = detect_pdf_type(pdf_path)
    print(f"Tipo detectado: {pdf_type}")

    if pdf_type == "text":
        return extract_text_from_pdf(pdf_path)

    return extract_text_ocr(pdf_path)
