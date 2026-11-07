""""""

from pathlib import Path

# _version.py はビルド時に setuptools-scm が書き出す (git では追跡しない)。
# 無いときの注意は pyproject.toml の [tool.setuptools_scm] を参照。
_version_file = Path(__file__).parent / "_version.py"

if _version_file.is_file():
    from ._version import __version__
else:
    __version__ = "unknown"

__license__ = "MIT"
__author__ = "yu9824"
__copyright__ = "Copyright © 2026 yu9824"

# __all__ = ()
