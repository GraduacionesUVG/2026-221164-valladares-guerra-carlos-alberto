"""Calibración del umbral del clasificador de dominio (in_domain_threshold).

Usa un conjunto propio, eval/calibration_domain.jsonl, distinto de las pruebas
de límites y del banco. Para cada consulta reproduce las etapas previas al LLM
del servicio: filtro de seguridad, clasificador de dominio y umbral de
similitud de la recuperación. Criterio fijado antes de medir (EXPERIMENTOS.md):
el umbral de 0.50 a 0.95 con mayor rechazo fuera de dominio y falsos rechazos
≤ 5% en los controles; en empate, el más bajo.

Salida: results/exp/calibration_threshold.json

Uso:  python -m eval.calibrate_threshold
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from service import runtime_config as rc  # noqa: E402
from service.rag import ADVERSARIAL_RE, RagEngine  # noqa: E402

GRID = [round(x, 2) for x in np.arange(0.50, 0.951, 0.05)]
MAX_FALSE_REJECTION = 0.05


def main():
    rows = [json.loads(line) for line in open(config.EVAL_DIR / "calibration_domain.jsonl", encoding="utf-8")]
    engine = RagEngine()
    min_score = rc.get("min_retrieval_score")
    for r in rows:
        q = r["question"]
        r["safety"] = bool(ADVERSARIAL_RE.search(q))
        emb = engine.retriever.embed([q])[0]
        r["p_in_domain"] = engine.classifier.predict(emb)["in_domain_probability"]
        hits = engine.retriever.search(q, query_embedding=emb)
        r["low_retrieval"] = max((h["score"] for h in hits), default=0.0) < min_score

    def rejected(r, t):
        return r["safety"] or r["p_in_domain"] < t or r["low_retrieval"]

    ood = [r for r in rows if r["type"] == "fuera_de_dominio"]
    ctl = [r for r in rows if r["type"] == "control"]
    table = []
    for t in GRID:
        table.append({"umbral": t,
                      "rechazo_fuera_de_dominio": round(np.mean([rejected(r, t) for r in ood]), 4),
                      "falsos_rechazos": round(np.mean([rejected(r, t) for r in ctl]), 4)})
    ok = [x for x in table if x["falsos_rechazos"] <= MAX_FALSE_REJECTION]
    best = max(ok, key=lambda x: (x["rechazo_fuera_de_dominio"], -x["umbral"])) if ok else None

    out = {"n_fuera_de_dominio": len(ood), "n_control": len(ctl), "criterio_max_falsos_rechazos": MAX_FALSE_REJECTION,
           "tabla": table, "elegido": best,
           "filas": [{k: r[k] for k in ("id", "type", "question", "p_in_domain", "safety", "low_retrieval")} for r in rows]}
    (config.RESULTS_DIR / "exp" / "calibration_threshold.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    for x in table:
        print(f"umbral {x['umbral']:.2f}  fuera de dominio {x['rechazo_fuera_de_dominio']:.0%}  falsos rechazos {x['falsos_rechazos']:.0%}")
    print("elegido:", best)


if __name__ == "__main__":
    main()
