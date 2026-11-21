"""Fase III: representación vectorial (embeddings) e indexación en ChromaDB.

Vectoriza cada fragmento con un modelo de embeddings y lo guarda en una
colección de ChromaDB configurada con distancia coseno. Se construyen dos
colecciones para poder comparar ambos modelos en la evaluación:

  - ley_transito_base     -> modelo pre-entrenado sin ajustar
  - ley_transito_vialbot  -> modelo propio (fine-tuning), si ya fue entrenado

Uso:  python -m pipeline.build_index [--only base|vialbot]
"""
import argparse
import json
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

METADATA_KEYS = ("doc_id", "doc_title", "article", "article_key", "heading",
                 "titulo", "capitulo", "part", "parts", "reference")


def load_chunks() -> list[dict]:
    path = config.PROCESSED_DIR / "chunks.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def build_collection(client, name: str, model_path: str, chunks: list[dict]):
    model = SentenceTransformer(model_path)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    collection = client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine", "embedding_model": str(model_path)},
    )
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=32, normalize_embeddings=True,
                              show_progress_bar=True)
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[{k: c[k] for k in METADATA_KEYS} for c in chunks],
    )
    print(f"[index] {name}: {collection.count()} vectores de {embeddings.shape[1]} dimensiones")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["base", "vialbot"])
    args = parser.parse_args()

    config.ensure_dirs()
    chunks = load_chunks()
    client = get_client()

    if args.only in (None, "base"):
        build_collection(client, config.COLLECTION_BASE, config.BASE_EMBEDDER, chunks)
    if args.only in (None, "vialbot"):
        if config.FINETUNED_EMBEDDER_DIR.exists():
            build_collection(client, config.COLLECTION_FINETUNED,
                             str(config.FINETUNED_EMBEDDER_DIR), chunks)
        else:
            print("[index] modelo propio aún no entrenado; se omite ley_transito_vialbot")


if __name__ == "__main__":
    main()
