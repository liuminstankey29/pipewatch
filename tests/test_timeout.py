"""Tests for pipewatch.timeout."""
from __future__ import annotations

import time
import types

import pytest

from pipewatch.timeout import (
    TimeoutExpired,
    TimeoutPolicy,
    policy_from_config,
    timeout_context,
)


# ---------------------------------------------------------------------------
# TimeoutPolicy
# ---------------------------------------------------------------------------

class TestTimeoutPolicy:
    def test_disabled_when_none(self):
        p = TimeoutPolicy(seconds=None)
        assert not p.is_enabled()

    def test_disabled_when_zero(self):
        p = TimeoutPolicy(seconds=0)
        assert not p.is_enabled()

    def test_enabled_when_positive(self):
        p = TimeoutPolicy(seconds=30)
        assert p.is_enabled()

    def test_describe_no_timeout(self):
        assert TimeoutPolicy().describe() == "no timeout"

    def test_describe_with_seconds(self):
        assert TimeoutPolicy(seconds=60).describe() == "60s timeout"

    def test_negative_seconds_treated_as_disabled(self):
        """Negative values should be treated the same as None/zero (disabled)."""
        p = TimeoutPolicy(seconds=-1)
        assert not p.is_enabled()


# ---------------------------------------------------------------------------
# policy_from_config
# ---------------------------------------------------------------------------

def test_policy_from_config_reads_timeout():
    cfg = types.SimpleNamespace(timeout=45)
    p = policy_from_config(cfg)
    assert p.seconds == 45


def test_policy_from_config_missing_attr():
    cfg = types.SimpleNamespace()
    p = policy_from_config(cfg)
    assert p.seconds is None
    assert not p.is_enabled()


# ---------------------------------------------------------------------------
# timeout_context
# ---------------------------------------------------------------------------

def test_timeout_context_no_op_when_disabled():
    policy = TimeoutPolicy(seconds=None)
    with timeout_context(policy):
        time.sleep(0.01)  # should complete without error


def test_timeout_context_completes_within_limit():
    policy = TimeoutPolicy(seconds=5)
    with timeout_context(policy):
        pass  # instant — should not raise


def test_timeout_context_raises_on_expire():
    policy = TimeoutPolicy(seconds=1)
    with pytest.raises(TimeoutExpired) as exc_info:
        with timeout_context(policy):
            time.sleep(5)
    assert exc_info.value.seconds == 1
    assert "1s" in str(exc_info.value)


def test_timeout_expired_message():
    err = TimeoutExpired(10)
    assert "10" in str(err)


def test_timeout_context_restores_after_completion():
    """Ensure the timeout context cleans up properly after a successful block.

    A second context with a short limit should still fire correctly,
    proving the first context did not leave any stale alarm signal behind.
    """
    policy_ok = TimeoutPolicy(seconds=5)
    with timeout_context(policy_ok):
        pass  # completes instantly

    policy_short = TimeoutPolicy(seconds=1)
    with pytest.raises(TimeoutExpired):
        with timeout_context(policy_short):
            time.sleep(5)
