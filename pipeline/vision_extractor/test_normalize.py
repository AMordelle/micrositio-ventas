from pipeline.vision_extractor.normalize import normalize_item


def test_normalize_item_discount_calculated_only_when_no_explicit_text():
    item = {
        "sku": 12345,
        "title": "Producto",
        "regular_price": 100,
        "sale_price": 85,
        "discount": "calculated",
    }

    normalized = normalize_item(item, page_num=14)

    assert normalized["sku"] == "12345"
    assert normalized["price_regular"] == 100
    assert normalized["price_sale_final"] == 85
    assert normalized["discount_badge"] == {
        "style": "calculated",
        "text": "15% DE DESCUENTO",
        "percent": 15,
    }


def test_normalize_item_from_regular_sale_without_discount():
    item = {
        "sku": "A-1",
        "regular": 250,
        "sale": 199,
    }

    normalized = normalize_item(item, page_num=15)

    assert normalized["price_regular"] == 250
    assert normalized["price_sale_final"] == 199
    assert normalized["discount_badge"] is None


def test_normalize_item_discount_string_mas_del():
    item = {
        "sku": "999",
        "discount": "Más del 45% de descuento",
    }

    normalized = normalize_item(item, page_num=16)

    assert normalized["discount_badge"] == {
        "style": "upto",
        "text": "MÁS DEL 45% DE DESCUENTO",
        "percent": 45,
    }


def test_normalize_item_discount_string_hasta():
    item = {
        "sku": "1000",
        "discount": "Hasta 40% de descuento",
    }

    normalized = normalize_item(item, page_num=17)

    assert normalized["discount_badge"] == {
        "style": "upto",
        "text": "HASTA 40% DE DESCUENTO",
        "percent": 40,
    }


def test_normalize_item_discount_string_fixed_percent():
    item = {
        "sku": "1001",
        "discount": "35% de descuento",
    }

    normalized = normalize_item(item, page_num=18)

    assert normalized["discount_badge"] == {
        "style": "fixed",
        "text": "35% DE DESCUENTO",
        "percent": 35,
    }


def test_normalize_item_prefers_explicit_text_over_calculated_flag():
    item = {
        "sku": "1002",
        "regular_price": 200,
        "sale_price": 100,
        "discount": "Más del 45% de descuento",
        "discount_style": "calculated",
    }

    normalized = normalize_item(item, page_num=19)

    assert normalized["discount_badge"]["style"] == "upto"
    assert normalized["discount_badge"]["percent"] == 45


def test_normalize_item_adds_warning_when_calculated_without_prices():
    item = {
        "sku": "1003",
        "discount": "calculated",
    }

    normalized = normalize_item(item, page_num=20)

    assert normalized["discount_badge"] is None
    assert "DISCOUNT_TEXT_MISSING" in normalized["warnings"]
