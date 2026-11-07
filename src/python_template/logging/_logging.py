import importlib.util
import os
from logging import (
    INFO,
    NOTSET,
    Formatter,
    Handler,
    Logger,
    NullHandler,
    StreamHandler,
    getLogger,
)
from types import TracebackType
from typing import TypeVar

HandlerType = TypeVar("HandlerType", bound=Handler)


def _should_color(handler: Handler) -> bool:
    """
    Check whether the output of a handler should be colored.

    Color is used only when the handler writes to a terminal and the
    `NO_COLOR` environment variable is not set. A handler without a stream
    (e.g., `QueueHandler`) or writing to a file or buffer gets no color, so
    no color codes end up there.

    Parameters
    ----------
    handler : Handler
        The handler to check.

    Returns
    -------
    bool
        True if the output should be colored, False otherwise.
    """
    if os.environ.get("NO_COLOR"):
        return False

    isatty = getattr(getattr(handler, "stream", None), "isatty", None)
    return callable(isatty) and bool(isatty())


_default_handler: StreamHandler | None = None
"""default root logger handler

if not configured, None
"""


def _get_library_name() -> str:
    """
    Get the root package name for logger configuration.

    Extracts the top-level package name from the current module's `__name__`.
    This is used as the root logger name to ensure proper logger hierarchy
    within the package.

    Returns
    -------
    str
        The root package name (e.g., 'python_template').

    Examples
    --------
    If called from `python_template.logging._logging`, returns
    'python_template'.
    """
    return __name__.split(".")[0]


def create_default_formatter(use_color: bool = False) -> Formatter:
    """
    Create the default log formatter.

    The format is ``%(asctime)s - %(name)s:%(lineno)d[%(levelname)s] -
    %(message)s``. With `use_color`, the level name is colored by
    `colorlog`'s `ColoredFormatter`; without `colorlog`, the formatter is
    plain anyway.

    Parameters
    ----------
    use_color : bool, optional
        Whether to color the level name. Default is False.

    Returns
    -------
    Formatter
        A `ColoredFormatter` if `use_color` is True and `colorlog` is
        installed, a plain `logging.Formatter` otherwise.
    """
    if use_color and importlib.util.find_spec("colorlog"):
        from colorlog import ColoredFormatter

        return ColoredFormatter(
            "%(asctime)s - %(name)s:%(lineno)d"
            "%(log_color)s[%(levelname)s]%(reset)s - %(message)s"
        )
    return Formatter(
        "%(asctime)s - %(name)s:%(lineno)d[%(levelname)s] - %(message)s"
    )


def get_handler(
    handler: HandlerType,
    formatter: Formatter | None = None,
    level: int = NOTSET,
) -> HandlerType:
    """Configure a log handler with a formatter and log level.

    This function provides a convenient way to configure logging handlers
    by setting both the formatter and log level in a single call. If no
    formatter is specified, the default formatter is used, colored only if
    the handler writes to a terminal (e.g., `StreamHandler` on stderr or
    stdout) and the `NO_COLOR` environment variable is not set. A handler
    writing to a file or anywhere else gets no color codes.

    Parameters
    ----------
    handler : HandlerType
        The log handler instance to configure (e.g., `StreamHandler`,
        `FileHandler`). The handler will be modified in place.
    formatter : Optional[Formatter], optional
        The formatter to apply to the handler. If `None`, the default
        formatter is used as described above. Default is `None`.
    level : int, optional
        The logging level threshold for the handler. Only messages at or
        above this level will be processed. Use constants from the `logging`
        module (e.g., `logging.DEBUG`, `logging.INFO`, `logging.WARNING`).
        Default is `logging.NOTSET`.

    Returns
    -------
    HandlerType
        The configured handler instance (same object as the input `handler`).

    Examples
    --------
    >>> from logging import StreamHandler, FileHandler, INFO
    >>> # Colored if stderr is a terminal
    >>> stream_handler = get_handler(StreamHandler(), level=INFO)
    >>> logger.addHandler(stream_handler)
    >>>
    >>> # Never colored
    >>> file_handler = get_handler(FileHandler('app.log'), level=INFO)
    >>> logger.addHandler(file_handler)
    """
    handler.setLevel(level)
    if formatter is None:
        formatter = create_default_formatter(use_color=_should_color(handler))
    handler.setFormatter(formatter)
    return handler


def _create_default_handler() -> StreamHandler:
    """
    Create and configure the default stream handler for the library.

    This function creates a `StreamHandler` that writes to `sys.stderr` and
    configures it with the default formatter and log level. This handler is
    used as the default handler for the library's root logger.

    Returns
    -------
    StreamHandler
        A configured `StreamHandler` instance with the default formatter
        and log level applied.

    See Also
    --------
    get_handler : Configure a handler with formatter and level.
    _configure_library_root_logger : Set up the root logger with this handler.
    """
    return get_handler(StreamHandler())


