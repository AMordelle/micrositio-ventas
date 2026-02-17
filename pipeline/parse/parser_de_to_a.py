# pipeline/parse/parser_de_to_a.py

import re
from .parser_base import ParserBase

RE_SKU = re.compile(r"\(\s*(\d{3,7})\s*\)")
RE_DE = re.compile(r"\bDe\b[:\s]*\$?\s*(\d{2,5}(?:[.,]\d{2})?)", re.I)
RE_A = re.compile(r"\bA\b[:\s]*\$?\s*(\d{2,5}(?:[.,]\d{2})?)", re.I)
RE_PERCENT = re.compile(r"(\d{1,3})\s*%", re.I)
RE_PRICE = re.compile(r"\$?\s*(\d{2,5}(?:[.,]\d{2})?)")

class ParserDeToA(ParserBase):

    def parse(self, page_text: str, page_meta: dict) -> list:
        lines = [self.clean_line(l) for l in page_text.splitlines() if l.strip()]

        # Remover SKUs para no confundirlos con precios
        text_no_sku = RE_SKU.sub("", "\n".join(lines))

        price_before = None
        price_after = None
        discount = None
        sku = None

        # Intento 1: usar patrones explícitos De/A
        m_de = RE_DE.search(text_no_sku)
        m_a = RE_A.search(text_no_sku)
        if m_de:
            val = float(m_de.group(1).replace(",", "."))
            if val >= 20:
                price_before = val
        if m_a:
            val = float(m_a.group(1).replace(",", "."))
            if val >= 20:
                price_after = val

        # Intento 2: si falta alguno, usar heurística de mayores precios
        if price_before is None or price_after is None:
            prices = []
            for m in RE_PRICE.finditer(text_no_sku):
                val = float(m.group(1).replace(",", "."))
                if val < 20:
                    continue
                prices.append(val)

            prices = sorted(set(prices))
            if len(prices) >= 2:
                # asumimos before = mayor, after = penúltimo
                price_before = prices[-1]
                price_after = prices[-2]
            elif len(prices) == 1:
                price_after = prices[0]

        # porcentaje
        for ln in lines:
            p = RE_PERCENT.search(ln)
            if p:
                discount = int(p.group(1))
                break

        # SKU (si lo hay)
        for ln in lines:
            m = RE_SKU.search(ln)
            if m:
                sku = m.group(1)
                break

        # nombre y descripción: de forma simple
        name = None
        description_parts = []
        for ln in lines:
            if not name and not any(k in ln.lower() for k in ["de ", " a ", "$", "%", "pts"]):
                name = ln
            else:
                description_parts.append(ln)

        description = " ".join(description_parts).strip() if description_parts else None

        return [{
            "sku": sku,
            "name": name,
            "description": description,
            "price": price_after,
            "price_before": price_before,
            "discount_percent": discount,
            "source_page": page_meta["page"],
            "detected_type": "DE_TO_A",
        }]
