#!/usr/bin/env python3
# scripts/run_pipeline.py
#
# Pipeline completo y definitivo:
# 1) Pregunta o recibe el ciclo actual (ej. 202517)
# 2) Ejecuta extractor de SKUs -> all_skus_<ciclo>.json
# 3) Ejecuta scraper principal (Chrome CDP) -> catalogo_<ciclo>.json + missing_<ciclo>.json
# 4) Ejecuta rescraper automático -> catalogo_<ciclo>_final.json + missing_<ciclo>_final.json
# 5) Reporte final del catálogo completo y productos faltantes

import sys
import subprocess
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
OUTPUT_SKUS_DIR = ROOT / "output" / "skus"
OUTPUT_DATA_DIR = ROOT / "output" / "data"


def run_step(title: str, cmd: list[str]) -> None:
    """ Ejecuta un paso del pipeline mostrando encabezado bonito """
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print(f"▶ Ejecutando: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Error al ejecutar: {' '.join(cmd)}")


def ask_cycle_if_needed(cli_cycle: str | None) -> str:
    """ Obtiene el ciclo ya sea por parámetro o solicitándolo """
    if cli_cycle:
        ciclo = cli_cycle.strip()
    else:
        print("\n🟠 Ingresa el ciclo actual (ej. 202517):")
        ciclo = input("Ciclo: ").strip()

    if not (ciclo.isdigit() and len(ciclo) == 6):
        raise ValueError("Formato de ciclo inválido. Ejemplo válido: 202517")

    return ciclo


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline completo: SKUs -> Scraping -> Rescraping -> Catálogo Final"
    )
    parser.add_argument("--cycle", help="Ciclo actual (ej. 202517).")
    args = parser.parse_args()

    ciclo = ask_cycle_if_needed(args.cycle)

    # Carpetas necesarias
    OUTPUT_SKUS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Archivos clave
    extractor_script = SCRIPTS_DIR / "extract_all_skus.py"
    scraper_script = SCRIPTS_DIR / "scrape_natura_chrome_cdp.py"
    rescraper_script = SCRIPTS_DIR / "rescrape_missing.py"

    skus_file = OUTPUT_SKUS_DIR / f"all_skus_{ciclo}.json"
    catalog_file = OUTPUT_DATA_DIR / f"catalogo_{ciclo}.json"
    missing_file = OUTPUT_DATA_DIR / f"missing_{ciclo}.json"
    final_catalog_file = OUTPUT_DATA_DIR / f"catalogo_{ciclo}_final.json"
    final_missing_file = OUTPUT_DATA_DIR / f"missing_{ciclo}_final.json"

    print("\n📁 Proyecto:", ROOT)
    print("📁 Scripts:", SCRIPTS_DIR)
    print("📁 SKUs:", OUTPUT_SKUS_DIR)
    print("📁 Catálogos:", OUTPUT_DATA_DIR)

    # 1️⃣ EXTRAER SKUs
    run_step(
        "1️⃣ Extrayendo SKUs desde los PDFs (extract_all_skus.py)",
        [
            sys.executable,
            str(extractor_script),
            "--cycle",
            ciclo,
        ],
    )

    if not skus_file.exists():
        raise FileNotFoundError(f"Después de extraer, no encontré {skus_file}")

    # 2️⃣ SCRAPER PRINCIPAL
    print("\n💡 Recuerda:")
    print("   - Chrome DEBE estar abierto con CDP en el puerto 9222")
    print('     Ejemplo (PowerShell):')
    print('       & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
    print("   - Debes iniciar sesión en Natura y abrir en la MISMA pestaña:")
    print("       https://gsp.natura.com/login?country=MX")
    print("     hasta llegar a:")
    print("       https://gsp.natura.com/showcase/natura\n")

    run_step(
        "2️⃣ Scrapeando productos (scrape_natura_chrome_cdp.py)",
        [
            sys.executable,
            str(scraper_script),
            "--input",
            str(skus_file),
            "--cycle",
            ciclo,
        ],
    )

    if not catalog_file.exists():
        raise FileNotFoundError(f"No existe {catalog_file}. El scraper falló.")

    if not missing_file.exists():
        raise FileNotFoundError(f"No existe {missing_file}. Archivo missing no generado.")

    # 3️⃣ RESCRAPER AUTOMÁTICO (segunda vuelta)
    run_step(
        "3️⃣ Segunda vuelta: re-scrapeando SKUs faltantes (rescrape_missing.py)",
        [
            sys.executable,
            str(rescraper_script),
            "--cycle",
            ciclo,
        ],
    )

    if not final_catalog_file.exists():
        raise FileNotFoundError(f"No existe {final_catalog_file}. El rescrape falló.")

    # 🎉 RESUMEN FINAL
    print("\n🎉 PIPELINE COMPLETADO EXITOSAMENTE")
    print("===============================================================")
    print(f"📦 CICLO: {ciclo}")
    print(f"📄 SKUs extraídos:              {skus_file}")
    print(f"📄 Catálogo (1ª vuelta):        {catalog_file}")
    print(f"📄 Missing (1ª vuelta):         {missing_file}")
    print(f"📄 Catálogo FINAL (2 vueltas):  {final_catalog_file}")
    print(f"📄 Missing FINAL:               {final_missing_file}")
    print("===============================================================\n")


if __name__ == "__main__":
    main()
