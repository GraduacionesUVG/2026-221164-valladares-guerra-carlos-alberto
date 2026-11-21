"""Entrenamiento del clasificador propio de temas y de dominio.

Clasifica cada consulta en uno de los temas de config.TOPICS o en
'fuera_de_dominio'. Se usa para:
  - rechazar preguntas ajenas al tránsito (pruebas de límites), y
  - registrar el tema de cada consulta real, lo que alimenta el análisis de
    patrones de búsqueda del objetivo específico 3.

Modelo: regresión logística multinomial sobre los embeddings de la consulta
(generados por el mismo modelo de embeddings que usa el recuperador).

Salida: models/vialbot-classifier.joblib y eval/results/classifier.json

Uso:  python -m training.train_classifier
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from training.common import load_ood_messages, load_qa_pairs, load_testbench_questions  # noqa: E402


def main():
    embedder_name = (str(config.FINETUNED_EMBEDDER_DIR) if config.FINETUNED_EMBEDDER_DIR.exists()
                     else config.BASE_EMBEDDER)
    banned = load_testbench_questions()
    pairs = [p for p in load_qa_pairs() if p["question"].lower() not in banned]
    texts = [p["question"] for p in pairs] + load_ood_messages()
    labels = [p["topic"] for p in pairs] + [config.OUT_OF_DOMAIN] * (len(texts) - len(pairs))
    print(f"[classifier] {len(texts)} ejemplos, embeddings con {Path(embedder_name).name}")

    model = SentenceTransformer(embedder_name)
    X = model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=64)
    y = np.array(labels)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    clf = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced")
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    print(classification_report(y_te, y_pred, zero_division=0))

    # Métrica binaria del filtro de dominio
    ood_true = y_te == config.OUT_OF_DOMAIN
    ood_pred = y_pred == config.OUT_OF_DOMAIN
    domain = {
        "ood_recall": round(float((ood_true & ood_pred).sum() / max(ood_true.sum(), 1)), 4),
        "false_rejection_rate": round(float((~ood_true & ood_pred).sum() / max((~ood_true).sum(), 1)), 4),
    }

    # Modelo final entrenado con todos los datos
    final = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced").fit(X, y)
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": final,
        "embedder": embedder_name,
        "labels": sorted(set(labels)),
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }, config.CLASSIFIER_PATH)

    labels_sorted = sorted(set(labels))
    result = {
        "embedder": Path(embedder_name).name,
        "examples": len(texts),
        "class_counts": {label: int((y == label).sum()) for label in labels_sorted},
        "test_accuracy": round(report["accuracy"], 4),
        "macro_f1": round(report["macro avg"]["f1-score"], 4),
        "domain_filter": domain,
        "per_class": {k: {m: round(v[m], 4) for m in ("precision", "recall", "f1-score")}
                      for k, v in report.items() if k in labels_sorted},
        "confusion_matrix": {"labels": labels_sorted,
                             "matrix": confusion_matrix(y_te, y_pred, labels=labels_sorted).tolist()},
    }
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.RESULTS_DIR / "classifier.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[classifier] exactitud={result['test_accuracy']} macro-F1={result['macro_f1']} {domain}")


if __name__ == "__main__":
    main()
