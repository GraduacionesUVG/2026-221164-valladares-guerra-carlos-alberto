"""División del banco congelado en DESARROLLO (50) y PRUEBA (50).

Estratificada por categoría con semilla fija. Las decisiones de diseño se
toman solo con desarrollo; prueba se usa una única vez en la evaluación final.
Guarda el SHA-256 del banco: si el banco cambia, el split deja de ser válido.

    .venv/bin/python -m eval.make_split
"""
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

EVAL = Path(__file__).parent
BANK = EVAL / "testbench.jsonl"
SPLIT = EVAL / "split.json"
SEED = 42
N_DEV = 50


def bank_sha256() -> str:
    return hashlib.sha256(BANK.read_bytes()).hexdigest()


def load_split(name: str) -> set[str]:
    """IDs de 'dev' o 'test'; falla si el banco cambió después de congelarlo."""
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    if split["testbench_sha256"] != bank_sha256():
        raise SystemExit("testbench.jsonl cambió después de crear split.json")
    return set(split[name])


def main():
    if SPLIT.exists():
        raise SystemExit("split.json ya existe; la división no se rehace.")
    rows = [json.loads(line) for line in BANK.open(encoding="utf-8")]
    assert all(r["reviewed"] for r in rows), "el banco debe estar revisado y congelado"
    rng = random.Random(SEED)
    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r["id"])

    # Asignación proporcional por categoría (método del mayor residuo)
    total = len(rows)
    quotas = {c: len(ids) * N_DEV / total for c, ids in by_cat.items()}
    n_dev = {c: int(q) for c, q in quotas.items()}
    for c in sorted(quotas, key=lambda c: (quotas[c] - n_dev[c], c), reverse=True)[:N_DEV - sum(n_dev.values())]:
        n_dev[c] += 1

    dev, test = [], []
    for c in sorted(by_cat):
        ids = sorted(by_cat[c])
        rng.shuffle(ids)
        dev += ids[:n_dev[c]]
        test += ids[n_dev[c]:]
    split = {
        "seed": SEED,
        "testbench_sha256": bank_sha256(),
        "by_category": {c: {"dev": n_dev[c], "test": len(by_cat[c]) - n_dev[c]} for c in sorted(by_cat)},
        "dev": sorted(dev),
        "test": sorted(test),
    }
    SPLIT.write_text(json.dumps(split, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"dev={len(dev)} test={len(test)}", split["by_category"])


if __name__ == "__main__":
    main()
