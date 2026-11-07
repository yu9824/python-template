""""""

from importlib.metadata import PackageNotFoundError, version

# バージョンは setuptools-scm が git タグから決め、インストール時に
# メタデータへ書き込まれる。そこから読むので、インストールせずに
# src を直接 import したときは "unknown" になる。
try:
    __version__ = version("python-template")
except PackageNotFoundError:
    __version__ = "unknown"

__license__ = "MIT"
__author__ = "yu9824"
__copyright__ = "Copyright © 2026 yu9824"

# __all__ = ()
