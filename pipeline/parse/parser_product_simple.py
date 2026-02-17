# pipeline/parse/parser_product_simple.py

import re
from .parser_base import ParserBase

RE_SKU = re.compile(r"\(\s*(\d{3,7})\s*\)")
RE_POINTS = re.compile(r"(\d+)\s*pts", re.I)
RE_PRICE = re.compile(r"\$?\s*(\d{2,5}(?:[.,]\d{2})?)")
RE_POINTS_PRICE_LINE = re.compile(
    r"(\d+)\s*pts.*?\$?\s*(\d{2,5}(?:[.,]\d{2})?)",
    re.I
)

class ParserProductSimple(ParserBase):
    """
    Parser v2 para páginas clasificadas como PRODUCT_SIMPLE.
    Trabaja con ventanas locales alrededor de cada SKU para evitar mezclar productos.
    """

    def parse(self, page_text: str, page_meta: dict) -> list:
        lines = [self.clean_line(l) for l in page_text.splitlines() if l.strip()]
        products = []

        if not lines:
            return products

        # Índices donde encontramos SKUs
        sku_indices = []
        for idx, ln in enumerate(lines):
            if RE_SKU.search(ln):
                sku_indices.append(idx)

        # Si no hay SKU, tratamos toda la página como un solo producto "suave"
        if not sku_indices:
            prod = self._parse_block_as_single_product(lines, page_meta)
            return [prod] if prod else []

        # Para cada SKU, analizamos una ventana local de contexto
        for idx in sku_indices:
            window_start = max(0, idx - 4)
            window_end = min(len(lines), idx + 5)
            block_lines = lines[window_start:window_end]

            sku = RE_SKU.search(lines[idx]).group(1)

            product = self._parse_block_for_sku(
                sku=sku,
                block_lines=block_lines,
                sku_line_index=idx - window_start,
                page_meta=page_meta,
            )
            if product:
                products.append(product)

        return products

    # ----------------- helpers -----------------

    def _parse_block_for_sku(
        self,
        sku: str,
        block_lines: list,
        sku_line_index: int,
        page_meta: dict,
    ) -> dict | None:
        """
        block_lines: ventana alrededor del SKU
        sku_line_index: índice del SKU dentro de block_lines
        """
        name = None
        description_parts = []
        price = None
        points = None

        # 1) Precio + puntos: primero intentamos en una sola línea
        for ln in block_lines:
            m = RE_POINTS_PRICE_LINE.search(ln)
            if m:
                points = int(m.group(1))
                price = float(m.group(2).replace(",", "."))
                break

        # Si no encontramos, buscamos por separado
        if price is None or points is None:
            for ln in block_lines:
                if points is None:
                    p = RE_POINTS.search(ln)
                    if p:
                        points = int(p.group(1))

                if price is None and "$" in ln:
                    pr = RE_PRICE.search(ln)
                    if pr:
                        price_val = float(pr.group(1).replace(",", "."))
                        # Filtrar números absurdamente bajos
                        if price_val >= 20:
                            price = price_val

        # 2) Nombre: líneas inmediatamente arriba del SKU
        # Buscamos la primera línea "limpia" antes del SKU
        for i in range(sku_line_index - 1, -1, -1):
            cand = block_lines[i]
            if self._looks_like_title(cand):
                name = cand
                break

        # Si aún no hay nombre, tomar la línea anterior sin símbolos obvios
        if not name and sku_line_index > 0:
            name = block_lines[sku_line_index - 1]

        # 3) Descripción: líneas después del SKU que no sean puro precio/pts
        for i in range(sku_line_index + 1, len(block_lines)):
            ln = block_lines[i]
            if self._is_mostly_price_or_points(ln):
                continue
            description_parts.append(ln)

        description = " ".join(description_parts).strip() if description_parts else None

        product = {
            "sku": sku,
            "name": name,
            "description": description,
            "price": price,
            "points": points,
            "variants": [],
            "combo_items": [],
            "source_page": page_meta["page"],
            "detected_type": "PRODUCT_SIMPLE",
        }

        # Si no hay ni nombre ni precio, probablemente ruido
        if not product["name"] and product["price"] is None:
            return None

        return product

    def _parse_block_as_single_product(self, lines: list, page_meta: dict) -> dict | None:
        """
        Fallback para páginas sin SKU: un solo producto estimado.
        """
        price = None
        points = None
        name = None
        description_parts = []

        for ln in lines:
            if points is None:
                pts = RE_POINTS.search(ln)
                if pts:
                    points = int(pts.group(1))
            if price is None and "$" in ln:
                pr = RE_PRICE.search(ln)
                if pr:
                    val = float(pr.group(1).replace(",", "."))
                    if val >= 20:
                        price = val

        # Nombre: primera línea que parece título
        for ln in lines:
            if self._looks_like_title(ln):
                name = ln
                break

        # Descripción: resto de líneas sin precio/pts
        for ln in lines:
            if ln == name:
                continue
            if self._is_mostly_price_or_points(ln):
                continue
            description_parts.append(ln)

        description = " ".join(description_parts).strip() if description_parts else None

        if not name and price is None:
            return None

        return {
            "sku": None,
            "name": name,
            "description": description,
            "price": price,
            "points": points,
            "variants": [],
            "combo_items": [],
            "source_page": page_meta["page"],
            "detected_type": "PRODUCT_SIMPLE",
        }

    def _looks_like_title(self, line: str) -> bool:
        # Evitar líneas claramente de precio / pts / descuentos
        if any(k in line.lower() for k in ["pts", "$", "%", "descuento", "oferta", "cualquiera por"]):
            return False
        # No queremos líneas con solo 1 palabra muy corta
        tokens = line.split()
        if len(tokens) < 2:
            return False
        # Aceptar si la mayoría son letras
        alpha_chars = sum(ch.isalpha() for ch in line)
        return alpha_chars / max(len(line), 1) > 0.5

    def _is_mostly_price_or_points(self, line: str) -> bool:
        ln = line.lower()
        if "pts" in ln or "$" in ln or "%" in ln:
            return True
        if RE_PRICE.search(line):
            return True
        return False
