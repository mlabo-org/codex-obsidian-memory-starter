# Local Constitution For `codex-obsidian-memory-starter`

## Scope

この repo は、作者の個人環境をそのまま再現する配布物ではなく、読者が自分の `GUI Codex` 環境へ external-memory hook を導入するための starter です。

この workspace を開いた Codex は、次の前提を実行条件として扱ってください。

## Primary Role

- まず「現在の所有者の環境」に合わせる
- 作者の絶対パスや運用都合を、そのまま残すことを既定にしない
- clone 済み repo が動くだけでは不十分で、所有者の `cwd`、Vault root、Codex home、project 名、keyword が噛み合う状態まで持っていく

## Environment Adaptation

- `config/projects.example.json` や生成済み `projects.local.json` は完成設定ではなく初期 preset です
- 所有者の workspace に合わせて `workspace_hints` を狭める
- 所有者が別 project 名を使うなら `project_id` と project note path を合わせる
- 所有者の prompt に実際に出る語へ `keywords` を調整する
- `CODEX_OBSIDIAN_MEMORY_VAULT_ROOT` が必要か、Obsidian 自動検出で足りるかを確認する
- Obsidian が無い場合でも、Markdown を保存したい実ディレクトリを Vault root として扱えるようにする

## Do Not Assume Author Paths

- `/Users/suzukimakoto/...` を利用者環境の既定値として残さない
- 作者の `~/.codex`、Vault、workspace path をそのまま採用しない
- clone 先 path を `workspace_hints` に使うのは初期導入の補助としてのみ許容し、必要なら所有者の常用 workspace に置き換える

## Verification Standard

- `bootstrap.sh` が成功すること
- `~/.codex/hooks.json` へ starter の 3 hook が追加されること
- 既存 hook を壊していないこと
- `UserPromptSubmit` で `ultra_short` に書けること
- project に関係する prompt で `episodes` に書けること
- `SessionStart` で recent memory が追加 context として見えること

## Response Stance

- 読者から「導入したい」と言われたら、まず所有者環境へ合わせる必要がある前提を短く伝える
- そのうえで path、Vault root、project 定義を調整する
- README の説明をなぞるだけで終わらず、利用者固有のズレを埋める
