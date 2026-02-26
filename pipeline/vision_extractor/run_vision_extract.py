from __future__ import annotations

import argparse
import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

import fitz

MODEL = "gpt-4.1"
RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass
class PageResult:
    page: int
    items: list[dict[str, Any]]
    error: str | None = None


def parse_skip_pages(value: str | None) -> set[int]:
    if not value:
        return set()
    pages: set[int] = set()
    for chunk in value.split(","):
        token = chunk.strip()
        if not token:
            continue
        pages.add(int(token))
    return pages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vision extractor por página de PDF")
    parser.add_argument("--pdf", required=True, help="Ruta al PDF")
    parser.add_argument("--catalog", required=True, help="Nombre catálogo")
    parser.add_argument("--cycle", required=True, help="Ciclo")
    parser.add_argument("--start-page", type=int, default=1, help="Página inicial (1-index)")
    parser.add_argument("--end-page", type=int, default=None, help="Página final (1-index)")
    parser.add_argument("--skip-pages", default="", help="Lista CSV de páginas a saltar (1-index)")
    parser.add_argument("--allow-partial", action="store_true", help="Generar by_sku.json aunque haya errores")
    parser.add_argument("--save-images", action="store_true", help="Guardar PNG renderizado de cada página")
    parser.add_argument("--only-discount-pages", action="store_true", help="Filtrar y extraer solo páginas candidatas por criterio visual")
    return parser.parse_args()


def load_context(context_path: Path) -> str:
    return context_path.read_text(encoding="utf-8").strip()


def page_to_png_bytes(pdf_path: Path, page_index_zero_based: int) -> bytes:
    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_index_zero_based)
        pix = page.get_pixmap(dpi=220)
        return pix.tobytes("png")


def extract_response_text(response_json: dict[str, Any]) -> str:
    if isinstance(response_json.get("output_text"), str):
        return response_json["output_text"].strip()

    outputs = response_json.get("output") or []
    texts: list[str] = []
    for output in outputs:
        for content in output.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                texts.append(content["text"])
    return "\n".join(texts).strip()


def validate_item(item: dict[str, Any]) -> None:
    expected_item_keys = {
        "sku",
        "title",
        "variant",
        "size",
        "prices",
        "discount_badge",
        "points",
    }
    if set(item.keys()) != expected_item_keys:
        raise ValueError("item keys inválidas")

    if not isinstance(item["sku"], str):
        raise ValueError("sku debe ser string")

    for nullable_text in ("title", "variant", "size"):
        value = item[nullable_text]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{nullable_text} debe ser string|null")

    prices = item["prices"]
    if not isinstance(prices, dict) or set(prices.keys()) != {"currency", "regular", "sale"}:
        raise ValueError("prices inválido")

    if prices["currency"] != "MXN":
        raise ValueError("currency debe ser MXN")

    for number_key in ("regular", "sale"):
        if prices[number_key] is not None and not isinstance(prices[number_key], (int, float)):
            raise ValueError(f"{number_key} debe ser number|null")

    badge = item["discount_badge"]
    if badge is not None:
        if not isinstance(badge, dict) or set(badge.keys()) != {"text", "percent", "kind"}:
            raise ValueError("discount_badge inválido")
        if not isinstance(badge["text"], str):
            raise ValueError("discount_badge.text inválido")
        if badge["percent"] is not None and not isinstance(badge["percent"], int):
            raise ValueError("discount_badge.percent inválido")
        if badge["kind"] not in {"exact", "more_than", "up_to"}:
            raise ValueError("discount_badge.kind inválido")

    if item["points"] is not None and not isinstance(item["points"], int):
        raise ValueError("points debe ser int|null")


def validate_page_schema(payload: dict[str, Any], expected_page: int) -> dict[str, Any]:
    if set(payload.keys()) != {"page", "items"}:
        raise ValueError("page schema keys inválidas")

    if payload["page"] != expected_page:
        raise ValueError("page debe coincidir con página procesada")

    items = payload["items"]
    if not isinstance(items, list):
        raise ValueError("items debe ser lista")

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("item debe ser objeto")
        validate_item(item)

    return payload


