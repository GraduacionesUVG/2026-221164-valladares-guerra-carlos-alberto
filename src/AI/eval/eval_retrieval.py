"""Métricas cuantitativas de recuperación sobre el banco de pruebas.

Para cada consulta del banco se conoce el artículo que la responde. Se mide,
a nivel de artículo (varios fragmentos del mismo artículo cuentan una vez):

  Precision@K  proporción de consultas cuyo artículo correcto aparece entre
               los K primeros resultados (en la literatura de IR también se
               le llama Hit Rate@K o Recall@K cuando hay un solo relevante).
               Se reporta la curva completa, K = 1..10.
  MRR          Mean Reciprocal Rank: promedio de 1/posición del artículo
               correcto (0 si no aparece en los primeros 10).

Se comparan el modelo de embeddings base y el modelo propio (fine-tuning), con
la estrategia de recuperación indicada (densa, híbrida, con o sin reranker).

Uso:
  python -m eval.eval_retrieval                         # banco completo → results/retrieval.json
  python -m eval.eval_retrieval --split dev --tag base  # → results/exp/retrieval_base_dev.json
  python -m eval.eval_retrieval --split dev --mode hybrid --reranker bge-m3 --tag hyb_bge
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import chromadb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from eval.make_split import load_split  # noqa: E402
from service.rag import Retriever  # noqa: E402

KS = tuple(range(1, 11))
DEPTH = 10


def load_testbench(split: str = "all") -> list[dict]:
    with open(config.EVAL_DIR / "testbench.jsonl", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    if split == "all":
        return rows
    ids = load_split(split)
    return [r for r in rows if r["id"] in ids]


def ranked_articles(retriever: Retriever, question: str, **search) -> list[str]:
    hits = retriever.search(question, k=DEPTH * 2, **search)
    seen: list[str] = []
    for h in hits:
        if h["article_key"] not in seen:
            seen.append(h["article_key"])
    return seen[:DEPTH]


def evaluate(retriever: Retriever, testbench: list[dict], **search) -> dict:
    hits_at = {k: 0 for k in KS}
    rr_sum = 0.0
    per_category: dict[str, list[float]] = {}
    failures, latencies = [], []
    ranked_articles(retriever, testbench[0]["question"], **search)  # carga de modelos
    for case in testbench:
        t0 = time.perf_counter()
        ranking = ranked_articles(retriever, case["question"], **search)
        latencies.append((time.perf_counter() - t0) * 1000)
        expected = case["expected_article"]
        rank = ranking.index(expected) + 1 if expected in ranking else None
        for k in KS:
            hits_at[k] += int(rank is not None and rank <= k)
        rr = 1.0 / rank if rank else 0.0
        rr_sum += rr
        per_category.setdefault(case["category"], []).append(rr)
        if rank != 1:
            failures.append({"id": case["id"], "question": case["question"],
                             "expected": expected, "rank": rank, "top3": ranking[:3]})
    n = len(testbench)
    return {
        "n": n,
        **{f"precision@{k}": round(hits_at[k] / n, 4) for k in KS},
        "mrr": round(rr_sum / n, 4),
        "latencia_ms_mediana": round(statistics.median(latencies), 1),
        "mrr_by_category": {c: round(sum(v) / len(v), 4) for c, v in sorted(per_category.items())},
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all")
    parser.add_argument("--mode", choices=["dense", "hybrid"], default="dense")
    parser.add_argument("--reranker", default=None, help="clave de service.rag.RERANKERS")
    parser.add_argument("--candidates", type=int, default=20, help="candidatos para el reranker")
    parser.add_argument("--embedders", default="base,vialbot")
    parser.add_argument("--tag", default=None, help="nombre del experimento (guarda en results/exp/)")
    args = parser.parse_args()

    testbench = load_testbench(args.split)
    reranker = None if args.reranker in (None, "none") else args.reranker
    search = dict(mode=args.mode, reranker=reranker, candidates=args.candidates)
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    names = {c.name for c in client.list_collections()}
    wanted = args.embedders.split(",")
    results = {"split": args.split, "config": search}
    if "base" in wanted and config.COLLECTION_BASE in names:
        results["base"] = {"embedder": config.BASE_EMBEDDER,
                           **evaluate(Retriever(use_finetuned=False), testbench, **search)}
    if "vialbot" in wanted and config.COLLECTION_FINETUNED in names:
        results["vialbot"] = {"embedder": "vialbot-embedder (fine-tuning propio)",
                              **evaluate(Retriever(use_finetuned=True), testbench, **search)}

    if args.tag:
        out = config.RESULTS_DIR / "exp" / f"retrieval_{args.tag}_{args.split}.json"
    elif args.split == "all" and args.mode == "dense" and not args.reranker:
        out = config.RESULTS_DIR / "retrieval.json"
    else:
        raise SystemExit("Los experimentos requieren --tag (no se sobrescribe retrieval.json)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[{args.split} n={len(testbench)}] {search}")
    print(f"{'Modelo':<9}" + "".join(f"{'P@' + str(k):>6}" for k in KS) + f"{'MRR':>7}{'ms':>7}")
    for name in ("base", "vialbot"):
        if name in results:
            r = results[name]
            print(f"{name:<9}" + "".join(f"{r[f'precision@{k}']:>6.2f}" for k in KS)
                  + f"{r['mrr']:>7.3f}{r['latencia_ms_mediana']:>7.0f}")
    print(f"→ {out.relative_to(config.BASE_DIR)}")


if __name__ == "__main__":
    main()
