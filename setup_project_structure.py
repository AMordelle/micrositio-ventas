import os
from pathlib import Path

# ===============================
#  CONFIGURACIÓN DEL PROYECTO
# ===============================

PROJECT_ROOT = Path("micrositio-ventas")

FOLDERS = [
    "input_pdfs",
    "pipeline/extract",
    "pipeline/clean",
    "pipeline/parse",
    "pipeline/utils",
    "pipeline/models",
    "output",
    "output/logs",
    "output/previews",
    "config",
    "frontend/public",
    "frontend/src",
    "scripts"
]

FILES = {
    "README.md": "# Micrositio de Ventas\n\nProyecto generado automáticamente.\n",
    ".gitignore": """
# Python
__pycache__/
*.pyc
venv/
.env

# Node
node_modules/
.next/
dist/

# Output
output/logs/
output/previews/

# OS Files
.DS_Store
Thumbs.db
""",
    "requirements.txt": "",
    "pipeline/__init__.py": "",
    "scripts/watcher.py": "# Placeholder: Watcher de PDFs nuevos.\n",
    "scripts/update_catalogs.py": "# Placeholder: actualizador de campañas.\n",
    "input_pdfs/README.md": "# Coloca aquí los catálogos PDF.\n",
}

# ===============================
#  CREACIÓN
# ===============================

def create_structure():
    if PROJECT_ROOT.exists():
        print(f"⚠️ La carpeta '{PROJECT_ROOT}' ya existe. No se realizará la creación para evitar sobrescritura.")
        return

    print(f"🚀 Creando estructura de proyecto en: {PROJECT_ROOT}/\n")
    PROJECT_ROOT.mkdir()

    # Crear carpetas
    for folder in FOLDERS:
        path = PROJECT_ROOT / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Carpeta creada: {path}")

    # Crear archivos
    for filepath, content in FILES.items():
        full_path = PROJECT_ROOT / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        print(f"📄 Archivo creado: {full_path}")

    print("\n🎉 Estructura creada exitosamente.")


if __name__ == "__main__":
    create_structure()
