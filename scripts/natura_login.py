#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

STORAGE_FILE = Path("storage/natura_state.json")
STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

LOGIN_URL = "https://gsp.natura.com/login?country=MX"

print("🟡 Abriré navegador SIN sesión…")
print("🟡 Por favor inicia sesión SOLO en este dominio:")
print("    https://gsp.natura.com")
print("🟡 NO entres al módulo 'Nuevo Pedido'")
print("🟡 Debes terminar exactamente en:")
print("    https://gsp.natura.com/showcase/natura")
print("🟡 Cuando estés en la página de SHOWCASE, vuelve aquí y presiona ENTER.\n")

input("Presiona ENTER para comenzar…")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    page = context.new_page()
    page.goto(LOGIN_URL, timeout=0)

    input("\n👉 Cuando estés en https://gsp.natura.com/showcase/natura presiona ENTER aquí...")

    print("💾 Guardando sesión…")
    context.storage_state(path=str(STORAGE_FILE))
    print("✅ Sesión guardada correctamente.")

    browser.close()
