# pipeline/parse/page_router.py

from .parser_product_simple import ParserProductSimple
from .parser_tones_list import ParserTonesList
from .parser_combo import ParserCombo
from .parser_de_to_a import ParserDeToA
from .parser_holistic_life import ParserHolisticLife

class PageRouter:

    def __init__(self):
        self.parsers = {
            "PRODUCT_SIMPLE": ParserProductSimple(),
            "TONES_LIST": ParserTonesList(),
            "COMBO": ParserCombo(),
            "DE_TO_A": ParserDeToA(),
            "PROMO_BANNER": None,
            "UNKNOWN": None
        }

    def parse_page(self, page_text: str, page_meta: dict, pdf_name: str):
        """
        page_meta = {"page": int, "detected_type": "..."}
        """
        t = page_meta["detected_type"]

        # Holistic Life: parser especial
        if "Holistic" in pdf_name:
            return ParserHolisticLife().parse(page_text, page_meta)

        parser = self.parsers.get(t)

        if parser is None:
            return []  # Banners, unknown, páginas de sección, etc.

        return parser.parse(page_text, page_meta)
