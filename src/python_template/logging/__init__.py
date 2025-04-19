"""This module provides a set of utilities for logging in Python.

It includes functions to configure logging behavior, such as enabling or disabling
the default handler, retrieving a child logger, and accessing the root logger.
Additionally, this module defines constants for various logging levels to be used
in logging configurations.

Functions
---------
- enable_default_handler: Enables the default handler for the root logger.
- disable_default_handler: Disables the default handler for the root logger.
- get_child_logger: Retrieves a child logger associated with the given module name.
- get_handler: Configures and returns a logger handler.
- get_root_logger: Retrieves the root logger of the package.
- catch_default_handler: Context manager for temporarily disabling the default handler.

Logging Levels
--------------
- CRITICAL: Level 50, for critical error messages.
- ERROR: Level 40, for error messages.
- WARNING: Level 30, for warnings.
- INFO: Level 20, for informational messages.
- DEBUG: Level 10, for debug messages.
- NOTSET: Level 0, used to indicate that no level is set.
"""

from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING

from ._logging import (
    catch_default_handler,
    disable_default_handler,
    enable_default_handler,
    get_child_logger,
    get_handler,
    get_root_logger,
)

__all__ = (
    "catch_default_handler",
    "disable_default_handler",
    "enable_default_handler",
    "get_child_logger",
    "get_handler",
    "get_root_logger",
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "INFO",
    "NOTSET",
    "WARNING",
)
