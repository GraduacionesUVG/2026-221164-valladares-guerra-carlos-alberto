"""Fase I: ingesta, preprocesamiento y limpieza de datos.

Extrae el texto de los PDF oficiales y aplica rutinas de limpieza con
expresiones regulares: encabezados y números de página repetidos, saltos de
línea del PDF, espacios anómalos y caracteres invisibles. El resultado se
guarda en data/processed/<id>.txt en UTF-8.

Uso:  python -m pipeline.extract
"""
import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

# Líneas de ruido que se repiten en cada página de los PDF oficiales
NOISE_LINES = [
    re.compile(r"^REGLAMENTO DE TRANSITO\s*$"),
    re.compile(r"^BIBLIOTECA DIGITAL PARA LA ADMINISTRACI[OÓ]N FINANCIERA\s*$"),
    re.compile(r"^\d{1,3}\s*$"),  # números de página
]

# Correcciones puntuales de defectos de las fuentes oficiales, verificadas a
# mano contra el PDF. Son pares (expresión regular, reemplazo).
SOURCE_FIXES = {
    "ley": [
        # El PDF omite el encabezado del artículo 23 al inicio del Título VI
        (r"(TITULO VI\s*\nVía Publica\s*\n+)Vía publica\. ", r"\1Artículo 23. Vía publica. "),
    ],
    "reglamento": [
        (r"Tr ánsito", "Tránsito"),
        (r"Artículo\. 67\.", "Artículo 67."),
        # Artículos 26 y 109: falta el punto después del número
        (r"(?m)^(Artículo (?:26|109)) (?=[A-Z])", r"\1. "),
    ],
}


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # Caracteres invisibles y espacios no estándar
    text = re.sub("[\u200b\u200c\u200d\ufeff\u00ad]", "", text)
    text = text.replace("\u00a0", " ").replace("\t", " ")
    return text


def clean_page(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(p.match(stripped) for p in NOISE_LINES):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def reflow(text: str) -> str:
    """Une las líneas cortadas por el PDF preservando los inicios estructurales
    (artículos, títulos, capítulos, incisos y literales)."""
    structural = re.compile(
        r"^(Art[íi]culo\s+\d+|ART[ÍI]CULO\s+\d+|T[ÍI]TULO\s+[IVXLC]+|CAP[ÍI]TULO\s+(?:[IVXLC]+|[ÚU]NICO)|"
        r"\d{1,3}\)|[a-zñ]\)|[a-zñ]\.\s|\d{1,2}\.\s)"
    )
    out: list[str] = []
    for line in text.splitlines():
        if not line:
            out.append("")
            continue
        # Un inciso numerado solo ("39)") se une con la línea siguiente
        if out and re.fullmatch(r"\d{1,3}\)", out[-1].strip()):
            out[-1] = out[-1].strip() + " " + line
            continue
        if out and out[-1] and not structural.match(line) and not out[-1].isupper():
            out[-1] = out[-1] + " " + line
        else:
            out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{2,}", "\n", text)
    return text


def clean_text(text: str) -> str:
    text = normalize_unicode(text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" +([,;:])", r"\1", text)
    return text.strip()


def apply_fixes(doc_id: str, text: str) -> str:
    for pattern, replacement in SOURCE_FIXES.get(doc_id, []):
        text, n = re.subn(pattern, replacement, text)
        if n == 0:
            print(f"[extract] aviso: corrección no aplicada en {doc_id}: {pattern!r}")
    return text


def extract_document(pdf_path: Path, doc_id: str) -> str:
    doc = pymupdf.open(pdf_path)
    pages = [clean_page(page.get_text()) for page in doc]
    text = "\n".join(pages)
    text = clean_text(normalize_unicode(text))
    text = apply_fixes(doc_id, text)
    text = reflow(text)
    return clean_text(text)


def main():
    config.ensure_dirs()
    for meta in config.DOCUMENTS:
        pdf_path = config.RAW_DIR / meta["file"]
        if not pdf_path.exists():
            raise FileNotFoundError(f"Falta el documento {pdf_path}")
        text = extract_document(pdf_path, meta["id"])
        out = config.PROCESSED_DIR / f"{meta['id']}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"[extract] {meta['short']}: {len(text):,} caracteres -> {out.name}")


if __name__ == "__main__":
    main()
