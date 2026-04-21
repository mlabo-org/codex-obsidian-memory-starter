#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_NAME="${CODEX_OBSIDIAN_MEMORY_REPO_NAME:-codex-obsidian-memory-starter}"
DESCRIPTION="${CODEX_OBSIDIAN_MEMORY_REPO_DESCRIPTION:-Codex-assisted starter for an episode-first external-memory hook workflow using Obsidian-readable Markdown storage.}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required. Install GitHub CLI first."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub authentication is missing. Run: gh auth login"
  exit 1
fi

cd "${REPO_ROOT}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This directory is not a git repository: ${REPO_ROOT}"
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  gh repo create "${REPO_NAME}" \
    --private \
    --source . \
    --remote origin \
    --description "${DESCRIPTION}" \
    --push
else
  git push -u origin "$(git branch --show-current)"
fi

gh repo view --web=false
