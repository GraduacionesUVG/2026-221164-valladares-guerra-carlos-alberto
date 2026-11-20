"""Utilidades compartidas por los scripts de entrenamiento."""
import json
import random

import config


def load_chunks_by_id() -> dict[str, dict]:
    with open(config.PROCESSED_DIR / "chunks.jsonl", encoding="utf-8") as f:
        return {c["id"]: c for c in map(json.loads, f)}


def load_qa_pairs() -> list[dict]:
    """Aplana el dataset en pares pregunta-respuesta con su fragmento. Usa la
    versión verificada si existe (ver generate_dataset verify)."""
    pairs = []
    verified = config.DATASET_DIR / "synthetic_qa_verified.jsonl"
    path = verified if verified.exists() else config.DATASET_DIR / "synthetic_qa.jsonl"
    with open(path, encoding="utf-8") as f:
        for record in map(json.loads, f):
            for item in record["items"]:
                pairs.append({
                    "question": item["pregunta"].strip(),
                    "answer": item["respuesta"].strip(),
                    "chunk_id": record["chunk_id"],
                    "article_key": record["article_key"],
                    "reference": record["reference"],
                    "topic": record["topic"],
                })
    return pairs


def load_ood_messages() -> list[str]:
    path = config.DATASET_DIR / "out_of_domain.jsonl"
    msgs = []
    with open(path, encoding="utf-8") as f:
        for record in map(json.loads, f):
            msgs.extend(record["messages"])
    return msgs


def load_testbench_questions() -> set[str]:
    path = config.EVAL_DIR / "testbench.jsonl"
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["question"].strip().lower() for line in f}


def split_by_chunk(pairs: list[dict], val_ratio: float = 0.1, seed: int = 42):
    """Divide en entrenamiento/validación por pregunta, garantizando que ninguna
    pregunta del banco de pruebas se use para entrenar."""
    banned = load_testbench_questions()
    pairs = [p for p in pairs if p["question"].lower() not in banned]
    rng = random.Random(seed)
    rng.shuffle(pairs)
    n_val = int(len(pairs) * val_ratio)
    return pairs[n_val:], pairs[:n_val]