def is_suspicious_sku(sku: str) -> bool:
    if not sku.isdigit():
        return True
    if len(sku) > 6:
        return True
    if " " in sku or "-" in sku:
        return True
    return False


def contains_repuesto(title: str | None) -> bool:
    if not title:
        return False
    return "repuesto" in title.lower()


def apply_repuesto_title_normalization(items: list[dict[str, Any]]) -> None:
    for item in items:
        title = item.get("title")
        variant = item.get("variant")
        if (
            isinstance(title, str)
            and title.strip().lower() == "repuesto"
            and isinstance(variant, str)
            and len(variant.strip()) >= 10
        ):
            item["title"] = f"Repuesto {variant.strip()}"
            item["variant"] = None


def detect_guardrail_issues(items: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []

    if any(is_suspicious_sku(str(item.get("sku", ""))) for item in items):
        reasons.append("suspicious_sku")

    principal_skus = {
        item["sku"]
        for item in items
        if isinstance(item.get("sku"), str) and not contains_repuesto(item.get("title"))
    }
    repuesto_skus = {
        item["sku"]
        for item in items
        if isinstance(item.get("sku"), str) and contains_repuesto(item.get("title"))
    }

    if principal_skus.intersection(repuesto_skus):
        reasons.append("repuesto_principal_overlap")

    if any(
        contains_repuesto(item.get("title")) and is_suspicious_sku(str(item.get("sku", ""))) for item in items
    ):
        reasons.append("repuesto_suspicious_sku")

    return reasons


def build_guardrail_instruction(reasons: list[str]) -> str:
    instructions: list[str] = []
    if "suspicious_sku" in reasons:
        instructions.append(
            "Relee SOLO los SKUs de la página y devuélvelos exactamente como aparecen impresos "
            "(números entre paréntesis). No agregues dígitos."
        )
    if "repuesto_principal_overlap" in reasons or "repuesto_suspicious_sku" in reasons:
        instructions.append(
            "Los SKUs del producto principal no pueden aparecer como Repuesto. "
            "Extrae Repuesto SOLO de la sección rotulada 'Repuesto'. "
            "No inventes SKUs. Si un SKU no es legible, omite el item completo."
        )
        instructions.append(
            "Para Repuesto, devuelve pares (variant, sku) respetando el orden de la lista impresa; "
            "no cruces filas."
        )
    return " ".join(instructions)



def call_vision_quick_scan(context: str, page_number: int, image_png_bytes: bytes) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurado")

    prompt = (
        "Analiza visualmente la página completa y responde SOLO JSON válido sin markdown con este schema exacto: "
        '{"page": <int>, "has_percent": <bool>, "has_price": <bool>, "has_de_a_pattern": <bool>, "should_extract": <bool>}. '
        "No uses semántica de palabras; usa solo patrones visuales. "
        "should_extract debe ser has_percent AND has_price AND has_de_a_pattern."
    )

    image_b64 = base64.b64encode(image_png_bytes).decode("utf-8")
    body = {
        "model": MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": context}]},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                ],
            },
        ],
    }

    req = request.Request(
        RESPONSES_URL,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            data = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Error HTTP quick scan en Responses API: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Error de red quick scan en Responses API: {exc}") from exc

    response_json = json.loads(data)
    output_text = extract_response_text(response_json)
    if not output_text:
        raise RuntimeError("Quick scan no devolvió output_text")

    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Quick scan JSON inválido: {exc}") from exc

    expected_keys = {"page", "has_percent", "has_price", "has_de_a_pattern", "should_extract"}
    if not isinstance(payload, dict) or set(payload.keys()) != expected_keys:
        raise RuntimeError("Quick scan schema inválido")

    if payload["page"] != page_number:
        raise RuntimeError("Quick scan page inválido")

    for key in ("has_percent", "has_price", "has_de_a_pattern", "should_extract"):
        if not isinstance(payload[key], bool):
            raise RuntimeError(f"Quick scan campo inválido: {key}")

    expected_should_extract = payload["has_percent"] and payload["has_price"] and payload["has_de_a_pattern"]
    payload["should_extract"] = expected_should_extract
    return payload

def call_vision(
    context: str,
    page_number: int,
    image_png_bytes: bytes,
    extra_instruction: str | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurado")

    schema_hint = {
        "page": page_number,
        "items": [
            {
                "sku": "string",
                "title": "string|null",
                "variant": "string|null",
                "size": "string|null",
                "prices": {"currency": "MXN", "regular": "number|null", "sale": "number|null"},
                "discount_badge": {"text": "string", "percent": "int|null", "kind": "exact|more_than|up_to"},
                "points": "int|null",
            }
        ],
    }

    prompt = (
        "Extrae SOLO datos visibles de esta página completa. "
        "No uses OCR por bloques ni coordenadas. "
        "Responde ÚNICAMENTE JSON válido sin markdown y con este schema exacto: "
        + json.dumps(schema_hint, ensure_ascii=False)
    )
    if extra_instruction:
        prompt = f"{prompt} {extra_instruction}"

    image_b64 = base64.b64encode(image_png_bytes).decode("utf-8")
    body = {
        "model": MODEL,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": context}]},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                ],
            },
        ],
    }

    req = request.Request(
        RESPONSES_URL,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode("utf-8"),
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            data = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 400:
            input_summary: list[dict[str, Any]] = []
            for msg in body.get("input", []):
                content = msg.get("content", [])
                input_summary.append(
                    {
                        "role": msg.get("role"),
                        "content_types": [item.get("type") for item in content],
                        "content_keys": [sorted(item.keys()) for item in content],
                    }
                )
            raise RuntimeError(
                "Error HTTP 400 en Responses API. "
                f"input_summary={json.dumps(input_summary, ensure_ascii=False)} detail={detail}"
            ) from exc
        raise RuntimeError(f"Error HTTP en Responses API: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Error de red en Responses API: {exc}") from exc

    response_json = json.loads(data)
    output_text = extract_response_text(response_json)
    if not output_text:
        raise RuntimeError("Responses API no devolvió output_text")

    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"La salida de Vision no fue JSON válido: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("La salida JSON de Vision debe ser objeto")

    return payload


def consolidate_by_sku(page_results: list[PageResult]) -> list[dict[str, Any]]:
    by_sku: dict[str, dict[str, Any]] = {}
    for result in sorted(page_results, key=lambda p: p.page):
        for item in result.items:
            # Política explícita: último SKU visto reemplaza objeto completo.
            by_sku[item["sku"]] = item
    return [by_sku[sku] for sku in sorted(by_sku.keys())]


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    context_path = Path(__file__).with_name("vision_context.md")
    context = load_context(context_path)

    output_dir = Path("output") / "vision" / args.catalog / args.cycle
    output_dir.mkdir(parents=True, exist_ok=True)
    pages_image_dir = output_dir / "pages"
    if args.save_images:
        pages_image_dir.mkdir(parents=True, exist_ok=True)

    skip_pages = parse_skip_pages(args.skip_pages)

    page_results: list[PageResult] = []
    pages_error = 0
    pages_ok = 0
    pages_selected: list[int] = []
    pages_skipped_filter: list[int] = []

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)

    start_page = max(1, args.start_page)
    end_page = args.end_page if args.end_page is not None else total_pages
    end_page = min(end_page, total_pages)

    if start_page > end_page:
        raise ValueError("Rango de páginas inválido")

    for page_number in range(start_page, end_page + 1):
        if page_number in skip_pages:
            continue

        page_file = output_dir / f"page_{page_number:04d}.json"
        page_image_file = pages_image_dir / f"page_{page_number:04d}.png"
        page_index = page_number - 1

        error_message: str | None = None
        validated: dict[str, Any] | None = None

        try:
            image_png = page_to_png_bytes(pdf_path, page_index)
            if args.save_images:
                page_image_file.write_bytes(image_png)
            print(f"page={page_number} render_ok bytes={len(image_png)}")
        except Exception as exc:  # noqa: BLE001
            error_message = f"render_failed page={page_number} error={exc}"
            print(error_message)
            pages_error += 1
            fallback = {"page": page_number, "items": []}
            page_file.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
            page_results.append(PageResult(page=page_number, items=[], error=error_message))
            continue

        if args.only_discount_pages:
            try:
                quick_scan = call_vision_quick_scan(context, page_number, image_png)
                print(
                    "page="
                    f"{page_number} quick_scan should_extract={quick_scan['should_extract']} "
                    f"percent={quick_scan['has_percent']} price={quick_scan['has_price']} "
                    f"de_a={quick_scan['has_de_a_pattern']}"
                )
            except Exception as exc:  # noqa: BLE001
                error_message = f"vision_failed page={page_number} quick_scan error={exc}"
                print(error_message)
                pages_error += 1
                fallback = {"page": page_number, "items": []}
                page_file.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
                page_results.append(PageResult(page=page_number, items=[], error=error_message))
                continue

            if not quick_scan["should_extract"]:
                pages_skipped_filter.append(page_number)
                fallback = {"page": page_number, "items": []}
                page_file.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"page={page_number} skipped_by_filter")
                pages_ok += 1
                page_results.append(PageResult(page=page_number, items=[]))
                continue
            pages_selected.append(page_number)

        for attempt in range(2):
            try:
                payload = call_vision(context, page_number, image_png)
                print(f"page={page_number} vision_ok")
                validated = validate_page_schema(payload, page_number)
                print(f"page={page_number} json_valid")
                break
            except Exception as exc:  # noqa: BLE001
                error_message = f"vision_failed page={page_number} attempt={attempt + 1} error={exc}"
                print(error_message)
                if attempt == 1:
                    break

        if validated is None:
            pages_error += 1
            fallback = {"page": page_number, "items": []}
            page_file.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
            page_results.append(PageResult(page=page_number, items=[], error=error_message))
            continue

        guardrail_reasons = detect_guardrail_issues(validated["items"])
        if guardrail_reasons:
            print(f"page={page_number} guardrail_retry_triggered reasons={','.join(guardrail_reasons)}")
            extra_instruction = build_guardrail_instruction(guardrail_reasons)
            try:
                retry_payload = call_vision(
                    context,
                    page_number,
                    image_png,
                    extra_instruction=extra_instruction,
                )
                print(f"page={page_number} vision_ok guardrail_retry")
                retry_validated = validate_page_schema(retry_payload, page_number)
                print(f"page={page_number} json_valid guardrail_retry")
                validated = retry_validated
            except Exception as exc:  # noqa: BLE001
                print(f"page={page_number} guardrail_retry_failed error={exc}")

            post_retry_reasons = detect_guardrail_issues(validated["items"])
            if post_retry_reasons:
                print(
                    f"page={page_number} warning_guardrail_unresolved reasons={','.join(post_retry_reasons)}"
                )

        apply_repuesto_title_normalization(validated["items"])

        page_file.write_text(json.dumps(validated, ensure_ascii=False, indent=2), encoding="utf-8")
        if not validated["items"]:
            print(f"page={page_number} no_items_detected (valid)")
        pages_ok += 1
        page_results.append(PageResult(page=page_number, items=validated["items"]))

    if args.only_discount_pages:
        filter_report = {
            "total_pages": len(page_results),
            "pages_selected": pages_selected,
            "pages_skipped": pages_skipped_filter,
        }
        filter_report_path = output_dir / "filter_report.json"
        filter_report_path.write_text(json.dumps(filter_report, ensure_ascii=False, indent=2), encoding="utf-8")

    if pages_error == 0 or args.allow_partial:
        by_sku_items = consolidate_by_sku(page_results)
        by_sku_path = output_dir / "by_sku.json"
        by_sku_path.write_text(json.dumps(by_sku_items, ensure_ascii=False, indent=2), encoding="utf-8")

    if len(page_results) != pages_ok + pages_error:
        raise RuntimeError("Inconsistencia en conteo de páginas: pages_processed != pages_ok + pages_error")

    summary = {
        "pages_processed": len(page_results),
        "pages_ok": pages_ok,
        "pages_error": pages_error,
        "output_dir": str(output_dir),
        "by_sku_generated": pages_error == 0 or args.allow_partial,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
