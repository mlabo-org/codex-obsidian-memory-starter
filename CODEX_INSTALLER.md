# Codex Installer Mode

この repo では、Codex を「README を読むだけの相手」ではなく、環境適応と検証を担当する installer の一部として使えます。

## Intent

- clone 後の path 調整
- Vault root の決定
- `workspace_hints` と `keywords` の調整
- 既存 hook との共存確認
- `bootstrap.sh` 実行後の動作検証
- `verify_install.sh` による one-shot self-check

## Recommended flow

1. この repo を GUI Codex で開く
2. `AGENTS.md` と `CODEX_SETUP.md` と `CODEX_INSTALLER.md` と `README.md` を先に読む
3. `./scripts/print_codex_installer_prompt.sh` を Codex 自身が実行する
4. そのまま Codex が ownership-aware install と verify を最後まで進める

## Why this is useful

この starter は、clone して script を一発実行すれば終わるタイプではありません。
利用者ごとに `cwd`、Vault root、project 名、keywords、既存 hooks が違うので、最後の環境適応を Codex に担当させたほうが速くて事故も減ります。
`verify_install.sh` を足したので、最後の確認もかなり自動化できます。
