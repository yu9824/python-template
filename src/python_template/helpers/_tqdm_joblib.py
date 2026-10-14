from __future__ import annotations

import functools
import threading
from collections.abc import Callable
from types import TracebackType
from typing import Any

from ._helpers import dummy_tqdm, is_installed

# joblib is an optional dependency: it is imported only where Parallel is
# replaced, so that importing this package works without it.

#: Name of the attribute of a ``Parallel`` instance that binds its running
#: call to the progress of a ``tqdm_joblib`` context, as ``(progress, base)``.
_BINDING_ATTRIBUTE = "_python_template_tqdm_joblib_binding"


class _Progress:
    """Progress of one active ``tqdm_joblib`` context.

    Parameters
    ----------
    progress_bar : tqdm or dummy_tqdm
        The progress bar to move forward.
    """

    def __init__(self, progress_bar: Any) -> None:
        self.progress_bar = progress_bar
        # Whether a counted call is running. Only the thread that entered
        # the context reads and writes it.
        self.tracking = False
        # Guards the attributes below and the progress bar. joblib is never
        # called while it is held.
        self._lock = threading.Lock()
        # The number of tasks finished by the counted calls that have ended.
        self._total = 0
        # How far the progress bar has been moved.
        self._position = 0
        self._closed = False

    def start_call(self) -> int:
        """Mark a counted call as running.

        Returns
        -------
        int
            The number of tasks finished by the counted calls so far, which
            is where the progress of the new call starts.
        """
        self.tracking = True
        with self._lock:
            return self._total

    def advance_to(self, position: int) -> None:
        """Move the progress bar forward to ``position``.

        Parameters
        ----------
        position : int
            The number of finished tasks. Nothing happens if the bar is
            already there or further, or if it is closed.
        """
        with self._lock:
            self._advance_to(position)

    def finish_call(self, total: int) -> None:
        """Mark the counted call as ended and move the bar to ``total``.

        Parameters
        ----------
        total : int
            The number of tasks finished by the counted calls, including
            the call that ended.
        """
        self.tracking = False
        with self._lock:
            self._total = total
            self._advance_to(total)

    def close(self) -> None:
        """Close the progress bar; it is not moved any more."""
        with self._lock:
            self._closed = True
        self.progress_bar.close()

    def _advance_to(self, position: int) -> None:
        if self._closed or position <= self._position:
            return
        self.progress_bar.update(position - self._position)
        self._position = position


#: The stacks of the active contexts, one stack per thread.
_ACTIVE_CONTEXTS = threading.local()


def _progress_stack() -> list[_Progress]:
    """Return the stack of the active contexts of the current thread."""
    stack = getattr(_ACTIVE_CONTEXTS, "stack", None)
    if stack is None:
        stack = _ACTIVE_CONTEXTS.stack = []
    return stack


def _make_tracking_methods(
    original_call: Callable[..., Any],
    original_print_progress: Callable[..., Any],
) -> tuple[Callable[..., Any], Callable[..., Any]]:
    """Return ``Parallel.__call__`` and ``Parallel.print_progress`` that count.

    The original methods are kept in the closures, so the returned methods
    keep working after the originals are restored: with loky, joblib may call
    ``print_progress`` of a call from its callback thread after the call has
    returned, or even after the context has exited.

    Parameters
    ----------
    original_call : callable
        The original ``Parallel.__call__``.
    original_print_progress : callable
        The original ``Parallel.print_progress``.

    Returns
    -------
    tuple of callable
        The replacements of ``__call__`` and ``print_progress``.
    """

    @functools.wraps(original_call)
    def tracking_call(self, *args, **kwargs):
        stack = _progress_stack()
        if (
            not stack
            or stack[-1].tracking
            # The call returns a generator before its tasks run.
            or getattr(self, "return_generator", False)
        ):
            return original_call(self, *args, **kwargs)

        progress = stack[-1]
        base = progress.start_call()
        setattr(self, _BINDING_ATTRIBUTE, (progress, base))
        try:
            return original_call(self, *args, **kwargs)
        finally:
            try:
                progress.finish_call(
                    base + getattr(self, "n_completed_tasks", 0)
                )
            finally:
                setattr(self, _BINDING_ATTRIBUTE, None)

    @functools.wraps(original_print_progress)
    def tracking_print_progress(self):
        # Read the binding once: the call may end and unbind it meanwhile.
        # The position is the same however often it is computed for a call.
        binding = getattr(self, _BINDING_ATTRIBUTE, None)
        if binding is not None:
            progress, base = binding
            progress.advance_to(base + self.n_completed_tasks)
        return original_print_progress(self)

    return tracking_call, tracking_print_progress


