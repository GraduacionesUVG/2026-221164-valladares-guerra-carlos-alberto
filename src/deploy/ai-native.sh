#!/bin/bash
# Motor de IA en el anfitrión (fuera de Docker) para usar la GPU de Apple
# Silicon (MPS): en el contenedor, sin GPU, el reranker tarda ~9× más.
# Lo ejecuta launchd (deploy/gt.vialbot.ai.plist); escucha solo en 127.0.0.1 y
# los contenedores lo alcanzan en host.docker.internal:8000, igual que a Ollama.
set -euo pipefail
cd "$(dirname "$0")/.."
AI_SERVICE_TOKEN=$(grep '^AI_SERVICE_TOKEN=' .env.production | cut -d= -f2-)
export AI_SERVICE_TOKEN TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1
cd AI
exec .venv/bin/uvicorn service.app:app --host 127.0.0.1 --port 8000 --workers 1
