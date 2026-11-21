#!/bin/bash
# Entrena los tres modelos propios y ejecuta la evaluación completa.
# Requiere el dataset generado (training.generate_dataset qa + verify).
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
step() { echo; echo "=== $(date '+%H:%M:%S') $1 ==="; }

# Libera la memoria de GPU que ocupen los modelos de Ollama antes de entrenar
for m in qwen3:8b qwen2.5:7b gemma3:4b qwen2.5:1.5b; do
  curl -s localhost:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null || true
done

step "1/7 Embeddings propios"
$PY -m training.train_embedder
step "2/7 Índice vectorial con el modelo propio"
$PY -m pipeline.build_index --only vialbot
step "3/7 Clasificador de temas y dominio"
$PY -m training.train_classifier
step "4/7 LLM propio (LoRA) y registro en Ollama"
$PY -m training.train_generator all
step "5/7 Evaluación de recuperación"
$PY -m eval.eval_retrieval
step "6/7 Pruebas de límites"
$PY -m eval.eval_boundary
step "7/7 Evaluación de generación (LLM-as-a-Judge)"
$PY -m eval.eval_generation --n 50
step "Listo"
