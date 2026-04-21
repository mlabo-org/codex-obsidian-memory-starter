# Codex Setup Notes

このファイルは、この repo を開いた Codex が「作者の環境を再演する」のではなく、「いまの所有者の環境に合わせて導入する」ための短い確認メモです。

## Minimum adaptation points

1. `workspace_hints`
   clone 先の path が入っていても、それが所有者の実際の作業場所とズレるなら直してください。
2. `project_id` と project note
   所有者が別 project 名で運用するなら揃えてください。
3. `keywords`
   実際の prompt に出る言い回しへ寄せてください。
4. Vault root
   Obsidian 自動検出で足りるか、`CODEX_OBSIDIAN_MEMORY_VAULT_ROOT` が必要かを見てください。
5. Existing hooks
   既存 hook を壊さず、この starter の 3 本だけを追加・更新してください。

## Definition of done

- prompt が `ultra_short` に落ちる
- relevant prompt が `episodes` に残る
- 再開時に `SessionStart` context が出る
- 作者の固定 path が残っていない
