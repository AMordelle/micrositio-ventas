from pipeline.vision_extractor.normalize import normalize_item


def test_normalize_item_from_regular_price_sale_price_with_calculated_discount():
    item = {
        "sku": 12345,
        "title": "Producto",
        "regular_price": 100,
        "sale_price": 85,
        "discount_style": "calculated",
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


def test_normalize_item_from_discount_string():
    item = {
        "sku": "999",
        "discount": "Más del 15% de descuento",
    }

    normalized = normalize_item(item, page_num=16)

    assert normalized["discount_badge"] == {
        "style": "fixed",
        "text": "MÁS DEL 15% DE DESCUENTO",
        "percent": 15,
    }
