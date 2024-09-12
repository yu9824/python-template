import importlib.util
import inspect
import sys

# deprecated in python >=3.12
from typing import TypeVar

if sys.version_info >= (3, 9):
    from collections.abc import Callable
else:
    from typing import Callable

T = TypeVar("T")


def is_installed(package_name: str) -> bool:
    """Check if the package is installed.

    Parameters
    ----------
    package_name : str
        package name like `sklearn`

    Returns
    -------
    bool
        if installed, True
    """
    return bool(importlib.util.find_spec(package_name))


def dummy_func(x: T, *args, **kwargs) -> T:
    """dummy function

    Parameters
    ----------
    x : T
        Anything

    Returns
    -------
    T
        same as input
    """
    return x


def is_argument(_callable: Callable, arg_name: str) -> bool:
    """Check to see if it is included in the callable argument.

    Parameters
    ----------
    _callable : Callable

    arg_name : str
        argument name

    Returns
    -------
    bool
        if included, True
    """
    return arg_name in set(inspect.signature(_callable).parameters.keys())
