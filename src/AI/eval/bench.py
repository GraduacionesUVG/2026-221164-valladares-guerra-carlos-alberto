"""Latencia por etapa y prueba de carga del motor de IA desplegado.

Usa las preguntas de DESARROLLO (medir tiempos no es una decisión de diseño,
pero así el conjunto de prueba queda intacto) contra el servicio en producción
(http://127.0.0.1:8000, motor de IA en el anfitrión con GPU).

  latencia  una consulta a la vez: mediana y p95 por etapa (clasificación,
            recuperación + reranker, generación) y total.
  carga     N consultas simultáneas (N = 1, 2, 4, 8): throughput y latencia
            percibida por el usuario.

Salida: results/exp/bench.json

Uso:  AI_SERVICE_TOKEN=... python -m eval.bench [--url http://127.0.0.1:8000]
"""
import argparse
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from eval.make_split import load_split  # noqa: E402


def pct(values, q):
    return round(float(np.percentile(values, q)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--levels", default="1,2,4,8")
    args = parser.parse_args()
    headers = {"X-Internal-Token": os.environ.get("AI_SERVICE_TOKEN", "")}
    ids = load_split("dev")
    with open(config.EVAL_DIR / "testbench.jsonl", encoding="utf-8") as f:
        questions = [json.loads(line)["question"] for line in f if json.loads(line)["id"] in ids]
    client = httpx.Client(base_url=args.url, headers=headers, timeout=300)
    settings = client.get("/settings").json()["current"]

    def ask(q):
        t0 = time.perf_counter()
        r = client.post("/query", json={"question": q, "history": []})
        r.raise_for_status()
        return (time.perf_counter() - t0) * 1000, r.json()

    ask(questions[0])  # calentamiento (carga de modelos)
    stages = {"classification": [], "retrieval": [], "generation": [], "total": []}
    for q in questions:
        _, res = ask(q)
        if res["refused"]:
            continue
        for k in stages:
            stages[k].append(res["latency_ms"][k])
    latency = {k: {"mediana": int(statistics.median(v)), "p95": pct(v, 95)} for k, v in stages.items()}
    latency["n"] = len(stages["total"])

    load = []
    for n in map(int, args.levels.split(",")):
        batch = (questions * 4)[: max(2 * n, 8)]
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=n) as pool:
            times = [t for t, _ in pool.map(ask, batch)]
        wall = time.perf_counter() - t0
        load.append({"concurrencia": n, "consultas": len(batch),
                     "throughput_consultas_min": round(len(batch) / wall * 60, 1),
                     "latencia_mediana_ms": int(statistics.median(times)), "latencia_p95_ms": pct(times, 95)})
        print(load[-1])

    out = {"config": {k: settings.get(k) for k in ("top_k", "reranker", "num_ctx", "retrieval_mode")},
           "latencia_por_etapa_ms": latency, "carga": load}
    (config.RESULTS_DIR / "exp" / "bench.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(latency, ensure_ascii=False))


if __name__ == "__main__":
    main()
