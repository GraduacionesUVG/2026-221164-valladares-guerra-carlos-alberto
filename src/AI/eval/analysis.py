"""Análisis estadístico de la evaluación final (conjunto de PRUEBA).

A partir de los resultados ya generados (no vuelve a consultar ningún modelo):
  - Intervalos de confianza al 95% por bootstrap (10 000 remuestreos) para la
    curva P@K, el MRR y las métricas de generación.
  - Pruebas pareadas entre condiciones sobre las mismas preguntas: Wilcoxon de
    rangos con signo (escalas 1-5) y McNemar exacta (tasas de cita y alucinación).
  - Taxonomía de errores de la condición final (C).
  - Tabla de ablación / progresión: base → ajuste fino → configuración final.

Salida: results/exp/analysis_test.json

Uso:  python -m eval.analysis
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from eval.eval_boundary import is_refusal as _is_refusal  # noqa: E402

EXP = config.RESULTS_DIR / "exp"
RNG = np.random.default_rng(42)
B = 10_000
KS = range(1, 11)


def load(name: str) -> dict:
    return json.loads((EXP / name).read_text(encoding="utf-8"))


def ci(values, stat=np.mean) -> list[float]:
    values = np.asarray(values, dtype=float)
    idx = RNG.integers(0, len(values), size=(B, len(values)))
    boots = stat(values[idx], axis=1)
    return [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)]


def ranks_from(result: dict, ids: list[str]) -> dict[str, int | None]:
    """Posición del artículo correcto por pregunta (las que no están en
    'failures' quedaron en la posición 1)."""
    failed = {f["id"]: f["rank"] for f in result["failures"]}
    return {i: failed.get(i, 1) for i in ids}


def retrieval_block(result: dict, ids: list[str]) -> dict:
    ranks = ranks_from(result, ids)
    out = {}
    for k in KS:
        hits = [int(r is not None and r <= k) for r in ranks.values()]
        out[f"P@{k}"] = {"value": round(float(np.mean(hits)), 4), "ci95": ci(hits)}
    rr = [1.0 / r if r else 0.0 for r in ranks.values()]
    out["MRR"] = {"value": round(float(np.mean(rr)), 4), "ci95": ci(rr)}
    return out


def mcnemar(a: list[bool], b: list[bool]) -> dict:
    only_a = sum(x and not y for x, y in zip(a, b))
    only_b = sum(y and not x for x, y in zip(a, b))
    n = only_a + only_b
    p = binomtest(only_a, n, 0.5).pvalue if n else 1.0
    return {"solo_primera": only_a, "solo_segunda": only_b, "p": round(float(p), 4)}


def wilcox(a: list[int], b: list[int]) -> dict:
    d = np.asarray(b) - np.asarray(a)
    if not np.any(d):
        return {"dif_media": 0.0, "p": 1.0}
    res = wilcoxon(a, b, zero_method="wilcox")
    return {"dif_media": round(float(d.mean()), 3), "mejor": int((d > 0).sum()),
            "igual": int((d == 0).sum()), "peor": int((d < 0).sum()), "p": round(float(res.pvalue), 4)}


def is_refusal(answer: str) -> bool:
    # Mismo criterio que las pruebas de límites
    return _is_refusal({"refused": None, "answer": answer})


def taxonomy(rows: list[dict]) -> dict:
    """Clasifica cada respuesta de la condición C en una sola categoría."""
    cats = {"correcta": [], "parcial": [], "rechazo_indebido": [],
            "fallo_recuperacion": [], "alucinacion_con_articulo": []}
    for r in rows:
        c = r["conditions"]["vialbot"]
        in_ctx = r["expected_article"] in c["sources"]
        if is_refusal(c["answer"]):
            cat = "rechazo_indebido"
        elif c["fidelidad"] >= 4:
            cat = "correcta"
        elif not in_ctx:
            cat = "fallo_recuperacion"
        elif c["fidelidad"] <= 2:
            cat = "alucinacion_con_articulo"
        else:
            cat = "parcial"
        cats[cat].append({"id": r["id"], "question": r["question"],
                          "expected": r["expected_article"], "fidelidad": c["fidelidad"],
                          "cita_correcta": c["cita_correcta"], "answer": c["answer"]})
    n = len(rows)
    return {k: {"n": len(v), "pct": round(len(v) / n, 4), "casos": v} for k, v in cats.items()}


def main():
    split = json.loads((config.EVAL_DIR / "split.json").read_text(encoding="utf-8"))
    ids = split["test"]
    dense = load("retrieval_final_dense_test.json")
    final = load("retrieval_final_bge_test.json")
    gen = load("generation_final_test.json")
    base_c = load("generation_baseline_test.json")

    out = {"n": len(ids), "bootstrap": B, "retrieval": {
        "embedder_base_denso": retrieval_block(dense["base"], ids),
        "embedder_propio_denso": retrieval_block(dense["vialbot"], ids),
        "embedder_propio_bge": retrieval_block(final["vialbot"], ids),
    }}

    # Retrieval: McNemar sobre acierto en P@7 entre configuraciones consecutivas
    def hit7(res):
        r = ranks_from(res, ids)
        return [r[i] is not None and r[i] <= 7 for i in ids]
    out["retrieval_tests"] = {
        "P@7 base→propio": mcnemar(hit7(dense["base"]), hit7(dense["vialbot"])),
        "P@7 propio→propio+bge": mcnemar(hit7(dense["vialbot"]), hit7(final["vialbot"])),
    }

    rows = {r["id"]: r for r in gen["rows"]}
    brows = {r["id"]: r for r in base_c["rows"]}
    order = sorted(rows)
    conds = {"A": ("llm_sin_rag", rows), "B": ("llm_base_rag", rows),
             "C0": ("vialbot", brows), "C": ("vialbot", rows)}

    def col(cond, key):
        name, src = conds[cond]
        return [src[i]["conditions"][name][key] for i in order]

    gen_ci = {}
    for cond in conds:
        fid = col(cond, "fidelidad")
        gen_ci[cond] = {
            "fidelidad": {"value": round(float(np.mean(fid)), 3), "ci95": ci(fid)},
            "relevancia": {"value": round(float(np.mean(col(cond, "relevancia"))), 3),
                           "ci95": ci(col(cond, "relevancia"))},
            "claridad": {"value": round(float(np.mean(col(cond, "claridad"))), 3),
                         "ci95": ci(col(cond, "claridad"))},
            "cita_correcta": {"value": round(float(np.mean(col(cond, "cita_correcta"))), 3),
                              "ci95": ci([int(x) for x in col(cond, "cita_correcta")])},
            "alucinacion_grave": {"value": round(float(np.mean([f <= 2 for f in fid])), 3),
                                  "ci95": ci([int(f <= 2) for f in fid])},
            "latencia_ms_mediana": int(np.median(col(cond, "latency_ms"))),
        }
    out["generation"] = gen_ci

    tests = {}
    for a, b in (("A", "C"), ("B", "C"), ("C0", "C"), ("A", "B")):
        tests[f"{a}→{b}"] = {
            **{k: wilcox(col(a, k), col(b, k)) for k in ("fidelidad", "relevancia", "claridad")},
            "cita_correcta": mcnemar(col(a, "cita_correcta"), col(b, "cita_correcta")),
            "alucinacion_grave": mcnemar([f <= 2 for f in col(a, "fidelidad")],
                                         [f <= 2 for f in col(b, "fidelidad")]),
        }
    out["generation_tests"] = tests
    out["taxonomy_C"] = taxonomy([rows[i] for i in order])

    (EXP / "analysis_test.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                            encoding="utf-8")
    for name, block in out["retrieval"].items():
        print(f"{name:24} P@7 {block['P@7']['value']:.2f} {block['P@7']['ci95']}  MRR {block['MRR']['value']:.3f} {block['MRR']['ci95']}")
    for cond, m in gen_ci.items():
        print(cond, {k: (v["value"], v["ci95"]) if isinstance(v, dict) else v for k, v in m.items()})
    for name, t in tests.items():
        print(name, {k: (v.get("dif_media", ""), v["p"]) for k, v in t.items()})
    print("taxonomía C:", {k: v["n"] for k, v in out["taxonomy_C"].items()})


if __name__ == "__main__":
    main()
