# 📘 Proyecto de Procesamiento Inteligente de PDFs

Este proyecto implementa una herramienta completa para la extracción, análisis y procesamiento avanzado de documentos PDF utilizando Python y un conjunto de librerías especializadas.

Su objetivo es facilitar tareas como:

* Extracción de texto
* Conversión de páginas a imágenes
* OCR automático
* Procesamiento de imágenes
* Limpieza de texto mediante expresiones regulares
* Análisis estructural mediante modelos de datos

---

## 🚀 Objetivos del Proyecto

* Crear una herramienta modular para el manejo inteligente de archivos PDF.
* Establecer una arquitectura limpia y escalable para futuras mejoras.
* Integrar OCR, visión por computadora y análisis de texto.
* Simplificar la instalación, ejecución y mantenimiento del proyecto.

---

## 📂 Arquitectura del Proyecto

```
📁 proyecto-pdf
│
├── 📁 src
│   ├── extractor_pdf.py
│   ├── ocr.py
│   ├── procesado_imagen.py
│   ├── limpieza_texto.py
│   ├── modelos.py
│   └── main.py
│
├── venv/ (entorno virtual)
├── requirements.txt
└── README.md
```

---

## 🧩 Requerimientos

* Python 3.10 o superior
* Pip actualizado
* Windows, Linux o MacOS

---

## ⚙️ Instalación

### 1️⃣ Crear el entorno virtual

```
python -m venv venv
```

### 2️⃣ Activarlo

**Windows (PowerShell):**

```
venv\Scripts\activate
```

### 3️⃣ Instalar dependencias

```
pip install \
    pymupdf \
    pytesseract \
    pdf2image \
    opencv-python \
    regex \
    pydantic \
    python-dotenv \
    rich \
    typer \
    numpy \
    pytest \
    ruff
```

O si usas PowerShell, con backticks:

```
pip install `
    pymupdf `
    pytesseract `
    pdf2image `
    opencv-python `
    regex `
    pydantic `
    python-dotenv `
    rich `
    typer `
    numpy `
    pytest `
    ruff
```

---

## 🔧 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## ▶️ Ejecución del Proyecto

Para correr el módulo principal:

```
python src/main.py
```

---

## 📚 Funcionalidades

### 🔹 Extracción de texto con PyMuPDF

Permite leer texto, metadatos y estructura del PDF.

### 🔹 OCR con Tesseract

Convierte imágenes en texto.

### 🔹 Conversión PDF → Imagen

Utilizando `pdf2image`.

### 🔹 Procesamiento de imágenes

Con `opencv-python`.

### 🔹 Limpieza y normalización de texto

Expresiones regulares mediante `regex`.

### 🔹 Modelos de datos

Estructuras validadas con `pydantic`.

### 🔹 CLI interactiva

Construida en `typer`.

---

## 🧪 Pruebas

Para ejecutar pruebas unitarias:

```
pytest
```

---

## 🧹 Calidad de Código

Para análisis estático:

```
ruff check .
```

---

## 🛣️ Roadmap / Fases del Proyecto

### **Fase 1 — Base del sistema**

* Instalación del entorno
* Arquitectura principal
* Extracción básica de PDFs

### **Fase 2 — OCR y Visión por Computadora**

* Integración con Tesseract
* Procesamiento de imágenes

### **Fase 3 — Limpieza y análisis de texto**

* Normalización semántica
* Modelos estructurados

### **Fase 4 — CLI interactiva y automatización**

* Interfaz por línea de comandos
* Pipeline automatizado

### **Fase 5 — Optimización y despliegue**

* Integración con APIs
* Contenedores (Docker)

---

## 📄 Licencia

Uso interno y educativo.

---

## ✨ Notas Finales

Este proyecto está diseñado para crecer. La arquitectura modular permite añadir nuevos componentes como:

* IA generativa
* Análisis semántico
* Identificación de tablas
* Extracción de entidades

Si deseas, puedo crear también:

* El archivo `requirements.txt`
* La estructura completa del proyecto
* Los módulos Python listos para usar
# 📘 Proyecto de Procesamiento Inteligente de PDFs

