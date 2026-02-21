from collections.abc import Iterable
from copy import deepcopy
from typing import Any


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def merge_pages_by_sku(
    page_docs: Iterable[dict[str, Any]],
    catalog: str,
    cycle: str,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_sku: dict[str, dict[str, Any]] = {}
    unmatched_items: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for page_doc in page_docs:
        page_num = page_doc.get("page")
        for item in page_doc.get("items", []):
            sku = item.get("sku")
            if not sku:
                unmatched = deepcopy(item)
                unmatched["page"] = page_num
                unmatched_items.append(unmatched)
                continue

            if sku not in by_sku:
                by_sku[sku] = {
                    "catalog": catalog,
                    "cycle": cycle,
                    "family_id": None,
                    "title": item.get("title"),
                    "variant": item.get("variant"),
                    "size": item.get("size"),
                    "price_regular": item.get("price_regular"),
                    "price_sale_final": item.get("price_sale_final"),
                    "discount_badge": item.get("discount_badge"),
                    "notes": item.get("notes"),
                    "trace": {"pages": [page_num] if page_num is not None else []},
                    "warnings": list(item.get("warnings", [])),
                }
                continue

            merged = by_sku[sku]
            pages = set(merged["trace"]["pages"])
            if page_num is not None:
                pages.add(page_num)
            merged["trace"]["pages"] = sorted(pages)

            if item.get("warnings"):
                warning_set = set(merged.get("warnings", []))
                warning_set.update(item["warnings"])
                merged["warnings"] = sorted(warning_set)

            for field in [
                "title",
                "variant",
                "size",
                "price_regular",
                "price_sale_final",
                "discount_badge",
                "notes",
            ]:
                new_value = item.get(field)
                old_value = merged.get(field)

                if _is_missing(old_value) and not _is_missing(new_value):
                    merged[field] = new_value
                    continue

                if not _is_missing(old_value) and not _is_missing(new_value) and old_value != new_value:
                    conflicts.append(
                        {
                            "sku": sku,
                            "field": field,
                            "first_value": old_value,
                            "new_value": new_value,
                            "pages": sorted(pages),
                        }
                    )

    return by_sku, unmatched_items, conflicts
