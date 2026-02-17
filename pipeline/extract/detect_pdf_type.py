import fitz  # PyMuPDF

def detect_pdf_type(pdf_path: str) -> str:
    """
    Detecta si un PDF es de TEXTO o IMAGEN usando PyMuPDF.
    Retorna: "text" o "image"
    """
    doc = fitz.open(pdf_path)
    total_chars = 0

    for page in doc:
        text = page.get_text("text")
        total_chars += len(text.strip())

    doc.close()

    # Heurística: menos de 50 caracteres → probablemente escaneado
    return "text" if total_chars > 50 else "image"
