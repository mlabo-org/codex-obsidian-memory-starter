#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODEX_HOME="${CODEX_OBSIDIAN_MEMORY_CODEX_HOME:-$HOME/.codex}"
HOOKS_JSON="${CODEX_HOME}/hooks.json"

if [[ ! -f "${HOOKS_JSON}" ]]; then
  echo "No hooks.json found at ${HOOKS_JSON}"
  exit 0
fi

cp "${HOOKS_JSON}" "${HOOKS_JSON}.bak"
export REPO_ROOT
export HOOKS_JSON

python3 <<'PY'
import json
import os
from pathlib import Path

repo_root = os.environ["REPO_ROOT"]
hooks_json = Path(os.environ["HOOKS_JSON"])
data = json.loads(hooks_json.read_text())

for event_name, entries in list(data.get("hooks", {}).items()):
    kept = []
    for entry in entries:
        hooks = []
        for hook in entry.get("hooks", []):
            command = hook.get("command", "")
            if repo_root in command and "/hooks/" in command:
                continue
            hooks.append(hook)
        if hooks:
            entry["hooks"] = hooks
            kept.append(entry)
    data["hooks"][event_name] = kept

hooks_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY

echo "Removed starter hook entries from ${HOOKS_JSON}"
echo "Your generated vault notes were left untouched."
