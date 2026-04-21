#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODEX_HOME="${CODEX_OBSIDIAN_MEMORY_CODEX_HOME:-$HOME/.codex}"
VAULT_ROOT="${CODEX_OBSIDIAN_MEMORY_VAULT_ROOT:-$REPO_ROOT/vault}"
PROJECTS_LOCAL="${CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE:-$REPO_ROOT/config/projects.local.json}"
HOOKS_JSON="${CODEX_HOME}/hooks.json"

mkdir -p "${CODEX_HOME}"
mkdir -p "${VAULT_ROOT}/episodes/ultra_short"
mkdir -p "${VAULT_ROOT}/knowledge/projects" "${VAULT_ROOT}/knowledge/rules" "${VAULT_ROOT}/knowledge/decisions"

if [[ ! -f "${PROJECTS_LOCAL}" ]]; then
  cp "${REPO_ROOT}/config/projects.example.json" "${PROJECTS_LOCAL}"
fi

if [[ -f "${HOOKS_JSON}" ]]; then
  cp "${HOOKS_JSON}" "${HOOKS_JSON}.bak"
fi

export REPO_ROOT
export VAULT_ROOT
export PROJECTS_LOCAL
export HOOKS_JSON

python3 <<'PY'
import json
import os
from pathlib import Path

hooks_json = Path(os.environ["HOOKS_JSON"])
repo_root = os.environ["REPO_ROOT"]
vault_root = os.environ["VAULT_ROOT"]
projects_local = os.environ["PROJECTS_LOCAL"]

if hooks_json.exists():
    data = json.loads(hooks_json.read_text())
else:
    data = {"hooks": {}}

data.setdefault("hooks", {})

commands = {
    "SessionStart": {
        "matcher": "startup|resume|clear|compact",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{repo_root}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{repo_root}/hooks/session_start.py'"
        ),
    },
    "UserPromptSubmit": {
        "matcher": "",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{repo_root}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{repo_root}/hooks/user_prompt_submit.py'"
        ),
    },
    "Stop": {
        "matcher": "",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{repo_root}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{repo_root}/hooks/stop.py'"
        ),
    },
}

for event_name, spec in commands.items():
    entries = data["hooks"].setdefault(event_name, [])
    found = False
    for entry in entries:
        for hook in entry.get("hooks", []):
            if hook.get("command") == spec["command"]:
                found = True
                break
        if found:
            break
    if not found:
        entries.append(
            {
                "matcher": spec["matcher"],
                "hooks": [
                    {
                        "type": "command",
                        "command": spec["command"],
                        "timeout": 10,
                    }
                ],
            }
        )

hooks_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY

echo "Installed starter hooks into ${HOOKS_JSON}"
echo "Vault root: ${VAULT_ROOT}"
echo "Projects file: ${PROJECTS_LOCAL}"
echo "Edit ${PROJECTS_LOCAL} before relying on project-aware episode capture."
