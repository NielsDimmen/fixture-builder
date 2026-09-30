#!/bin/bash
set -euo pipefail

export PORT="${PORT:-8099}"

if [ -f /data/options.json ]; then
  eval "$(python3 - <<'PY'
import json
import shlex
from pathlib import Path

opts = json.loads(Path("/data/options.json").read_text())
mapping = {
    "openai_api_key": "OPENAI_API_KEY",
    "openai_model": "OPENAI_MODEL",
    "library_path": "LIBRARY_PATH",
}
for key, env in mapping.items():
    value = opts.get(key, "")
    if value is None:
        value = ""
    print(f"export {env}={shlex.quote(str(value))}")
PY
)"
fi

export OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o}"
export LIBRARY_PATH="${LIBRARY_PATH:-/share/dmxlan}"

cd /app
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