def _configure_library_root_logger() -> None:
    """
    Configure the library's root logger with default settings.

    This function performs one-time initialization of the library's root
    logger. It creates and attaches a default stream handler, sets the logging
    level to `INFO`, and disables propagation to prevent duplicate log
    messages from appearing in parent loggers. This function is idempotent and
    safe to call multiple times; configuration is only applied once.

    The configuration includes:
    - A default stream handler writing to `sys.stderr`
    - Logging level set to `INFO`
    - Propagation disabled to avoid duplicate messages

    Returns
    -------
    None

    See Also
    --------
    get_library_root_logger : Get the configured root logger.
    _create_default_handler : Create the default handler.
    """
    global _default_handler

    if _default_handler:
        # This library has already configured the library root logger.
        return

    _default_handler = _create_default_handler()

    # Apply our default configuration to the library root logger.
    library_root_logger = get_library_root_logger()
    library_root_logger.addHandler(_default_handler)
    library_root_logger.setLevel(INFO)
    library_root_logger.propagate = False


def _reset_library_root_logger() -> None:
    """
    Reset the library's root logger to its initial configuration.

    This function removes every handler from the root logger, discards the
    default handler, and configures the root logger again as on first use:
    a new default handler is attached, the logging level is set to `INFO`,
    and propagation is disabled.

    This is primarily used internally for testing or cleanup purposes.
    Regular users should use `disable_default_handler()` instead.

    Returns
    -------
    None

    See Also
    --------
    disable_default_handler : Disable the default handler (recommended).
    _configure_library_root_logger : Reconfigure the root logger.
    """
    global _default_handler
    _default_handler = None

    # Not through get_library_root_logger(): it would configure the logger,
    # and the new default handler would then be removed below with the rest.
    library_root_logger = getLogger(_get_library_name())
    for _handler in library_root_logger.handlers.copy():
        library_root_logger.removeHandler(_handler)

    _configure_library_root_logger()


def get_library_root_logger() -> Logger:
    """
    Get the root logger for this library package.

    This function returns the root logger for the library, ensuring it is
    properly configured with a default handler and logging level. The logger
    name corresponds to the top-level package name (e.g., 'python_template').

    The logger is automatically configured on first access with:

    - Default stream handler (with color support if available)
    - Logging level set to `INFO`
    - Propagation disabled

    Returns
    -------
    Logger
        The configured root logger instance for the library package.

    Examples
    --------
    >>> logger = get_library_root_logger()
    >>> logger.info("Library initialized")
    python_template - INFO - Library initialized

    See Also
    --------
    get_child_logger : Get a child logger for a specific module.
    """
    _configure_library_root_logger()

    return getLogger(_get_library_name())


def get_child_logger(name: str) -> Logger:
    """
    Get the logger for a module of the library.

    Pass `__name__` as `name`. The logger is placed under the library's root
    logger, so its messages go to the library's handlers.

    Parameters
    ----------
    name : str
        The module name, typically `__name__`. Must be either:

        - The library name itself (in the package's `__init__.py`), which
          gives the library's root logger
        - A name within the library's namespace
          (e.g., 'python_template.module')
        - The string '__main__' for scripts executed directly

    Returns
    -------
    Logger
        The logger for the module.

    Raises
    ------
    ValueError
        If `name` is none of the above.

    Examples
    --------
    >>> # In a module: python_template/utils.py
    >>> logger = get_child_logger(__name__)
    >>> logger.info("Module loaded")
    2026-01-01 00:00:00,000 - python_template.utils:3[INFO] - Module loaded
    """
    root_logger = get_library_root_logger()
    library_name = root_logger.name

    if name == library_name:
        return root_logger
    if name.startswith(f"{library_name}.") or name == "__main__":
        return root_logger.getChild(name.removeprefix(f"{library_name}."))
    raise ValueError(
        "get_child_logger() takes the name of a module in "
        f"'{library_name}' or '__main__', but got {name!r}. "
        "Call it as get_child_logger(__name__)."
    )


def enable_default_handler() -> None:
    """
    Enable the default handler for the library's root logger.

    This function re-attaches the default stream handler to the root logger
    if it has been previously removed (e.g., by `disable_default_handler()`).
    If the handler was never configured, it will be created and attached.

    This is useful for restoring logging output after it has been temporarily
    disabled, or for ensuring logging is enabled after a clean state.

    Returns
    -------
    None

    See Also
    --------
    disable_default_handler : Remove the default handler.
    catch_default_handler : Context manager to temporarily disable the handler.
    """
    _configure_library_root_logger()

    assert _default_handler is not None
    get_library_root_logger().addHandler(_default_handler)


