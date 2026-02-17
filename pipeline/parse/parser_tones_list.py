# pipeline/parse/parser_tones_list.py

import re
from .parser_base import ParserBase

RE_SKU = re.compile(r"\(\s*(\d{3,7})\s*\)")
RE_POINTS = re.compile(r"(\d+)\s*pts", re.I)
RE_PRICE = re.compile(r"\$?\s*(\d{2,5}(?:[.,]\d{2})?)")

class ParserTonesList(ParserBase):
    """
    Parser v2 para páginas TONES_LIST (labiales, bases, etc).
    - Toma precio/puntos del encabezado.
    - Cada SKU se convierte en un "tono" con nombre propio.
    """

    def parse(self, page_text: str, page_meta: dict) -> list:
        lines = [self.clean_line(l) for l in page_text.splitlines() if l.strip()]
        products = []

        if not lines:
            return products

        # Índices de líneas con SKU
        sku_indices = [i for i, ln in enumerate(lines) if RE_SKU.search(ln)]
        if not sku_indices:
            return products

        first_sku_idx = sku_indices[0]
        header_lines = lines[:first_sku_idx]

        price_general, points_general = self._extract_header_price_points(header_lines)

        for idx in sku_indices:
            sku_line = lines[idx]
            m = RE_SKU.search(sku_line)
            sku = m.group(1)

            tone_name = self._infer_tone_name(lines, idx)
            products.append({
                "sku": sku,
                "name": tone_name,
                "price": price_general,
                "points": points_general,
                "variants": [],
                "source_page": page_meta["page"],
                "detected_type": "TONES_LIST",
            })

        return products

    # ---------------- helpers ----------------

    def _extract_header_price_points(self, header_lines: list) -> tuple[float | None, int | None]:
        """
        Extrae precio y puntos del encabezado:
        - Ignora números dentro de paréntesis (SKUs).
        - Prefiere números con símbolo $.
        - Filtra precios demasiado pequeños (2, 5, 10).
        """
        text = "\n".join(header_lines)
        # Quitar SKUs tipo (123456)
        text_no_sku = RE_SKU.sub("", text)

        price_candidates = []
        points = None

        for ln in text_no_sku.splitlines():
            # puntos
            if points is None:
                p = RE_POINTS.search(ln)
                if p:
                    points = int(p.group(1))

            # precios
            for m in RE_PRICE.finditer(ln):
                raw = m.group(1)
                # saltar cosas muy cortas tipo 2, 5, 10
                try:
                    val = float(raw.replace(",", "."))
                except ValueError:
                    continue
                if val < 20:
                    continue
                # si hay símbolo $, darle peso extra (pero aquí solo los apilamos)
                price_candidates.append(val)

        price = price_candidates[-1] if price_candidates else None
        return price, points

    def _infer_tone_name(self, lines: list, sku_idx: int) -> str | None:
        """
        Busca el nombre de tono justo antes del SKU.
        """
        # Miramos máximo 2 líneas hacia atrás
        for offset in range(1, 3):
            i = sku_idx - offset
            if i < 0:
                break
            cand = lines[i]
            if self._is_valid_tone_name_candidate(cand):
                return cand
        return None

    def _is_valid_tone_name_candidate(self, line: str) -> bool:
        ln = line.lower()
        if any(k in ln for k in ["pts", "$", "%", "descuento", "oferta", "cualquiera por"]):
            return False
        if "(" in ln or ")" in ln:
            return False
        tokens = line.split()
        if not tokens:
            return False
        # Evitar nombres tipo "13 pts"
        if len(tokens) == 2 and tokens[1].lower().startswith("pts"):
            return False
        # Al menos una palabra alfabética
        alpha_tokens = [t for t in tokens if any(ch.isalpha() for ch in t)]
        return len(alpha_tokens) >= 1
