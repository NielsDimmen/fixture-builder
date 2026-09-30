#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${HA_HOST:-root@homeassistant.local}"
REMOTE_DIR="${HA_ADDON_DIR:-/addons/fixture_builder}"

cd "$ROOT"

if [[ "${1:-}" == "--scp" ]]; then
  echo "Copying add-on to ${HOST}:${REMOTE_DIR}"
  ssh "$HOST" "mkdir -p ${REMOTE_DIR}"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.env' \
    "$ROOT/" "$HOST:$REMOTE_DIR/"
  echo "Copied. In Home Assistant: Settings → Add-ons → Add-on Store → ⋮ → Check for updates / Reload, then install Fixture Builder."
  exit 0
fi

echo "Add-on source: $ROOT"
echo "Install on HA with:"
echo "  ./scripts/pack-ha-addon.sh --scp"
echo "or:"
echo "  scp -r \"$ROOT\" ${HOST}:/addons/fixture_builder"
