#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CODEX_HOME="${CODEX_OBSIDIAN_MEMORY_CODEX_HOME:-$HOME/.codex}"
INSTALL_ROOT="${CODEX_OBSIDIAN_MEMORY_INSTALL_ROOT:-$CODEX_HOME/hooks/obsidian-memory-starter}"
RUNTIME_HOOKS_DIR="${INSTALL_ROOT}/hooks"
RUNTIME_CONFIG_DIR="${INSTALL_ROOT}/config"
PROJECTS_LOCAL="${CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE:-$RUNTIME_CONFIG_DIR/projects.local.json}"
HOOKS_JSON="${CODEX_HOME}/hooks.json"
OBSIDIAN_CONFIG_JSON="${HOME}/Library/Application Support/obsidian/obsidian.json"

detect_obsidian_vault_root() {
  if [[ -n "${CODEX_OBSIDIAN_MEMORY_VAULT_ROOT:-}" ]]; then
    printf '%s\n' "${CODEX_OBSIDIAN_MEMORY_VAULT_ROOT}"
    return
  fi

  if [[ -f "${OBSIDIAN_CONFIG_JSON}" ]]; then
    local detected
    detected="$(
      python3 <<'PY'
import json
from pathlib import Path

config_path = Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
try:
    payload = json.loads(config_path.read_text())
except Exception:
    print("")
    raise SystemExit(0)

vaults = payload.get("vaults", {})
preferred = None
fallback = None

for item in vaults.values():
    path = str(item.get("path", "")).strip()
    if not path:
        continue
    if fallback is None:
        fallback = path
    if item.get("open") is True:
        preferred = path
        break

print(preferred or fallback or "")
PY
    )"
    if [[ -n "${detected}" ]]; then
      printf '%s\n' "${detected}"
      return
    fi
  fi

  printf '%s\n' "${REPO_ROOT}/vault"
}

VAULT_ROOT="$(detect_obsidian_vault_root)"

mkdir -p "${CODEX_HOME}"
mkdir -p "${RUNTIME_HOOKS_DIR}" "${RUNTIME_CONFIG_DIR}"
mkdir -p "${VAULT_ROOT}/episodes/ultra_short"
mkdir -p "${VAULT_ROOT}/knowledge/projects" "${VAULT_ROOT}/knowledge/rules" "${VAULT_ROOT}/knowledge/decisions"
mkdir -p "${VAULT_ROOT}/maps" "${VAULT_ROOT}/archive" "${VAULT_ROOT}/templates"

cp "${REPO_ROOT}/hooks/"*.py "${RUNTIME_HOOKS_DIR}/"
cp "${REPO_ROOT}/config/projects.example.json" "${RUNTIME_CONFIG_DIR}/projects.example.json"

seed_if_missing() {
  local source_path="$1"
  local target_path="$2"
  if [[ ! -e "${target_path}" ]]; then
    cp "${source_path}" "${target_path}"
  fi
}

seed_if_missing "${REPO_ROOT}/vault/episodes/README.md" "${VAULT_ROOT}/episodes/README.md"
seed_if_missing "${REPO_ROOT}/vault/episodes/ultra_short/README.md" "${VAULT_ROOT}/episodes/ultra_short/README.md"
seed_if_missing "${REPO_ROOT}/vault/knowledge/README.md" "${VAULT_ROOT}/knowledge/README.md"
seed_if_missing "${REPO_ROOT}/vault/knowledge/decisions/README.md" "${VAULT_ROOT}/knowledge/decisions/README.md"
seed_if_missing "${REPO_ROOT}/vault/knowledge/projects/obsidian-memory-system.md" "${VAULT_ROOT}/knowledge/projects/obsidian-memory-system.md"
seed_if_missing "${REPO_ROOT}/vault/knowledge/rules/episode-write-timing.md" "${VAULT_ROOT}/knowledge/rules/episode-write-timing.md"
seed_if_missing "${REPO_ROOT}/vault/maps/README.md" "${VAULT_ROOT}/maps/README.md"
seed_if_missing "${REPO_ROOT}/vault/archive/README.md" "${VAULT_ROOT}/archive/README.md"
seed_if_missing "${REPO_ROOT}/vault/templates/README.md" "${VAULT_ROOT}/templates/README.md"

