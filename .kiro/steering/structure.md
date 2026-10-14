# Project Structure

## Organization Philosophy

「再利用するコード」と「一度きりの実験」を置き場で分ける。実験で書いた
処理が他でも要るようになったら、テストを付けて `src/` に移す。

## Directory Patterns

### ライブラリ本体
**Location**: `src/<package>/`
**Purpose**: 配布するコード。機能ごとにサブパッケージ (`logging/`, `helpers/`)
**Example**: 実装は `_` 付きの非公開モジュール (`helpers/_helpers.py`) に書き、
`__init__.py` で再 export して `__all__` に並べる。Sphinx は `__all__` にある
名前だけをドキュメントにする

### テスト
**Location**: `tests/`
**Purpose**: インストールされたパッケージに対する pytest
**Example**: `tests/test_helpers.py`。重い optional 依存を使うものは別ファイル
(`tests/test_tqdm_joblib.py`) にして、ファイル単位でスキップできるようにする

### 実験
**Location**: `notebooks/`、`examples/`
**Purpose**: notebook は `.ipynb` と `.py` (percent 形式) を jupytext でペアにする
(`jupytext.toml`)。編集は差分の読める `.py` 側で行い、`jupytext --sync` で
`.ipynb` に反映する (VS Code が自動で同期するのは `.ipynb` を保存したときだけ)

### データと成果物
**Location**: `data/raw/`、`data/processed/`、`models/`
**Purpose**: 中身は git で追跡しない (`.gitkeep` だけ残す)。`data/raw/` は
入手したままの元データで書き換えない。加工したものは `data/processed/` へ

### 環境
**Location**: `.devcontainer/`、`docker/`
**Purpose**: `.devcontainer/` は開発用コンテナ (compose + conda 環境)、
`docker/` は利用者向けイメージ (`Dockerfile` と専用の `.dockerignore`)

### その他
- `docs_src/`: Sphinx のソース。`tutorials/` の notebook もペア管理
- `packages/`: 別のビルド構成 (hatchling、Cython など) のひな形

## Naming Conventions

- **Modules**: snake_case。非公開モジュールは `_` で始める
- **Classes**: PascalCase。ただし `with` で使うコンテキストマネージャは関数風の
  snake_case (`catch_default_handler`, `tqdm_joblib`)
- **Functions**: snake_case

## Import Organization

```python
# パッケージ内は相対 import
from ._helpers import is_installed

# optional な依存は、使う関数の中で import する
def run():
    if not is_installed("joblib"):
        raise ImportError("... requires joblib; install it with `pip install joblib`.")
    import joblib
```

## Code Organization Principles

- **ログ**: ライブラリ内では `print` せず、`get_child_logger(__name__)` で
  得た logger を使う。ライブラリのルート logger は親に伝播しない
- **optional な依存**: モジュールの先頭で import しない。無ければ使った時点で
  インストール方法つきの `ImportError` を出し、進捗バーのような
  付加機能は `dummy_tqdm` などで黙って代替する
- **副作用を小さく**: グローバル状態を書き換える処理 (logger のハンドラ、
  ライブラリのメソッド差し替え) はコンテキストマネージャにし、抜けるときに
  入る前の状態へ戻す

---
_updated_at: 2026-10-14_
