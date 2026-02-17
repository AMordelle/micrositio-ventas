# pipeline/parse/parse_products.py
import re

def is_name(line):
    tokens = line.lower()
    if any(x in tokens for x in ["$", "pts", "(", "a:"]):
        return False
    return len(line.split()) >= 2


def is_description(line):
    tokens = line.lower()
    return (
        len(line.split()) >= 3 and
        not any(x in tokens for x in ["$", "pts", "(", "a:"])
    )


def is_code(line):
    return bool(re.search(r"\(\d{5,6}\)", line))


def is_price(line):
    return "$" in line


def is_price_discount(line):
    return "a:" in line.lower() and "$" in line


def is_footer(line):
    tokens = line.lower()
    return (
        "válido hasta agotar existencias" in tokens or
        "valido hasta agotar existencias" in tokens or
        "cofepris" in tokens or
        "salud es belleza" in tokens
    )


def parse_products(blocks):
    products = []

    current = {
        "nombre": [],
        "descripcion": [],
        "codigo": None,
        "puntos": None,
        "precio_normal": None,
        "precio_descuento": None
    }

    state = "nombre"

    for line in blocks:
        line = line.strip()
        if not line or is_footer(line):
            continue

        if state == "nombre":
            if is_name(line):
                current["nombre"].append(line)
                continue
            else:
                state = "descripcion"

        if state == "descripcion":
            if is_description(line):
                current["descripcion"].append(line)
                continue
            else:
                state = "codigo"

        if state == "codigo":
            if is_code(line):
                code_match = re.search(r"\((\d{5,6})\)", line)
                if code_match:
                    current["codigo"] = code_match.group(1)
                pts_match = re.search(r"(\d+)\s*pts", line.lower())
                if pts_match:
                    current["puntos"] = int(pts_match.group(1))
                state = "precios"
                continue
            else:
                continue

        if state == "precios":
            if is_price_discount(line):
                current["precio_descuento"] = float(line.lower().split("$")[1])
            elif is_price(line):
                current["precio_normal"] = float(line.split("$")[1])

            if current["codigo"] and current["precio_descuento"] is not None:
                current["nombre"] = " ".join(current["nombre"]).strip()
                current["descripcion"] = " ".join(current["descripcion"]).strip()

                products.append(current)

                current = {
                    "nombre": [],
                    "descripcion": [],
                    "codigo": None,
                    "puntos": None,
                    "precio_normal": None,
                    "precio_descuento": None
                }
                state = "nombre"

    return products
