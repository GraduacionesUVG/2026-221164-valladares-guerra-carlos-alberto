"""Validación humana del juez LLM (concordancia humano–juez).

  sheet   genera eval/human/hoja_calificacion.csv: 30 respuestas del conjunto
          de prueba (10 por condición A, B y C), mezcladas y anónimas, con la
          consulta y el artículo oficial. El evaluador llena fidelidad,
          relevancia y claridad (1–5) sin saber qué sistema respondió.
          La clave (qué condición es cada fila y qué nota dio el juez) queda
          aparte en eval/human/clave.json.
  score   lee la hoja llena y calcula la concordancia con el juez: kappa de
          Cohen ponderada (cuadrática), correlación de Spearman y porcentaje de
          acuerdo exacto y a ±1 punto → results/exp/human_agreement.json

Uso:  python -m eval.human_eval sheet | score
"""
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from eval.eval_generation import article_text  # noqa: E402
from training.common import load_chunks_by_id  # noqa: E402

DIR = config.EVAL_DIR / "human"
SHEET = DIR / "hoja_calificacion.csv"
KEY = DIR / "clave.json"
CRITERIA = ("fidelidad", "relevancia", "claridad")
PER_CONDITION = 10


def sheet():
    gen = json.loads((config.RESULTS_DIR / "exp" / "generation_final_test.json").read_text(encoding="utf-8"))
    chunks = load_chunks_by_id()
    rng = random.Random(2026)
    rows = gen["rows"]
    items = []
    for cond in ("llm_sin_rag", "llm_base_rag", "vialbot"):
        for r in rng.sample(rows, PER_CONDITION):
            c = r["conditions"][cond]
            items.append({"id": r["id"], "condicion": cond, "question": r["question"],
                          "article": article_text(chunks, r["expected_article"]),
                          "answer": c["answer"], "juez": {k: c[k] for k in CRITERIA}})
    rng.shuffle(items)
    DIR.mkdir(exist_ok=True)
    with SHEET.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "consulta", "articulo_oficial", "respuesta",
                    "fidelidad_1a5", "relevancia_1a5", "claridad_1a5"])
        for n, it in enumerate(items, 1):
            w.writerow([n, it["question"], it["article"][:1500], it["answer"], "", "", ""])
    KEY.write_text(json.dumps([{"n": n, **{k: it[k] for k in ("id", "condicion", "juez")}}
                               for n, it in enumerate(items, 1)], indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"{len(items)} respuestas → {SHEET.relative_to(config.BASE_DIR)}")


def score():
    import numpy as np
    from scipy.stats import spearmanr
    from sklearn.metrics import cohen_kappa_score

    key = {k["n"]: k for k in json.loads(KEY.read_text(encoding="utf-8"))}
    with SHEET.open(encoding="utf-8-sig") as f:
        filled = [r for r in csv.DictReader(f) if r["fidelidad_1a5"].strip()]
    out = {"n": len(filled)}
    for c in CRITERIA:
        human = [int(r[f"{c}_1a5"]) for r in filled]
        judge = [key[int(r["n"])]["juez"][c] for r in filled]
        diff = np.abs(np.array(human) - np.array(judge))
        out[c] = {
            "kappa_ponderada": round(float(cohen_kappa_score(human, judge, weights="quadratic")), 3),
            "spearman": round(float(spearmanr(human, judge).statistic), 3),
            "acuerdo_exacto": round(float((diff == 0).mean()), 3),
            "acuerdo_1punto": round(float((diff <= 1).mean()), 3),
            "media_humano": round(float(np.mean(human)), 2),
            "media_juez": round(float(np.mean(judge)), 2),
        }
    (config.RESULTS_DIR / "exp" / "human_agreement.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    {"sheet": sheet, "score": score}[sys.argv[1]]()
