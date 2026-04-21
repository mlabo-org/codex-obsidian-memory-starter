#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cat <<EOF
次の repo を読んで、あなた自身を installer の一部として扱って導入してください。

repo:
${REPO_ROOT}

最初に読むファイル:
- ${REPO_ROOT}/AGENTS.md
- ${REPO_ROOT}/CODEX_SETUP.md
- ${REPO_ROOT}/CODEX_INSTALLER.md
- ${REPO_ROOT}/README.md

やること:
1. いまの所有者の環境に合わせて導入方針を決める
2. 既存の ~/.codex/hooks.json を壊さない
3. Obsidian があるか確認し、無ければ使う Markdown 保存先を決める
4. ${REPO_ROOT} の starter 設定を所有者環境へ合わせて調整する
5. bootstrap.sh を実行する
6. ${REPO_ROOT}/scripts/verify_install.sh を実行する
7. ultra_short / episodes / SessionStart context が動くところまで確認する

禁止:
- 作者の絶対パスを利用者環境の既定として残さない
- 既存 hook を消さない
- README を読むだけで終わらない

完了条件:
- この starter の 3 hook が追加されている
- verify_install.sh が成功する
- relevant prompt が episodes に残る
- 再開時に SessionStart context が見える
- 利用者環境へ寄せるために変えた点を最後に簡潔に報告する
EOF
