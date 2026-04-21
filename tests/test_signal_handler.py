"""Tests for pipewatch.signal_handler."""

from __future__ import annotations

import signal
import threading
from unittest.mock import patch

import pytest

from pipewatch.signal_handler import ShutdownEvent, SignalHandler, make_handler


# ---------------------------------------------------------------------------
# ShutdownEvent
# ---------------------------------------------------------------------------


class TestShutdownEvent:
    def test_not_set_initially(self):
        ev = ShutdownEvent()
        assert not ev.is_set()
        assert ev.signal_received is None

    def test_request_sets_event(self):
        ev = ShutdownEvent()
        ev.request(signal.SIGTERM)
        assert ev.is_set()
        assert ev.signal_received == signal.SIGTERM

    def test_clear_resets_state(self):
        ev = ShutdownEvent()
        ev.request(signal.SIGINT)
        ev.clear()
        assert not ev.is_set()
        assert ev.signal_received is None

    def test_wait_returns_true_when_set(self):
        ev = ShutdownEvent()
        ev.request(signal.SIGTERM)
        assert ev.wait(timeout=0.0) is True

    def test_wait_returns_false_when_not_set(self):
        ev = ShutdownEvent()
        assert ev.wait(timeout=0.01) is False


# ---------------------------------------------------------------------------
# SignalHandler
# ---------------------------------------------------------------------------


class TestSignalHandler:
    def test_register_and_restore(self):
        handler = SignalHandler(signals=[signal.SIGUSR1])
        original = signal.getsignal(signal.SIGUSR1)
        handler.register()
        assert signal.getsignal(signal.SIGUSR1) is not original
        handler.restore()
        assert signal.getsignal(signal.SIGUSR1) == original

    def test_context_manager_restores_on_exit(self):
        original = signal.getsignal(signal.SIGUSR1)
        with SignalHandler(signals=[signal.SIGUSR1]):
            pass
        assert signal.getsignal(signal.SIGUSR1) == original

    def test_handle_sets_shutdown(self):
        handler = SignalHandler(signals=[signal.SIGUSR1])
        handler._handle(signal.SIGUSR1, None)
        assert handler.shutdown.is_set()
        assert handler.shutdown.signal_received == signal.SIGUSR1

    def test_signal_triggers_shutdown(self):
        with SignalHandler(signals=[signal.SIGUSR1]) as handler:
            signal.raise_signal(signal.SIGUSR1)
            assert handler.shutdown.is_set()


# ---------------------------------------------------------------------------
# make_handler
# ---------------------------------------------------------------------------


def test_make_handler_default_signals():
    handler = make_handler()
    assert signal.SIGINT in handler.signals
    assert signal.SIGTERM in handler.signals


def test_make_handler_callback_invoked():
    received: list[int] = []

    handler = make_handler(
        signals=[signal.SIGUSR1],
        on_shutdown=lambda sig: received.append(sig),
    )
    with handler:
        signal.raise_signal(signal.SIGUSR1)

    assert received == [signal.SIGUSR1]
    assert handler.shutdown.is_set()
