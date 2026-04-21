"""Graceful shutdown via OS signals for long-running pipeline jobs."""

from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional

log = logging.getLogger(__name__)


@dataclass
class ShutdownEvent:
    """Shared state that tracks whether a shutdown has been requested."""

    _event: threading.Event = field(default_factory=threading.Event, init=False)
    signal_received: Optional[int] = field(default=None, init=False)

    def request(self, signum: int) -> None:
        self.signal_received = signum
        self._event.set()
        log.warning("Shutdown requested via signal %s", signal.Signals(signum).name)

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._event.wait(timeout=timeout)

    def clear(self) -> None:
        self._event.clear()
        self.signal_received = None


@dataclass
class SignalHandler:
    """Registers OS signal handlers and exposes a shared ShutdownEvent."""

    signals: List[int] = field(
        default_factory=lambda: [signal.SIGINT, signal.SIGTERM]
    )
    _shutdown: ShutdownEvent = field(default_factory=ShutdownEvent, init=False)
    _previous: dict = field(default_factory=dict, init=False)

    @property
    def shutdown(self) -> ShutdownEvent:
        return self._shutdown

    def register(self) -> None:
        """Install signal handlers, saving previous handlers for restore."""
        for sig in self.signals:
            prev = signal.signal(sig, self._handle)
            self._previous[sig] = prev
            log.debug("Registered handler for %s", signal.Signals(sig).name)

    def restore(self) -> None:
        """Restore previously installed signal handlers."""
        for sig, prev in self._previous.items():
            signal.signal(sig, prev)
        self._previous.clear()

    def _handle(self, signum: int, _frame) -> None:  # noqa: ANN001
        self._shutdown.request(signum)

    def __enter__(self) -> "SignalHandler":
        self.register()
        return self

    def __exit__(self, *_) -> None:
        self.restore()


def make_handler(
    *,
    signals: Optional[List[int]] = None,
    on_shutdown: Optional[Callable[[int], None]] = None,
) -> SignalHandler:
    """Convenience factory; optionally attach a callback invoked on shutdown."""
    sigs = signals or [signal.SIGINT, signal.SIGTERM]
    handler = SignalHandler(signals=sigs)
    if on_shutdown is not None:
        original_handle = handler._handle

        def _wrapped(signum: int, frame) -> None:  # noqa: ANN001
            original_handle(signum, frame)
            on_shutdown(signum)

        handler._handle = _wrapped  # type: ignore[method-assign]
    return handler