class _ParallelPatch:
    """Replace methods of ``joblib.parallel.Parallel`` while it is acquired.

    The first ``acquire`` replaces ``__call__`` and ``print_progress``, and
    the ``release`` that matches the last ``acquire`` restores them. The
    lock is held only while counting and replacing, never while joblib runs
    (joblib calls ``print_progress`` while holding its own lock).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._n_acquired = 0
        self._originals: (
            tuple[Callable[..., Any], Callable[..., Any]] | None
        ) = None

    def acquire(self) -> None:
        """Replace the methods unless they are already replaced."""
        with self._lock:
            if self._n_acquired == 0:
                import joblib.parallel

                parallel = joblib.parallel.Parallel
                originals = (parallel.__call__, parallel.print_progress)
                call, print_progress = _make_tracking_methods(*originals)
                setattr(parallel, "__call__", call)
                setattr(parallel, "print_progress", print_progress)
                self._originals = originals
            self._n_acquired += 1

    def release(self) -> None:
        """Restore the methods if no other acquisition remains.

        Raises
        ------
        RuntimeError
            If the methods are not replaced.
        """
        with self._lock:
            if self._originals is None:
                raise RuntimeError(
                    "joblib.parallel.Parallel is not replaced by tqdm_joblib"
                )
            self._n_acquired -= 1
            if self._n_acquired == 0:
                import joblib.parallel

                parallel = joblib.parallel.Parallel
                call, print_progress = self._originals
                setattr(parallel, "__call__", call)
                setattr(parallel, "print_progress", print_progress)
                self._originals = None


_PARALLEL_PATCH = _ParallelPatch()


class tqdm_joblib:
    """Show the progress of ``joblib.Parallel`` with a progress bar.

    Inside the context, ``joblib.Parallel`` calls move the progress bar
    forward by the number of tasks they have finished, whatever ``n_jobs``
    is (including the sequential ``n_jobs=1`` and ``None``). With several
    jobs the bar may move by batches of tasks. The bar is a
    ``tqdm.auto.tqdm``, or a :class:`dummy_tqdm` that shows nothing when
    tqdm is not installed or ``silent`` is True.

    joblib is an optional dependency: this class can be imported without
    it, and entering the context raises ImportError when it is missing.

    A call is counted when it is started on the thread that entered the
    context while no other counted call of the context is running. So the
    work of the outermost ``Parallel`` is counted, and the ``Parallel``
    calls that its tasks start (on the same thread with ``n_jobs=1``, or on
    worker threads) are not. Calls with a ``return_as`` other than
    ``"list"`` (joblib >= 1.3), which return a generator before their tasks
    run, are not counted either; as such a call is not counted, the
    ``Parallel`` calls that its tasks start on the thread of the context
    (with ``n_jobs=1``) are counted.

    Contexts can be nested, and separate threads can use their own contexts
    at the same time. With nested contexts on a thread, the innermost active
    one counts; a context entered inside a task of a counted call counts the
    calls of that task.

    While any context is active, ``joblib.parallel.Parallel.__call__`` and
    ``Parallel.print_progress`` are replaced. They are restored when the
    last active context exits, also when an exception is raised.

    Parameters
    ----------
    total : int
        The expected number of tasks, passed to tqdm.
    silent : bool, default=False
        If True, use :class:`dummy_tqdm` even when tqdm is installed, so
        that no progress bar is shown.
    **tqdm_kwargs
        Other keyword arguments passed to tqdm, such as ``desc``.

    Attributes
    ----------
    total : int
        The expected number of tasks.
    silent : bool
        Whether no progress bar is shown.
    tqdm_kwargs : dict
        The other keyword arguments passed to tqdm.
    tqdm : tqdm, dummy_tqdm or None
        The progress bar made on the latest entering (closed after the
        context exits), or None before the context is entered.

    Examples
    --------
    >>> from joblib import Parallel, delayed
    >>> from python_template.helpers import tqdm_joblib
    >>> with tqdm_joblib(total=3, desc="squares") as progress_bar:
    ...     squares = Parallel(n_jobs=1)(delayed(pow)(i, 2) for i in range(3))
    >>> squares
    [0, 1, 4]

    Use ``silent`` to hide the progress bar:

    >>> with tqdm_joblib(total=3, silent=True):
    ...     squares = Parallel(n_jobs=2)(delayed(pow)(i, 2) for i in range(3))
    >>> squares
    [0, 1, 4]
    """

    def __init__(
        self, total: int, silent: bool = False, **tqdm_kwargs: Any
    ) -> None:
        """Store the arguments; the progress bar is made on entering.

        Parameters
        ----------
        total : int
            The expected number of tasks, passed to tqdm.
        silent : bool, default=False
            If True, use :class:`dummy_tqdm` even when tqdm is installed.
        **tqdm_kwargs
            Other keyword arguments passed to tqdm, such as ``desc``.
        """
        self.total = total
        self.silent = silent
        self.tqdm_kwargs = tqdm_kwargs
        self.tqdm: Any = None
        # The progress and the stack it is on, while the context is active.
        self._active: tuple[_Progress, list[_Progress]] | None = None

    def __enter__(self) -> Any:
        """Make the progress bar and start counting the ``Parallel`` calls.

        Returns
        -------
        tqdm or dummy_tqdm
            The progress bar (:class:`dummy_tqdm` when tqdm is not
            installed or ``silent`` is True).

        Raises
        ------
        RuntimeError
            If the context is already active (use another instance to nest
            contexts or to use them in other threads).
        ImportError
            If joblib is not installed.
        """
        if self._active is not None:
            raise RuntimeError(
                "This tqdm_joblib is already active; use another instance "
                "to nest contexts or to use them in other threads."
            )
        if not is_installed("joblib"):
            raise ImportError(
                "tqdm_joblib requires joblib; install it with "
                "`pip install joblib`.",
                name="joblib",
            )
        progress = _Progress(self._make_progress_bar())
        _PARALLEL_PATCH.acquire()
        stack = _progress_stack()
        stack.append(progress)
        self._active = (progress, stack)
        self.tqdm = progress.progress_bar
        return self.tqdm

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop counting, restore joblib if no context remains, close the bar.

        Exceptions raised in the context are not suppressed.

        Parameters
        ----------
        exc_type : type or None
            The type of the exception raised in the context, if any.
        exc_value : BaseException or None
            The exception raised in the context, if any.
        traceback : traceback or None
            The traceback of the exception, if any.

        Raises
        ------
        RuntimeError
            If the context is not active.
        """
        if self._active is None:
            raise RuntimeError(
                "This tqdm_joblib is not active; exit it only after "
                "entering it."
            )
        progress, stack = self._active
        self._active = None
        stack.remove(progress)
        try:
            _PARALLEL_PATCH.release()
        finally:
            progress.close()

    def _make_progress_bar(self) -> Any:
        """Return a new tqdm progress bar, or a dummy_tqdm."""
        if self.silent or not is_installed("tqdm"):
            return dummy_tqdm(total=self.total, **self.tqdm_kwargs)
        from tqdm.auto import tqdm

        return tqdm(total=self.total, **self.tqdm_kwargs)
