# pipeline/parse/parser_combo.py

import re
from .parser_base import ParserBase

RE_SKU = re.compile(r"\(\s*(\d{3,7})\s*\)")
RE_PRICE = re.compile(r"\$?\s*(\d{2,5}(?:[.,]\d{2})?)")

class ParserCombo(ParserBase):

    def parse(self, page_text: str, page_meta: dict) -> list:
        lines = [self.clean_line(l) for l in page_text.splitlines() if l.strip()]
        if not lines:
            return []

        text = "\n".join(lines)
        # quitar SKUs para no confundirlos con precio
        text_no_sku = RE_SKU.sub("", text)

        combo_items = []
        for ln in lines:
            m = RE_SKU.search(ln)
            if m:
                combo_items.append(m.group(1))

        # precio del combo: tomamos el precio más grande razonable
        prices = []
        for m in RE_PRICE.finditer(text_no_sku):
            val = float(m.group(1).replace(",", "."))
            if val < 20:
                continue
            prices.append(val)

        price = max(prices) if prices else None

        # nombre del combo: primera línea que no sea puro texto legal
        name = None
        for ln in lines:
            if any(k in ln.lower() for k in ["promoción válida", "cofepris"]):
                continue
            name = ln
            break

        return [{
            "sku": None,
            "name": name or "Combo/Set",
            "combo_items": combo_items,
            "price": price,
            "price_before": None,
            "source_page": page_meta["page"],
            "detected_type": "COMBO",
        }]
