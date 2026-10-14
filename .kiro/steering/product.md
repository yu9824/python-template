# Product Overview

> このファイルはテンプレート自身の説明。テンプレートから作ったリポジトリでは、
> そのプロジェクトの説明に書き換える (`/kiro-steering` に頼んでもよい)。
> テンプレート固有の内容はこのファイルに集め、tech.md / structure.md は
> 下流でもそのまま通用するように書く。

yu9824 が自分の Python ライブラリと実験 (Kaggle など) を始めるための
GitHub テンプレートリポジトリ。「Use this template」で新しいリポジトリを作り、
パッケージ名を一括置換して使う。

## Core Capabilities

- **ライブラリの骨組み**: src レイアウト、git タグからのバージョン決定、
  Sphinx ドキュメント、CI (テスト・ドキュメント・リリース) が最初から揃う
- **再利用できる部品**: ライブラリ用 logging (`python_template.logging`) と
  小物 (`python_template.helpers`: `is_installed`, `dummy_tqdm`,
  `tqdm_joblib`, `deprecated`)。下流でもそのまま使う前提で、テスト付き
- **実験の置き場**: `notebooks/` (jupytext でペア)、`data/`、`models/`
- **環境**: conda 環境と Claude Code 入りの Dev Container、
  利用者向けの Docker イメージ

## Target Use Cases

- 新しい Python ライブラリを作り、PyPI / GitHub Releases に出す
- データ分析・機械学習の実験を、後でライブラリに切り出せる形で進める

## テンプレートとしての運用

- **下流で邪魔になるものは、main に merge する前に削除する**。
  例: テンプレート自身の改良のための spec (`.kiro/specs/<feature>/`) は作業
  ブランチで commit してよいが、merge 前に消す (中身は git 履歴に残る)
- 下流に引き継ぐもの (CLAUDE.md、`.kiro/steering/` の tech / structure、
  `.kiro/settings/`、`.claude/skills/`) はプロジェクト名に依存しない書き方にする
- 下流で書き換えるものはこのファイルとパッケージ名 (`python_template` /
  `python-template`) に限る

---
_updated_at: 2026-10-14_
