import fitz
import pytesseract
import cv2

print("PyMuPDF OK:", fitz.__doc__[:15])
print("Tesseract OK:", pytesseract.get_tesseract_version())
print("OpenCV OK:", cv2.__version__)