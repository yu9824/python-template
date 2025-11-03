"""Setup configuration for Cython extension modules.

This file is required for compiling Cython .pyx files.
It uses pyproject.toml for most configuration and only handles
the Cython-specific compilation.

This script automatically discovers and compiles all .pyx files
in the src/python_template directory tree.
"""

from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup

# srcディレクトリのパス
SRC_DIR = Path("src").resolve()
PACKAGE_DIR = SRC_DIR / "python_template"


def find_pyx_files(root_dir: Path) -> list[tuple[Path, str]]:
    """
    指定されたディレクトリ内のすべての.pyxファイルを検出し、
    モジュール名とファイルパスのペアを返す.

    Parameters
    ----------
    root_dir : Path
        検索するルートディレクトリ（通常はsrcディレクトリ）

    Returns
    -------
    list[tuple[Path, str]]
        (ファイルパス, モジュール名)のリスト
    """
    pyx_files = []
    root_path = root_dir.resolve()

    # すべての.pyxファイルを再帰的に検索
    for pyx_file in root_path.rglob("*.pyx"):
        # src/からの相対パスを取得
        relative_path = pyx_file.relative_to(root_path)

        # モジュール名を生成（拡張子を除く）
        # 例: python_template/cython.pyx -> python_template.cython
        # 例: python_template/module/foo.pyx -> python_template.module.foo
        parts = relative_path.parts[:-1] + (relative_path.stem,)
        module_name = ".".join(parts)

        pyx_files.append((pyx_file, module_name))
    return pyx_files


def create_extensions() -> list[Extension]:
    """
    プロジェクト内のすべての.pyxファイルから拡張モジュールを作成.

    Returns
    -------
    list[Extension]
        Extensionオブジェクトのリスト
    """
    extensions = []

    for pyx_file, module_name in find_pyx_files(SRC_DIR):
        # プロジェクトルートからの相対パスを取得
        project_root = SRC_DIR.parent.resolve()
        rel_path = pyx_file.relative_to(project_root)
        extensions.append(
            Extension(
                module_name,
                [str(rel_path)],
            )
        )
    return extensions


# 自動検出されたすべての.pyxファイルから拡張モジュールを作成
extensions = create_extensions()

# cythonizeを使って拡張モジュールをコンパイル
# setup()はpyproject.tomlから設定を読み込むため、ここではext_modulesのみ指定
setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
        },
    ),
)
