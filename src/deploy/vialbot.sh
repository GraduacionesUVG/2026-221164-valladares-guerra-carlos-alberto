#!/bin/bash
# Administra el despliegue de producción (vialbot.vallague.com) en la Mac Mini.
#
# Producción corre desde su propia copia, fuera de ~/Documents ($PROD): macOS
# no deja que los servicios de launchd (motor de IA, Colima al reiniciar) lean
# ~/Documents, y así los experimentos del repositorio no afectan el sitio.
#
#   deploy/vialbot.sh deploy       copia el repo a $PROD, reconstruye y reinicia todo
#   deploy/vialbot.sh up           reconstruye y levanta los contenedores de $PROD
#   deploy/vialbot.sh install-ai   instala el motor de IA en el anfitrión (launchd)
#   deploy/vialbot.sh restart-ai   reinicia el motor de IA
#   deploy/vialbot.sh ps|logs|down|restart
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
PROD=${VIALBOT_PROD:-$HOME/Servicios/vialbot}
export PATH=/opt/homebrew/bin:$PATH
dc() { (cd "$PROD" && docker compose -f docker-compose.prod.yml --env-file .env.production "$@"); }

sync_prod() {
  mkdir -p "$PROD"
  # Código, corpus, embedder, clasificador, índice y resultados. Quedan fuera
  # los secretos y la configuración en caliente (propios de producción) y lo
  # que solo sirve para entrenar o experimentar.
  rsync -a --delete \
    --exclude '.env.production' --exclude '.credenciales-produccion.txt' \
    --exclude 'AI/data/runtime_config.json' --exclude 'AI/.venv/' --exclude 'AI/logs/' \
    --exclude 'AI/models/vialbot-generator-*' --exclude 'AI/models/v1_backup/' \
    --exclude 'AI/models/*.gguf' --exclude 'AI/models/Modelfile*' \
    --exclude 'AI/data/dataset/' --exclude 'AI/eval/results/exp/' \
    --exclude 'node_modules/' --exclude 'Frontend/dist/' --exclude '__pycache__/' \
    "$REPO/" "$PROD/"
  [ -f "$PROD/AI/data/runtime_config.json" ] || cp "$REPO/AI/data/runtime_config.json" "$PROD/AI/data/"
  if [ ! -x "$PROD/AI/.venv/bin/python" ]; then
    uv venv --python 3.12 "$PROD/AI/.venv"
  fi
  uv pip install --quiet --python "$PROD/AI/.venv/bin/python" -r "$PROD/AI/requirements.txt"
}

install_ai() {
  local plist=~/Library/LaunchAgents/gt.vialbot.ai.plist
  mkdir -p "$PROD/AI/logs"
  sed "s|__PROTOTIPO__|$PROD|g" "$PROD/deploy/gt.vialbot.ai.plist" > "$plist"
  launchctl bootout "gui/$(id -u)/gt.vialbot.ai" 2>/dev/null || true
  # bootout es asíncrono: bootstrap falla ("Input/output error") si el
  # servicio anterior aún no terminó de salir
  for _ in $(seq 1 30); do
    launchctl print "gui/$(id -u)/gt.vialbot.ai" >/dev/null 2>&1 || break
    sleep 1
  done
  launchctl bootstrap "gui/$(id -u)" "$plist"
  for _ in $(seq 1 90); do
    curl -sf http://127.0.0.1:8000/health >/dev/null && { echo "Motor de IA en línea"; return; }
    sleep 2
  done
  echo "El motor de IA no respondió; revisa $PROD/AI/logs/ai-native.log" >&2
  return 1
}

case "${1:-up}" in
  deploy)
    sync_prod
    dc up -d --build
    install_ai ;;
  up)         dc up -d --build ;;
  install-ai) install_ai ;;
  restart-ai) launchctl kickstart -k "gui/$(id -u)/gt.vialbot.ai" ;;
  down)       dc down ;;
  restart)    dc restart ;;
  ps)         dc ps ;;
  logs)       shift; dc logs -f --tail 100 "$@" ;;
  *)          dc "$@" ;;
esac
