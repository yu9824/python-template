import importlib.util
import inspect
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Generic, TypeVar

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


def is_argument(__callable: "Callable[..., Any]", arg_name: str) -> bool:
    """Check to see if it is included in the callable argument.

    Parameters
    ----------
    __callable : Callable

    arg_name : str
        argument name

    Returns
    -------
    bool
        if included, True
    """
    return arg_name in set(inspect.signature(__callable).parameters.keys())


# HACK: when drop python3.8, use `dummy_tqdm(Iterable[T])`
class dummy_tqdm(Iterable, Generic[T]):
    """dummy class for 'tqdm'

    Parameters
    ----------
    __iterable : Iterable[T]
        iterable object
    """

    def __init__(self, __iterable: "Iterable[T]", *args, **kwargs) -> None:
        self.__iterable = __iterable

    def __iter__(self) -> "Iterator[T]":
        return iter(self.__iterable)

    def __getattr__(self, name: str) -> "Callable[..., None]":
        return self.__no_operation

    @staticmethod
    def __no_operation(*args, **kwargs) -> None:
        """no-operation"""
        return
