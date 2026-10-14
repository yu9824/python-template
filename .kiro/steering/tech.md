# Technology Stack

## Architecture

純 Python のライブラリ (src レイアウト) と、それを使う実験用ディレクトリの
同居。ライブラリ側は依存を最小に保ち、実験に要るもの (numpy, pandas,
jupyter など) は開発環境 (conda) にだけ入れる。

## Core Technologies

- **Language**: Python >= 3.9 (CI は 3.9〜3.14 で回す)
- **Build**: setuptools + setuptools_scm。バージョンは git タグ (`vX.Y.Z`)
  から決まり、`src/<package>/_version.py` は生成物で追跡しない
- **開発環境**: conda 環境 `work` (`environment.yml`)。Dev Container では
  イメージに焼き込み済みで、自分自身は editable install

## Dependencies

- 実行時の依存は最小限 (Python < 3.10 向けの `typing_extensions` だけ)
- extras: `test` (pytest)、`dev` (build)、`optional` (colorlog, tqdm,
  joblib)、`docs` (Sphinx 一式)
- optional な依存は無くても import が通るようにする (structure.md 参照)
- 下限は「動作を確認した版」の意味で、Dependabot も新版を許容できる限り
  上げない (`versioning-strategy: increase-if-necessary`)

## Development Standards

### Type Safety
- 型ヒントを付け、mypy (`mypy.ini`) を通す
- 3.9 でも動く書き方: `from __future__ import annotations` か `Optional`、
  3.10 以降の typing 機能は `typing_extensions` から

### Code Quality
- ruff (`ruff.toml`): 1 行 79 文字、docstring は numpy 形式
- エラーは握りつぶさず、直し方の分かるメッセージを付けて送出する

### Testing
- pytest。`tests/test_<module>.py` にモジュール単位で置く
- optional な依存に頼るテストは `pytest.importorskip` で飛ばし、
  「無い場合」は `monkeypatch.setitem(sys.modules, "<pkg>", None)` で再現する
- pytest 9 は伝播しない logger すべてに自前のハンドラを付けるので、
  ハンドラを比べるテストは pytest のものを除いて比べる

## Development Environment

### Required Tools
- Dev Container (VS Code) か、conda + `pip install -e ".[dev,test,optional]"`
- Docker (利用者向けイメージのビルド)

### Common Commands
```bash
# Test: pytest
# Lint / Format: ruff check . && ruff format .
# Type check: mypy src
# Docs: sphinx-apidoc -f -o ./docs_src ./src/<package> --module-first && sphinx-build -b html ./docs_src ./docs
# Build: python -m build
# User image: docker build -f docker/Dockerfile -t <package> . && docker run --rm -it <package>
```

## Key Technical Decisions

- **conda は開発環境、pip はライブラリ**: 実験の重い依存は conda で揃え、
  ライブラリの依存宣言 (pyproject.toml) には持ち込まない
- **Docker は用途で分ける**: `.devcontainer/` は開発用 (道具を足す方向)、
  `docker/` は利用者向け (wheel だけを入れた最小イメージ)
- **CI は paths で絞る**: 必須チェックにする workflow は `dorny/paths-filter`
  で job 単位に飛ばす (workflow ごと飛ぶと Pending のまま残るため)
- **リリース**: タグの push で build し、設定すれば PyPI にも出す
  (`HOW_TO_RELEASE.md`)

---
_updated_at: 2026-10-14_