def disable_default_handler() -> None:
    """
    Disable the default handler for the library's root logger.

    This function removes the default stream handler from the root logger,
    effectively suppressing all logging output from the library. The handler
    is not deleted and can be re-attached later using
    `enable_default_handler()`.

    This is useful for:

    - Temporarily suppressing output during testing
    - Allowing users to configure their own handlers without interference
    - Reducing noise in specific execution contexts

    Returns
    -------
    None

    See Also
    --------
    enable_default_handler : Re-attach the default handler.
    catch_default_handler : Context manager to temporarily disable the handler.
    """
    _configure_library_root_logger()

    assert _default_handler is not None
    get_library_root_logger().removeHandler(_default_handler)


class catch_default_handler:
    """
    Context manager to temporarily suppress the default logging handler.

    This context manager allows you to temporarily disable the default handler
    for the library's root logger. When entering the context, the default
    handler is removed, suppressing all logging output. When exiting (even if
    an exception occurs), the handler is restored if it was attached when
    entering, so a handler disabled beforehand stays disabled and nested
    contexts keep the outer one in effect.

    This is particularly useful for:

    - Suppressing logs during test execution
    - Creating cleaner output in specific code sections
    - Temporarily redirecting all logging to custom handlers

    Examples
    --------
    >>> from python_template.logging import (
    ...     get_child_logger,
    ...     catch_default_handler,
    ... )
    >>> logger = get_child_logger(__name__)
    >>>
    >>> logger.info("This will be logged")
    >>> with catch_default_handler():
    ...     logger.info("This message will not be logged")
    ...     logger.debug("Neither will this")
    >>> logger.info("This will be logged again")
    """

    def __init__(self) -> None:
        self._null_handler = NullHandler()
        # Whether the default handler was attached on entering, or None
        # while the context is not active.
        self._was_attached: bool | None = None

    def __enter__(self) -> None:
        """
        Enter the context and disable the default handler.

        Raises
        ------
        RuntimeError
            If the context is already active (use another instance to nest
            contexts).
        """
        if self._was_attached is not None:
            raise RuntimeError(
                "This catch_default_handler is already active; use another "
                "instance to nest contexts."
            )
        root_logger = get_library_root_logger()
        self._was_attached = _default_handler in root_logger.handlers
        disable_default_handler()
        # Without any handler, logging falls back to its last resort handler
        # and still prints warnings and errors to stderr.
        root_logger.addHandler(self._null_handler)

    def __exit__(
        self,
        exc_type: "type[Exception] | None",
        exc_value: Exception | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exit the context and restore the default handler if it was attached.

        Raises
        ------
        RuntimeError
            If the context is not active.
        """
        if self._was_attached is None:
            raise RuntimeError(
                "This catch_default_handler is not active; exit it only "
                "after entering it."
            )
        was_attached = self._was_attached
        self._was_attached = None
        get_library_root_logger().removeHandler(self._null_handler)
        if was_attached:
            enable_default_handler()


class catch_all_handler:
    """
    Context manager to temporarily suppress all handlers of the root logger.

    This context manager removes every handler from the library's root logger
    when entering the context, and restores them when exiting (even if an
    exception occurs). Unlike `catch_default_handler`, this also affects
    custom handlers added to the root logger. Handlers added directly to a
    child logger are not affected.

    This is useful for:

    - Completely suppressing all logging output during specific operations
    - Testing code paths without any logging interference

    Examples
    --------
    >>> from python_template.logging import (
    ...     get_child_logger,
    ...     get_library_root_logger,
    ...     catch_all_handler,
    ... )
    >>> get_library_root_logger().addHandler(custom_handler)
    >>> logger = get_child_logger(__name__)
    >>>
    >>> logger.info("This will be logged by all handlers")
    >>> with catch_all_handler():
    ...     logger.info("No handlers active - this won't be logged")
    ...     logger.error("Errors are also suppressed")
    >>> logger.info("All handlers restored - this will be logged again")
    """

    def __init__(self) -> None:
        self._null_handler = NullHandler()
        # The handlers removed on entering, or None while the context is not
        # active.
        self._handlers: list[Handler] | None = None

    def __enter__(self) -> None:
        """
        Enter the context and remove all handlers from the root logger.

        Raises
        ------
        RuntimeError
            If the context is already active (use another instance to nest
            contexts).
        """
        if self._handlers is not None:
            raise RuntimeError(
                "This catch_all_handler is already active; use another "
                "instance to nest contexts."
            )
        root_logger = get_library_root_logger()
        self._handlers = root_logger.handlers.copy()
        for handler in self._handlers:
            root_logger.removeHandler(handler)
        # Without any handler, logging falls back to its last resort handler
        # and still prints warnings and errors to stderr.
        root_logger.addHandler(self._null_handler)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exit the context and restore the removed handlers in order.

        Raises
        ------
        RuntimeError
            If the context is not active.
        """
        if self._handlers is None:
            raise RuntimeError(
                "This catch_all_handler is not active; exit it only after "
                "entering it."
            )
        handlers = self._handlers
        self._handlers = None
        root_logger = get_library_root_logger()
        root_logger.removeHandler(self._null_handler)
        for handler in handlers:
            root_logger.addHandler(handler)
