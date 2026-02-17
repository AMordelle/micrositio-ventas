# scripts/natura_sniffer.py

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

STORAGE_FILE = Path("storage/natura_state.json")

# Ejemplo de URL de búsqueda que pasaste
SEARCH_URL = "https://gsp.natura.com/showcase/pesquisa?q=151023&ciclo=202516"

def main():
    if not STORAGE_FILE.exists():
        print(f"❌ No se encontró {STORAGE_FILE}. Corre primero natura_login.py")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(STORAGE_FILE))

        # Handler para ver todas las respuestas JSON
        def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
            except Exception:
                ct = ""

            if "application/json" in ct:
                url = response.url
                try:
                    body = response.json()
                except Exception:
                    try:
                        body_text = response.text()
                        # Intentar parsear como JSON igual
                        body = json.loads(body_text)
                    except Exception:
                        body = None

                print("\n=== JSON detectado ===")
                print("URL:", url)
                if body is not None:
                    # Imprimir solo una parte si es muuuy largo
                    snippet = json.dumps(body, indent=2, ensure_ascii=False)
                    print(snippet[:2000], "...\n")
                else:
                    print("(No se pudo parsear el cuerpo como JSON)\n")

        context.on("response", on_response)

        page = context.new_page()
        print(f"Abriendo búsqueda: {SEARCH_URL}")
        page.goto(SEARCH_URL)

        print("\n⏳ Esperando unos segundos para que carguen las peticiones...")
        page.wait_for_timeout(8000)

        print("\n✅ Listo. Cierra el navegador cuando termines.")
        browser.close()

if __name__ == "__main__":
    main()
