# codex-obsidian-memory-starter

`Codex hooks` と `Obsidian` を使って、episode-first の外部記憶運用を最小構成で再現するためのスターターです。記事「Codex hooks と Obsidian で作る海馬的超短期型の外部記憶運用」と矛盾しないよう、実装は次の流れだけに絞っています。

- `SessionStart`: vault 全体ではなく、直近の `ultra_short` と現在 project の recent `episodes` だけ読む
- `UserPromptSubmit`: 送信直後の prompt を `ultra_short` へ即時保存し、project に紐づくものだけ `episodes` にも短く残す
- `Stop`: 会話の一区切りを `episodes` に追記する

## これは何を読むか

この starter が自動で読む対象は次の 2 系統です。

- `vault/episodes/ultra_short/*.md` の直近エントリ
- 現在の project に一致した `vault/episodes/*.md` の recent note

`knowledge/rules/` と `knowledge/projects/` は常時総なめしません。必要になったときだけ参照する前提です。

## これは何を書くか

この starter が自動で書く対象は次の 2 系統です。

- `ultra_short`
  送信した prompt の断片を、その場で判断せずに退避する混在 inbox
- `episodes`
  project と関係がある prompt や、会話の意味ある区切りを短い bullet で残す短中期メモ

`knowledge` は自動で肥大化させません。長く残す value があるものだけ、人間が昇格させる前提です。

## レイヤーの役割

- `ultra_short`
  保存時点では価値判断しない即時バッファです。取りこぼし防止が役割です。
- `episodes`
  project 寄りの短中期メモです。次の session で立ち上がりを軽くするのが役割です。
- `knowledge`
  durable な rules / decisions / projects だけを置く層です。全部を入れる棚ではありません。

## ディレクトリ構成

```text
codex-obsidian-memory-starter/
├── config/
│   ├── hooks.sample.json
│   ├── projects.example.json
│   └── projects.local.json   # bootstrap 時に生成。git 管理しない
├── hooks/
│   ├── memory_hooks.py
│   ├── session_start.py
│   ├── stop.py
│   └── user_prompt_submit.py
├── scripts/
│   ├── bootstrap.sh
│   └── uninstall.sh
└── vault/
    ├── episodes/
    │   ├── README.md
    │   └── ultra_short/
    │       └── README.md
    └── knowledge/
        ├── projects/
        └── rules/
```

## 導入手順

1. この repo を clone します。
2. `config/projects.local.json` を作ります。
   `./scripts/bootstrap.sh` を最初に実行すると、`config/projects.example.json` から雛形が生成されます。
3. `config/projects.local.json` の `workspace_hints` と `keywords` を、自分の project に合わせて編集します。
4. 必要なら `CODEX_OBSIDIAN_MEMORY_VAULT_ROOT` を既存 Obsidian Vault に変更します。
   既定ではこの repo 内の `vault/` を使います。
5. `./scripts/bootstrap.sh` を実行します。
   これで `~/.codex/hooks.json` に 3 つの hook が追記されます。
6. Codex を再開し、`SessionStart` の追加 context と `vault/episodes/ultra_short/` の書き込みを確認します。

## いちばん短いセットアップ例

```bash
cd /path/to/codex-obsidian-memory-starter
./scripts/bootstrap.sh
```

そのあとに `config/projects.local.json` を編集して、自分の workspace と project note を紐づけてください。

## 設定ファイル

### `config/projects.local.json`

project 判定のためのローカル設定です。各要素は次の意味です。

- `project_id`
  episode frontmatter と note 名に使う ID
- `project_note`
  vault root からの相対パス
- `workspace_hints`
  `cwd` に含まれていたら project 候補として扱う文字列
- `keywords`
  prompt や会話で見つかったら project 判定に使う語
- `related_rules`
  必要時に参照する rule note の相対パス

## hook 設定

`config/hooks.sample.json` に配布用のサンプルがあります。実際の導入では、`bootstrap.sh` がこの repo の絶対パスを埋め込んだ形で `~/.codex/hooks.json` を更新します。

## rollback / uninstall

hook だけ外したい場合は次を実行します。

```bash
./scripts/uninstall.sh
```

この script は `~/.codex/hooks.json` からこの starter の hook だけを削除します。vault 内の note は消しません。

完全に巻き戻す場合:

1. `./scripts/uninstall.sh` を実行する
2. `config/projects.local.json` を削除する
3. 必要なら `vault/episodes/` 以下の生成 note を手動で削除する

## 秘密情報の扱い

この repo に入れない前提のもの:

- `auth.json`
- token 類
- `~/.codex/hooks/logs/` の実ログ
- `~/.codex/hooks/state/` の実データ
- 個人的な vault 本文
- `/Users/...` を直接埋め込んだままの設定

`.gitignore` でも、ローカル設定と生成 note は既定で除外しています。

## 公開前チェック

public に切り替える前に、少なくとも次を確認してください。

1. `config/projects.local.json` が commit 対象に入っていない
2. `vault/episodes/` に自分の実メモが混ざっていない
3. `rg '/Users/|auth.json|token|secret|session=' .` で意図しない露出がない
4. repo 説明が記事本文と矛盾していない

## 記事との対応

記事と揃えて読むなら、説明の軸は次の 3 点です。

- 何を読むか: `ultra_short` と recent `episodes` を少量だけ読む
- 何を書くか: prompt 断片を `ultra_short` に、意味のある区切りを `episodes` に書く
- `knowledge` の扱い: 最初から何でも長期保存しない

## 注意

- これはスターターです。project ごとの durable 昇格 heuristics までは自動化していません。
- `knowledge` への昇格は、人間が運用しながら決める前提です。
- public 配布前に license は別途選んでください。既定では private repo 運用を想定しています。
