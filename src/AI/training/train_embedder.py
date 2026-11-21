"""Entrenamiento del modelo propio de embeddings (VialBot Embedder).

Parte de un modelo multilingüe pre-entrenado y lo ajusta (fine-tuning) con los
pares <consulta ciudadana, fragmento de la ley> del dataset sintético, usando
aprendizaje contrastivo con Multiple Negatives Ranking Loss: para cada consulta,
su fragmento es el ejemplo positivo y los fragmentos de las demás consultas del
lote actúan como negativos. Así el modelo aprende a acercar en el espacio
vectorial el lenguaje coloquial guatemalteco al lenguaje jurídico.

Salida: models/vialbot-embedder  (luego: python -m pipeline.build_index --only vialbot)

Uso:  python -m training.train_embedder [--epochs 4]
"""
import argparse
import json
import sys
from pathlib import Path

from datasets import Dataset
from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                   SentenceTransformerTrainingArguments)
from sentence_transformers.sentence_transformer.evaluation import InformationRetrievalEvaluator
from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
from sentence_transformers.sentence_transformer.training_args import BatchSamplers

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from training.common import load_chunks_by_id, load_qa_pairs, split_by_chunk  # noqa: E402


def build_evaluator(val_pairs, chunks) -> InformationRetrievalEvaluator:
    queries = {f"q{i}": p["question"] for i, p in enumerate(val_pairs)}
    corpus = {cid: c["text"] for cid, c in chunks.items()}
    relevant = {f"q{i}": {p["chunk_id"]} for i, p in enumerate(val_pairs)}
    return InformationRetrievalEvaluator(queries, corpus, relevant, name="val",
                                         accuracy_at_k=[1, 3, 5], mrr_at_k=[10],
                                         show_progress_bar=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-5)
    args = parser.parse_args()

    chunks = load_chunks_by_id()
    train_pairs, val_pairs = split_by_chunk(load_qa_pairs())
    print(f"[embedder] {len(train_pairs)} pares de entrenamiento, {len(val_pairs)} de validación")

    train_ds = Dataset.from_dict({
        "anchor": [p["question"] for p in train_pairs],
        "positive": [chunks[p["chunk_id"]]["text"] for p in train_pairs],
    })

    model = SentenceTransformer(config.BASE_EMBEDDER)
    evaluator = build_evaluator(val_pairs, chunks)
    before = evaluator(model)

    out_dir = config.FINETUNED_EMBEDDER_DIR
    training_args = SentenceTransformerTrainingArguments(
        output_dir=str(config.MODELS_DIR / "checkpoints" / "embedder"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.1,
        # Evita que un mismo fragmento aparezca dos veces en un lote (sería un
        # falso negativo para la función de pérdida)
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=20,
        seed=42,
        report_to="none",
    )
    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        loss=MultipleNegativesRankingLoss(model),
        evaluator=evaluator,
    )
    trainer.train()
    after = evaluator(model)
    model.save(str(out_dir))

    keys = ["val_cosine_accuracy@1", "val_cosine_accuracy@3", "val_cosine_accuracy@5", "val_cosine_mrr@10"]
    summary = {
        "base_model": config.BASE_EMBEDDER,
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "validation_before": {k: round(before[k], 4) for k in keys},
        "validation_after": {k: round(after[k], 4) for k in keys},
    }
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.RESULTS_DIR / "embedder_training.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"[embedder] modelo guardado en {out_dir}")


if __name__ == "__main__":
    main()
