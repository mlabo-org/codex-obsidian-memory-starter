# Publication Checklist

このファイルは、GitHub へ `public` 公開する直前の最終確認用です。

## 任意で追加するもの

- 任意なら `assets/demo/` の短い動画

## 公開前に確認すること

1. `config/projects.local.json` が commit 対象に入っていない
2. `episodes/` に実メモが混ざっていない
3. `rg 'auth.json|token|secret|session=' .` で意図しない露出がない
4. README が GitHub 単体で読んでも意味が通る
5. 記事 URL が README に反映されている
6. `bootstrap.sh` の既定動作が読者環境向けである
7. repo 説明が「作者の実データ配布」ではなく「再現用 starter」になっている
8. スクリーンショットに private note 本文や token が写っていない

## 公開前の最終確認箇所

- `README.md`
  `Status`
- 必要なら repo description

## 公開順序

1. private repo として push する
2. GitHub 上で README 表示とファイル一覧を確認する
3. README と repo description の最終文言を確認する
4. もう一度 secret 混入チェックをする
5. そのあとで public に切り替える
