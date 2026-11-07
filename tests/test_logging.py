"""Tests of ``python_template.logging``."""

from __future__ import annotations

import io
import logging
import logging.handlers
import queue
import sys

import pytest

import python_template.logging
from python_template.logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    NOTSET,
    WARNING,
    _logging,
    catch_all_handler,
    catch_default_handler,
    disable_default_handler,
    enable_default_handler,
    get_child_logger,
    get_handler,
    get_library_root_logger,
)

LIBRARY_NAME = "python_template"


@pytest.fixture(autouse=True)
def _fresh_library_logger():
    """Give each test a newly configured library root logger."""
    _logging._reset_library_root_logger()
    yield
    _logging._reset_library_root_logger()


def _default_handler() -> logging.StreamHandler:
    """Return the default handler, configuring the logger if needed."""
    get_library_root_logger()
    handler = _logging._default_handler
    assert handler is not None
    return handler


def _handlers() -> list[logging.Handler]:
    """Return the handlers of the library root logger, except pytest's.

    During a test, pytest attaches its capture handler to every logger that
    does not propagate, which includes the library root logger.
    """
    return [
        handler
        for handler in get_library_root_logger().handlers
        if not type(handler).__module__.startswith("_pytest")
    ]


def _is_attached() -> bool:
    """Return whether the default handler is attached to the root logger."""
    return _default_handler() in _handlers()


def _capture_default_handler() -> io.StringIO:
    """Make the default handler write to a new buffer and return it."""
    stream = io.StringIO()
    _default_handler().setStream(stream)
    return stream


