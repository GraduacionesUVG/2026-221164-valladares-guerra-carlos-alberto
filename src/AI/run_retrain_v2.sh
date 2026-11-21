#!/bin/bash
# Segundo intento de entrenamiento del LLM: menos épocas y tasa de aprendizaje
# más baja, para reducir el sobreajuste detectado en v1 (confusión al elegir
# entre varios fragmentos de contexto).
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
step() { echo; echo "=== $(date '+%H:%M:%S') $1 ==="; }

for m in qwen3:8b qwen2.5:7b gemma3:4b qwen2.5:1.5b vialbot vialbot-v1; do
  curl -s localhost:11434/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" >/dev/null || true
done

step "1/4 Reconstruyendo datos de entrenamiento (con el embedder propio ya indexado)"
$PY -m training.train_generator data
step "2/4 Entrenando LoRA v2 (1 epoca, lr=5e-5)"
$PY -m training.train_generator train --epochs 1 --lr 5e-5
step "3/4 Fusionando y registrando en Ollama"
$PY -m training.train_generator fuse
$PY -m training.train_generator ollama
step "4/4 Evaluacion de generacion (v2 vs base, n=50)"
$PY -m eval.eval_generation --n 50
step "Listo v2"
