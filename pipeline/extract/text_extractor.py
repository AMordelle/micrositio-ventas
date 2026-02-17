import fitz

def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrae texto de cada página del PDF.
    Retorna un diccionario {page_number: text}
    """
    doc = fitz.open(pdf_path)
    pages = {}

    for i, page in enumerate(doc):
        pages[i+1] = page.get_text("text")

    doc.close()
    return pages