export REPO_ROOT
export CODEX_HOME
export VAULT_ROOT
export PROJECTS_LOCAL
export HOOKS_JSON
export RUNTIME_HOOKS_DIR
export INSTALL_ROOT
export RUNTIME_CONFIG_DIR

if [[ ! -f "${PROJECTS_LOCAL}" ]]; then
  python3 <<'PY'
import json
import os
from pathlib import Path

example_path = Path(os.environ["RUNTIME_CONFIG_DIR"]) / "projects.example.json"
target_path = Path(os.environ["PROJECTS_LOCAL"])
payload = json.loads(example_path.read_text())
target_path.parent.mkdir(parents=True, exist_ok=True)

replacements = {
    "__REPO_ROOT__": os.environ["REPO_ROOT"],
    "__CODEX_HOME__": os.environ["CODEX_HOME"],
    "__VAULT_ROOT__": os.environ["VAULT_ROOT"],
}

for project in payload.get("projects", []):
    project["workspace_hints"] = [
        replacements.get(str(item).strip(), str(item).strip())
        for item in project.get("workspace_hints", [])
        if str(item).strip()
    ]

target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
PY
fi

if [[ -f "${HOOKS_JSON}" ]]; then
  cp "${HOOKS_JSON}" "${HOOKS_JSON}.bak"
fi

python3 <<'PY'
import json
import os
from pathlib import Path

hooks_json = Path(os.environ["HOOKS_JSON"])
install_root = os.environ["INSTALL_ROOT"]
repo_root = os.environ["REPO_ROOT"]
vault_root = os.environ["VAULT_ROOT"]
projects_local = os.environ["PROJECTS_LOCAL"]
runtime_hooks_dir = os.environ["RUNTIME_HOOKS_DIR"]

if hooks_json.exists():
    data = json.loads(hooks_json.read_text())
else:
    data = {"hooks": {}}

data.setdefault("hooks", {})

managed_scripts = (
    f"{install_root}/hooks/session_start.py",
    f"{install_root}/hooks/user_prompt_submit.py",
    f"{install_root}/hooks/stop.py",
    f"{repo_root}/hooks/session_start.py",
    f"{repo_root}/hooks/user_prompt_submit.py",
    f"{repo_root}/hooks/stop.py",
)
for event_name, entries in list(data["hooks"].items()):
    kept_entries = []
    for entry in entries:
        kept_hooks = []
        for hook in entry.get("hooks", []):
            command = hook.get("command", "")
            if any(script in command for script in managed_scripts):
                continue
            kept_hooks.append(hook)
        if kept_hooks:
            entry["hooks"] = kept_hooks
            kept_entries.append(entry)
    data["hooks"][event_name] = kept_entries

commands = {
    "SessionStart": {
        "matcher": "startup|resume|clear|compact",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{install_root}' "
            f"CODEX_OBSIDIAN_MEMORY_CODEX_HOME='{os.environ['CODEX_HOME']}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{runtime_hooks_dir}/session_start.py'"
        ),
    },
    "UserPromptSubmit": {
        "matcher": "",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{install_root}' "
            f"CODEX_OBSIDIAN_MEMORY_CODEX_HOME='{os.environ['CODEX_HOME']}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{runtime_hooks_dir}/user_prompt_submit.py'"
        ),
    },
    "Stop": {
        "matcher": "",
        "command": (
            f"env CODEX_OBSIDIAN_MEMORY_REPO_ROOT='{install_root}' "
            f"CODEX_OBSIDIAN_MEMORY_CODEX_HOME='{os.environ['CODEX_HOME']}' "
            f"CODEX_OBSIDIAN_MEMORY_VAULT_ROOT='{vault_root}' "
            f"CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE='{projects_local}' "
            f"python3 '{runtime_hooks_dir}/stop.py'"
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
echo "Installed runtime hooks into ${RUNTIME_HOOKS_DIR}"
echo "Vault root: ${VAULT_ROOT}"
echo "Projects file: ${PROJECTS_LOCAL}"
echo "Edit ${PROJECTS_LOCAL} before relying on project-aware episode capture."
echo "Run ${REPO_ROOT}/scripts/verify_install.sh for a one-shot install check."