class _ListHandler(logging.Handler):
    """Collect the messages of the records it handles."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


# --- Public names ------------------------------------------------------------


def test_all_public_names_are_importable():
    for name in python_template.logging.__all__:
        assert hasattr(python_template.logging, name)


def test_level_constants_are_the_standard_library_values():
    assert (CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING) == (
        logging.CRITICAL,
        logging.DEBUG,
        logging.ERROR,
        logging.INFO,
        logging.NOTSET,
        logging.WARNING,
    )


# --- get_library_root_logger -------------------------------------------------


def test_get_library_root_logger_configures_the_library_logger():
    logger = get_library_root_logger()

    assert logger is logging.getLogger(LIBRARY_NAME)
    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert _handlers() == [_default_handler()]


def test_get_library_root_logger_configures_the_logger_only_once():
    get_library_root_logger()
    get_library_root_logger()

    assert _handlers() == [_default_handler()]


def test_reset_library_root_logger_attaches_a_new_default_handler():
    old_handler = _default_handler()
    get_library_root_logger().addHandler(_ListHandler())
    get_library_root_logger().setLevel(logging.DEBUG)

    _logging._reset_library_root_logger()

    assert _default_handler() is not old_handler
    assert _handlers() == [_default_handler()]
    assert get_library_root_logger().level == logging.INFO


def test_default_handler_writes_info_and_above():
    stream = _capture_default_handler()
    logger = get_child_logger(f"{LIBRARY_NAME}.module")

    logger.debug("hidden")
    logger.info("shown")

    output = stream.getvalue()
    assert "hidden" not in output
    assert f"{LIBRARY_NAME}.module" in output
    assert "[INFO] - shown" in output


# --- get_child_logger --------------------------------------------------------


def test_get_child_logger_returns_a_logger_under_the_library():
    logger = get_child_logger(f"{LIBRARY_NAME}.sub.module")

    assert logger.name == f"{LIBRARY_NAME}.sub.module"
    assert logger.getEffectiveLevel() == logging.INFO


def test_get_child_logger_accepts_main():
    assert get_child_logger("__main__").name == f"{LIBRARY_NAME}.__main__"


def test_get_child_logger_returns_the_root_logger_for_the_package_itself():
    # __name__ in the package's own __init__.py is the library name.
    assert get_child_logger(LIBRARY_NAME) is get_library_root_logger()


@pytest.mark.parametrize(
    "name", ["", "other", "other.module", f"{LIBRARY_NAME}_x.module"]
)
def test_get_child_logger_rejects_a_name_outside_the_library(name):
    with pytest.raises(ValueError) as excinfo:
        get_child_logger(name)

    # The message shows what was passed and how to call it instead.
    assert repr(name) in str(excinfo.value)
    assert "get_child_logger(__name__)" in str(excinfo.value)


# --- enable_default_handler / disable_default_handler ------------------------


def test_disable_and_enable_never_duplicate_the_handler():
    disable_default_handler()
    disable_default_handler()
    assert not _is_attached()

    enable_default_handler()
    enable_default_handler()
    assert _handlers() == [_default_handler()]


# --- catch_default_handler ---------------------------------------------------


def test_catch_default_handler_suppresses_the_messages(capsys):
    stream = _capture_default_handler()
    logger = get_child_logger(f"{LIBRARY_NAME}.module")

    with catch_default_handler():
        logger.warning("inside")
    logger.warning("outside")

    assert "inside" not in stream.getvalue()
    assert "outside" in stream.getvalue()
    # Python's last resort handler does not print the message either.
    assert "inside" not in capsys.readouterr().err


def test_catch_default_handler_restores_an_attached_handler():
    with catch_default_handler():
        assert not _is_attached()

    assert _handlers() == [_default_handler()]


def test_catch_default_handler_restores_on_an_exception():
    with pytest.raises(KeyError, match="body"), catch_default_handler():
        raise KeyError("body")

    assert _handlers() == [_default_handler()]


def test_catch_default_handler_keeps_a_detached_handler():
    disable_default_handler()

    with catch_default_handler():
        pass

    assert not _is_attached()
    assert _handlers() == []


def test_nested_catch_default_handler_keeps_the_outer_one_active():
    stream = _capture_default_handler()
    logger = get_child_logger(f"{LIBRARY_NAME}.module")

    with catch_default_handler():
        with catch_default_handler():
            pass
        # Back in the outer context only: still suppressed.
        assert not _is_attached()
        logger.warning("between")

    assert "between" not in stream.getvalue()
    assert _handlers() == [_default_handler()]


def test_catch_default_handler_cannot_be_entered_while_active():
    context = catch_default_handler()

    with context:
        with pytest.raises(RuntimeError, match="already active"):
            context.__enter__()
        assert not _is_attached()

    assert _handlers() == [_default_handler()]


def test_catch_default_handler_cannot_be_exited_before_entered():
    with pytest.raises(RuntimeError, match="not active"):
        catch_default_handler().__exit__(None, None, None)

    assert _handlers() == [_default_handler()]


# --- catch_all_handler -------------------------------------------------------


def test_catch_all_handler_suppresses_every_handler(capsys):
    custom_handler = _ListHandler()
    get_library_root_logger().addHandler(custom_handler)
    stream = _capture_default_handler()
    logger = get_child_logger(f"{LIBRARY_NAME}.module")

    with catch_all_handler():
        logger.error("inside")
    logger.error("outside")

    assert custom_handler.messages == ["outside"]
    assert "inside" not in stream.getvalue()
    assert "inside" not in capsys.readouterr().err


def test_catch_all_handler_restores_the_handlers_in_order():
    custom_handler = _ListHandler()
    root_logger = get_library_root_logger()
    root_logger.addHandler(custom_handler)

    with pytest.raises(KeyError, match="body"), catch_all_handler():
        assert all(
            isinstance(handler, logging.NullHandler)
            for handler in root_logger.handlers
        )
        raise KeyError("body")

    assert _handlers() == [_default_handler(), custom_handler]


def test_catch_all_handler_cannot_be_entered_while_active():
    context = catch_all_handler()

    with context, pytest.raises(RuntimeError, match="already active"):
        context.__enter__()

    assert _handlers() == [_default_handler()]


def test_catch_all_handler_cannot_be_exited_before_entered():
    with pytest.raises(RuntimeError, match="not active"):
        catch_all_handler().__exit__(None, None, None)


# --- get_handler / formatters ------------------------------------------------


def test_get_handler_sets_the_level_and_formatter():
    formatter = logging.Formatter("%(message)s")
    handler = logging.StreamHandler(io.StringIO())

    configured = get_handler(handler, formatter=formatter, level=WARNING)

    assert configured is handler
    assert handler.level == WARNING
    assert handler.formatter is formatter


class _TerminalStream(io.StringIO):
    """A buffer that claims to be a terminal."""

    def isatty(self) -> bool:
        return True


def test_get_handler_colors_a_stream_to_a_terminal(monkeypatch):
    pytest.importorskip("colorlog")
    from colorlog import ColoredFormatter

    monkeypatch.delenv("NO_COLOR", raising=False)
    # What counts is the handler's own stream, not stderr.
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    handler = get_handler(logging.StreamHandler(_TerminalStream()))

    assert isinstance(handler.formatter, ColoredFormatter)


@pytest.mark.parametrize(
    "make_handler",
    [
        lambda tmp_path: logging.FileHandler(tmp_path / "log.txt"),
        lambda tmp_path: logging.StreamHandler(io.StringIO()),
        lambda tmp_path: logging.handlers.QueueHandler(queue.Queue()),
    ],
    ids=["file", "buffer", "queue"],
)
def test_get_handler_gives_a_handler_off_the_terminal_a_plain_formatter(
    make_handler, tmp_path, monkeypatch
):
    # Color codes must not reach a file, buffer or queue, even when stderr
    # is a terminal.
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(sys, "stderr", _TerminalStream())
    handler = make_handler(tmp_path)
    try:
        get_handler(handler)
        assert type(handler.formatter) is logging.Formatter
    finally:
        handler.close()


def test_get_handler_respects_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(sys, "stderr", _TerminalStream())

    handler = get_handler(logging.StreamHandler(_TerminalStream()))

    assert type(handler.formatter) is logging.Formatter


def test_create_default_formatter_follows_use_color():
    pytest.importorskip("colorlog")
    from colorlog import ColoredFormatter

    colored = _logging.create_default_formatter(use_color=True)
    plain = _logging.create_default_formatter(use_color=False)

    assert isinstance(colored, ColoredFormatter)
    assert type(plain) is logging.Formatter
