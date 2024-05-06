# ruff : noqa : F401
"""utils module"""

from ._utils import is_installed

# _utils.pyだと、_が入っているのでドキュメント化されない。
# ドキュメント化したい場合は、ぼジュールメソッドとして登録するため、__all__に入れる。
__all__ = ["is_installed"]
