#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADDON_SRC="${ROOT}/fixture_builder"
HOST="${HA_HOST:-root@homeassistant.local}"
REMOTE_DIR="${HA_ADDON_DIR:-/addons/fixture_builder}"

cd "$ROOT"

if [[ ! -f "${ADDON_SRC}/config.yaml" ]]; then
  echo "Missing ${ADDON_SRC}/config.yaml" >&2
  exit 1
fi

if [[ "${1:-}" == "--scp" ]]; then
  echo "Copying add-on to ${HOST}:${REMOTE_DIR}"
  ssh "$HOST" "mkdir -p ${REMOTE_DIR}"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.env' \
    "${ADDON_SRC}/" "$HOST:$REMOTE_DIR/"
  echo "Copied. In Home Assistant: Settings → Add-ons → Add-on Store → ⋮ → Check for updates / Reload, then install Fixture Builder."
  exit 0
fi

echo "Add-on source: $ADDON_SRC"
echo "Install as GitHub repository in HA:"
echo "  https://github.com/NielsDimmen/fixture-builder"
echo "Or copy local add-on with:"
echo "  ./scripts/pack-ha-addon.sh --scp"
