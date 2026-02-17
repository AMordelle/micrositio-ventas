import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
from pathlib import Path

def preprocess_image(img):
    """Mejora OCR: escala gris, threshold, dilatación suave."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh

def extract_text_ocr(pdf_path: str) -> dict:
    pages_text = {}
    images = convert_from_path(pdf_path, dpi=300)

    for i, img in enumerate(images):
        img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        processed = preprocess_image(img_np)
        text = pytesseract.image_to_string(processed, lang="spa")
        pages_text[i+1] = text

    return pages_text
