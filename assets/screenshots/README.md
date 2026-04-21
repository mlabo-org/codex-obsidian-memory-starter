# Screenshots

このディレクトリは、GitHub README や記事から参照する静止画の置き場です。

最小構成は 2 枚です。

## 1. `session-start-context.png`

目的:

- `SessionStart` で vault 全体ではなく、直近の memory だけを読んでいることを見せる

画面に入れるもの:

- Codex の会話画面
- `External memory policy: episode-first...` から始まる追加 context
- `Ultra-short captures:` と `Recent episodes:` の両方が見えている状態

入れないほうがよいもの:

- 余計な個人情報
- 関係ないスレッド一覧
- token や path が過度に露出した terminal

推奨キャプション:

- `SessionStart では vault 全体を読まず、直近の ultra_short と recent episodes だけを少量読みます。`

## 2. `obsidian-memory-notes.png`

目的:

- Obsidian 側に `ultra_short` と `episodes` の Markdown note が実際に置かれていることを見せる

画面に入れるもの:

- Obsidian の Vault
- `episodes/ultra_short/` と `episodes/` が分かるサイドバー
- note 本文の一部

入れないほうがよいもの:

- 実運用の private note 本文
- 個人名や private project 名が丸見えの箇所

推奨キャプション:

- `保存先は Obsidian で読める Markdown ですが、運用の主役は GUI ではなく hook 側の自動記録です。`

## 任意の demo

必要なら次も追加できます。

- `assets/demo/prompt-to-episode.mp4`

最小の流れ:

1. prompt を送る
2. `ultra_short` に書き込まれる
3. Stop 後に `episodes` に追記される

30 秒未満で十分です。

## README に足す文面

画像を置いたら、README に次のような短い説明を入れれば足ります。

- `SessionStart では recent memory だけを少量読む`
- `Obsidian では ultra_short と episodes を Markdown note として確認できる`

## 公開前チェック

1. private note 本文が写っていない
2. account 名や token が露出していない
3. 画像名が README の想定名と一致している
