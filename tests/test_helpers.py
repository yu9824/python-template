"""Tests of ``python_template.helpers``."""

from __future__ import annotations

import subprocess
import sys

import pytest

import python_template.helpers
from python_template.helpers import (
    dummy_tqdm,
    is_argument,
    is_installed,
    tqdm_joblib,
)
from python_template.helpers._helpers import deprecated


def test_all_public_names_are_importable():
    for name in python_template.helpers.__all__:
        assert hasattr(python_template.helpers, name)


# --- is_installed ------------------------------------------------------------


@pytest.mark.parametrize("package_name", ["sys", "pytest", "python_template"])
def test_is_installed_returns_true_for_an_installed_package(package_name):
    assert is_installed(package_name) is True


def test_is_installed_returns_false_for_a_missing_package():
    assert is_installed("python_template_package_that_does_not_exist") is False


def test_is_installed_returns_false_for_a_blocked_package(monkeypatch):
    # A None entry in sys.modules makes the package look missing. Tests of
    # optional dependencies rely on this.
    monkeypatch.setitem(sys.modules, "json", None)

    assert is_installed("json") is False


# --- is_argument -------------------------------------------------------------


def _function(alpha, beta=1, *args, gamma=None, **kwargs):
    """Take parameters of every kind (used by the tests of is_argument)."""


class _Model:
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, sample_weight=None):
        return self


@pytest.mark.parametrize("arg_name", ["alpha", "beta", "gamma"])
def test_is_argument_returns_true_for_a_parameter(arg_name):
    assert is_argument(_function, arg_name) is True


@pytest.mark.parametrize("arg_name", ["delta", "Alpha", ""])
def test_is_argument_returns_false_for_a_missing_parameter(arg_name):
    # ``**kwargs`` does not make every name a parameter.
    assert is_argument(_function, arg_name) is False


def test_is_argument_inspects_classes_and_bound_methods():
    assert is_argument(_Model, "alpha") is True
    assert is_argument(_Model().fit, "sample_weight") is True
    assert is_argument(_Model().fit, "eval_set") is False
    # Neither a class nor a bound method shows ``self``.
    assert is_argument(_Model, "self") is False
    assert is_argument(_Model().fit, "self") is False


# --- dummy_tqdm --------------------------------------------------------------


@pytest.mark.parametrize(
    ("make_iterable", "expected"),
    [
        (lambda: [3, 1, 2], [3, 1, 2]),
        (lambda: (3, 1, 2), [3, 1, 2]),
        (lambda: range(3), [0, 1, 2]),
        (lambda: (value for value in [3, 1, 2]), [3, 1, 2]),
        (lambda: iter([3, 1, 2]), [3, 1, 2]),
        (lambda: {"b": 1, "a": 2}, ["b", "a"]),
    ],
    ids=["list", "tuple", "range", "generator", "iterator", "dict"],
)
def test_dummy_tqdm_iterates_the_iterable_in_order(make_iterable, expected):
    assert list(dummy_tqdm(make_iterable())) == expected


def test_dummy_tqdm_ignores_the_arguments_of_tqdm():
    progress_bar = dummy_tqdm([1, 2], desc="fit", total=2, leave=False)

    assert list(progress_bar) == [1, 2]


@pytest.mark.parametrize(
    "progress_bar",
    [dummy_tqdm(), dummy_tqdm(total=3)],
    ids=["no-arguments", "total"],
)
def test_dummy_tqdm_without_an_iterable_is_empty(progress_bar):
    assert list(progress_bar) == []


@pytest.mark.parametrize(
    "method",
    ["update", "close", "refresh", "reset", "set_description", "set_postfix"],
)
def test_dummy_tqdm_accepts_calls_and_does_nothing(method):
    progress_bar = dummy_tqdm([1, 2, 3], total=3)

    assert getattr(progress_bar, method)() is None
    assert getattr(progress_bar, method)(1, n=2, desc="fit") is None
    # The calls do not change the iteration.
    assert list(progress_bar) == [1, 2, 3]


def test_dummy_tqdm_accepts_update_while_iterating():
    progress_bar = dummy_tqdm(["x", "y"])
    seen = []
    for value in progress_bar:
        progress_bar.update(1)
        seen.append(value)
    progress_bar.close()

    assert seen == ["x", "y"]


# --- deprecated --------------------------------------------------------------


def _deprecated_function(reason=None):
    @deprecated(reason)
    def old(value):
        """Return the value."""
        return value

    return old


def test_deprecated_warns_with_the_reason_and_returns_the_result():
    old = _deprecated_function("Use new instead.")

    with pytest.warns(DeprecationWarning) as record:
        assert old(3) == 3

    assert len(record) == 1
    assert str(record[0].message) == "old is deprecated. Use new instead."
    # stacklevel=2 attributes the warning to the caller, not the wrapper.
    assert record[0].filename == __file__


def test_deprecated_without_a_reason_warns_with_the_name_only():
    old = _deprecated_function()

    with pytest.warns(DeprecationWarning) as record:
        old(3)

    assert str(record[0].message) == "old is deprecated."


def test_deprecated_keeps_the_metadata_and_marks_the_docstring():
    old = _deprecated_function("Use new instead.")

    assert old.__name__ == "old"
    assert old.__doc__ == (
        ".. deprecated::\n    Use new instead.\n\nReturn the value."
    )


# --- tqdm_joblib without joblib ----------------------------------------------
# The tests that run joblib are in test_tqdm_joblib.py.


def test_importing_helpers_does_not_import_joblib():
    # A fresh interpreter, since this one may have imported joblib already.
    code = (
        "import sys, python_template.helpers; print('joblib' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "False"


def test_tqdm_joblib_without_joblib_raises_import_error(monkeypatch):
    # A None entry in sys.modules makes the package look missing.
    monkeypatch.setitem(sys.modules, "joblib", None)
    progress = tqdm_joblib(total=1)

    with pytest.raises(ImportError, match="pip install joblib") as excinfo:
        with progress:
            pass

    assert excinfo.value.name == "joblib"
    # No progress bar is made before the error.
    assert progress.tqdm is None
