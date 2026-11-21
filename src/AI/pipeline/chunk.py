"""Fase II: segmentación semántica (chunking).

La unidad de análisis es el artículo. Cada artículo se convierte en un
fragmento con metadatos (documento, número, título del artículo, título y
capítulo de la ley). Solo los artículos más largos que CHUNK_MAX_CHARS se
subdividen en fragmentos con traslape; la división se hace en límites de
inciso o de oración y cada subfragmento conserva el encabezado del artículo,
de modo que ningún fragmento pierde su referencia legal.

Salida: data/processed/chunks.jsonl y data/processed/articles.jsonl

Uso:  python -m pipeline.chunk
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

ARTICLE_RE = re.compile(r"^Art[íi]culo\s+(\d+)\.\s*(.*)$")
TITLE_RE = re.compile(r"^T[ÍI]TULO\s+([IVXLC]+)\s*$")
CHAPTER_RE = re.compile(r"^CAP[ÍI]TULO\s+([IVXLC]+|[ÚU]NICO)\s*$")


def split_heading(first_line: str) -> tuple[str, str]:
    """'Multas. Se impondrá...' -> ('Multas', 'Se impondrá...')"""
    m = re.match(r"^([^.]{2,120}?)\.\s*(.*)$", first_line)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", first_line.strip()


def parse_articles(doc_id: str, text: str) -> list[dict]:
    articles: list[dict] = []
    current = None
    titulo = capitulo = ""
    pending_label = None  # la línea siguiente a TITULO/CAPITULO es su nombre
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if m := TITLE_RE.match(line):
            titulo, pending_label = f"Título {m.group(1)}", "titulo"
            continue
        if m := CHAPTER_RE.match(line):
            capitulo, pending_label = f"Capítulo {m.group(1)}", "capitulo"
            continue
        if pending_label and not ARTICLE_RE.match(line):
            if pending_label == "titulo":
                titulo = f"{titulo}: {line}"
                capitulo = ""
            else:
                capitulo = f"{capitulo}: {line}"
            pending_label = None
            continue
        pending_label = None
        if m := ARTICLE_RE.match(line):
            if current:
                articles.append(current)
            heading, body = split_heading(m.group(2))
            current = {
                "doc_id": doc_id,
                "article": int(m.group(1)),
                "heading": heading,
                "titulo": titulo,
                "capitulo": capitulo,
                "lines": [body] if body else [],
            }
        elif current:
            current["lines"].append(line)
    if current:
        articles.append(current)

    for a in articles:
        a["text"] = "\n".join(a.pop("lines")).strip()
    return articles


def split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    """Divide en límites de línea (incisos) y, si hace falta, de oración."""
    units: list[str] = []
    for line in text.split("\n"):
        if len(line) <= max_chars:
            units.append(line)
        else:
            units.extend(s for s in re.split(r"(?<=[.;])\s+", line) if s)

    parts: list[str] = []
    buf = ""
    for u in units:
        if buf and len(buf) + len(u) + 1 > max_chars:
            parts.append(buf)
            # traslape: se arrastra la cola del fragmento anterior
            tail = buf[-overlap:]
            cut = tail.find(" ")
            buf = (tail[cut + 1:] if cut >= 0 else tail) + "\n" + u
        else:
            buf = f"{buf}\n{u}" if buf else u
    if buf:
        parts.append(buf)
    return parts


def build_chunks(articles: list[dict], doc_meta: dict) -> list[dict]:
    chunks = []
    for a in articles:
        ref = f"{doc_meta['short']}, Artículo {a['article']}"
        header = f"{ref}. {a['heading']}." if a["heading"] else f"{ref}."
        parts = split_long(a["text"], config.CHUNK_MAX_CHARS, config.CHUNK_OVERLAP_CHARS)
        for i, part in enumerate(parts):
            chunks.append({
                "id": f"{a['doc_id']}-art{a['article']}-{i}",
                "doc_id": a["doc_id"],
                "doc_title": doc_meta["title"],
                "article": a["article"],
                "article_key": f"{a['doc_id']}:{a['article']}",
                "heading": a["heading"],
                "titulo": a["titulo"],
                "capitulo": a["capitulo"],
                "part": i,
                "parts": len(parts),
                "reference": ref,
                # Texto que se vectoriza y se entrega al LLM como contexto
                "text": f"{header}\n{part}",
            })
    return chunks


def main():
    config.ensure_dirs()
    all_articles, all_chunks = [], []
    for meta in config.DOCUMENTS:
        text = (config.PROCESSED_DIR / f"{meta['id']}.txt").read_text(encoding="utf-8")
        articles = parse_articles(meta["id"], text)
        chunks = build_chunks(articles, meta)
        all_articles.extend(articles)
        all_chunks.extend(chunks)
        sizes = [len(c["text"]) for c in chunks]
        print(
            f"[chunk] {meta['short']}: {len(articles)} artículos -> {len(chunks)} fragmentos "
            f"(promedio {sum(sizes) // len(sizes)} car., máx {max(sizes)})"
        )

    with open(config.PROCESSED_DIR / "articles.jsonl", "w", encoding="utf-8") as f:
        for a in all_articles:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    with open(config.PROCESSED_DIR / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"[chunk] total: {len(all_articles)} artículos, {len(all_chunks)} fragmentos")


if __name__ == "__main__":
    main()
