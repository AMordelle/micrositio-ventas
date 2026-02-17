# pipeline/parse/parser_base.py

from abc import ABC, abstractmethod

class ParserBase(ABC):
    """
    Clase base para todos los parsers.
    Todos retornan una lista de productos estandarizados (dict).
    """

    @abstractmethod
    def parse(self, page_text: str, page_meta: dict) -> list:
        """
        Retorna:
        [
            {
                "sku": "...",
                "name": "...",
                "description": "...",
                "price": ...,
                "price_before": ...,
                "discount_percent": ...,
                "points": ...,
                "variants": [...],
                "combo_items": [...],
                "brand": "...",
                "category": "...",
                "source_page": n
            }
        ]
        """
        pass

    def clean_line(self, line: str) -> str:
        """Limpieza simple para todas las implementaciones."""
        return line.strip().replace("  ", " ")
