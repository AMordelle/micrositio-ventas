# pipeline/parse/parser_holistic_life.py

from .parser_base import ParserBase
import re

RE_PRICE = re.compile(r"\$?\s*(\d{2,5}(?:[.,]\d{2})?)")

class ParserHolisticLife(ParserBase):

    def parse(self, page_text: str, page_meta: dict) -> list:
        lines = [self.clean_line(l) for l in page_text.splitlines() if l.strip()]
        products = []

        buffer = {"name": "", "description": ""}

        for ln in lines:
            # Precio aproximado
            m = RE_PRICE.search(ln)
            if m:
                buffer["price"] = float(m.group(1).replace(",", "."))

            # Heurística simple: línea larga = nombre
            if len(ln.split()) >= 3 and "ml" not in ln.lower():
                if not buffer.get("name"):
                    buffer["name"] = ln
                else:
                    buffer["description"] += " " + ln

        if buffer["name"]:
            buffer["source_page"] = page_meta["page"]
            buffer["detected_type"] = "HOLISTIC"
            products.append(buffer)

        return products
