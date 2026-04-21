# Publication Checklist

このファイルは、GitHub へ `public` 公開する直前の確認用です。

## まだ確定してから公開するもの

- README 冒頭の公開文言
- `assets/screenshots/` の実画像
- 任意なら `assets/demo/` の短い動画

## private のうちに確認すること

1. `config/projects.local.json` が commit 対象に入っていない
2. `episodes/` に実メモが混ざっていない
3. `rg 'auth.json|token|secret|session=' .` で意図しない露出がない
4. README が GitHub 単体で読んでも意味が通る
5. 記事 URL が README に反映されている
6. `bootstrap.sh` の既定動作が読者環境向けである
7. repo 説明が「作者の実データ配布」ではなく「再現用 starter」になっている
8. スクリーンショットに private note 本文や token が写っていない

## public にする直前の差し替え箇所

- `README.md`
  `Status`
- `README.md`
  `Related article`
- 必要なら repo description

## 公開順序

1. private repo として push する
2. GitHub 上で README 表示とファイル一覧を確認する
3. 記事 URL と最終文言を反映する
4. もう一度 secret 混入チェックをする
5. そのあとで public に切り替える
