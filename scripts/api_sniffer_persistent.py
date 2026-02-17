#!/usr/bin/env python3
# scripts/api_sniffer_persistent.py
# Sniffer persistente: no se cierra hasta que tú cierres el navegador manualmente.

from playwright.sync_api import sync_playwright

TARGET_URL = "https://gsp.natura.com/showcase/natura"

def main():
    print("\n======================================")
    print("   🚀 Sniffer persistente NATURA")
    print("======================================")
    print("1. Se abrirá el navegador.")
    print("2. Inicia sesión manualmente.")
    print("3. Ve al buscador de productos.")
    print("4. Escribe un SKU para disparar la API.")
    print("5. Aquí verás todas las peticiones JSON.")
    print("6. El sniffer NO se cerrará hasta que cierres el navegador.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        # Escuchar todas las peticiones que devuelvan JSON
        def handle_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "application/json" in ct:
                    print("\n--------------------------------------")
                    print(f"🌐 URL: {response.url}")
                    print("--------------------------------------")
                    print(response.json())
            except:
                pass

        context.on("response", handle_response)

        print(f"\n🌍 Abriendo: {TARGET_URL}")
        page.goto(TARGET_URL)

        print("\n🕒 El sniffer está activo permanentemente.")
        print("💡 Cierra el navegador para terminar.\n")

        # Mantener bloqueado hasta que el usuario cierre Chrome manualmente
        page.wait_for_event("close")

    print("\n🧩 Sniffer finalizado.\n")


if __name__ == "__main__":
    main()