Este proyecto implementa una herramienta completa para la extracción, análisis y procesamiento avanzado de documentos PDF utilizando Python y un conjunto de librerías especializadas.

Su objetivo es facilitar tareas como:

* Extracción de texto
* Conversión de páginas a imágenes
* OCR automático
* Procesamiento de imágenes
* Limpieza de texto mediante expresiones regulares
* Análisis estructural mediante modelos de datos

---

## 🚀 Objetivos del Proyecto

* Crear una herramienta modular para el manejo inteligente de archivos PDF.
* Establecer una arquitectura limpia y escalable para futuras mejoras.
* Integrar OCR, visión por computadora y análisis de texto.
* Simplificar la instalación, ejecución y mantenimiento del proyecto.

---

## 📂 Arquitectura del Proyecto

```
📁 proyecto-pdf
│
├── 📁 src
│   ├── extractor_pdf.py
│   ├── ocr.py
│   ├── procesado_imagen.py
│   ├── limpieza_texto.py
│   ├── modelos.py
│   └── main.py
│
├── venv/ (entorno virtual)
├── requirements.txt
└── README.md
```

---

## 🧩 Requerimientos

* Python 3.10 o superior
* Pip actualizado
* Windows, Linux o MacOS

---

## ⚙️ Instalación

### 1️⃣ Crear el entorno virtual

```
python -m venv venv
```

### 2️⃣ Activarlo

**Windows (PowerShell):**

```
venv\Scripts\activate
```

### 3️⃣ Instalar dependencias

```
pip install \
    pymupdf \
    pytesseract \
    pdf2image \
    opencv-python \
    regex \
    pydantic \
    python-dotenv \
    rich \
    typer \
    numpy \
    pytest \
    ruff
```

O si usas PowerShell, con backticks:

```
pip install `
    pymupdf `
    pytesseract `
    pdf2image `
    opencv-python `
    regex `
    pydantic `
    python-dotenv `
    rich `
    typer `
    numpy `
    pytest `
    ruff
```

---

## 🔧 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## ▶️ Ejecución del Proyecto

Para correr el módulo principal:

```
python src/main.py
```

---

## 📚 Funcionalidades

### 🔹 Extracción de texto con PyMuPDF

Permite leer texto, metadatos y estructura del PDF.

### 🔹 OCR con Tesseract

Convierte imágenes en texto.

### 🔹 Conversión PDF → Imagen

Utilizando `pdf2image`.

### 🔹 Procesamiento de imágenes

Con `opencv-python`.

### 🔹 Limpieza y normalización de texto

Expresiones regulares mediante `regex`.

### 🔹 Modelos de datos

Estructuras validadas con `pydantic`.

### 🔹 CLI interactiva

Construida en `typer`.

---

## 🧪 Pruebas

Para ejecutar pruebas unitarias:

```
pytest
```

---

## 🧹 Calidad de Código

Para análisis estático:

```
ruff check .
```

---

## 🛣️ Roadmap / Fases del Proyecto

### **Fase 1 — Base del sistema**

* Instalación del entorno
* Arquitectura principal
* Extracción básica de PDFs

### **Fase 2 — OCR y Visión por Computadora**

* Integración con Tesseract
* Procesamiento de imágenes

### **Fase 3 — Limpieza y análisis de texto**

* Normalización semántica
* Modelos estructurados

### **Fase 4 — CLI interactiva y automatización**

* Interfaz por línea de comandos
* Pipeline automatizado

### **Fase 5 — Optimización y despliegue**

* Integración con APIs
* Contenedores (Docker)

---

## 📄 Licencia

Uso interno y educativo.

---

## ✨ Notas Finales

Este proyecto está diseñado para crecer. La arquitectura modular permite añadir nuevos componentes como:

* IA generativa
* Análisis semántico
* Identificación de tablas
* Extracción de entidades

Si deseas, puedo crear también:

* El archivo `requirements.txt`
* La estructura completa del proyecto
* Los módulos Python listos para usar
