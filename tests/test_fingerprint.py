"""Tests for pipewatch.fingerprint."""
import pytest
from pipewatch.fingerprint import (
    Fingerprint,
    compute,
    changed,
    describe_change,
)


# ---------------------------------------------------------------------------
# compute
# ---------------------------------------------------------------------------

def test_compute_returns_fingerprint():
    fp = compute(command="python etl.py")
    assert isinstance(fp, Fingerprint)
    assert len(fp.value) == 64  # SHA-256 hex


def test_compute_deterministic():
    fp1 = compute(command="python etl.py", pipeline="daily", tags=["prod"])
    fp2 = compute(command="python etl.py", pipeline="daily", tags=["prod"])
    assert fp1.matches(fp2)


def test_compute_tags_order_independent():
    fp1 = compute(command="run.sh", tags=["a", "b"])
    fp2 = compute(command="run.sh", tags=["b", "a"])
    assert fp1.matches(fp2)


def test_compute_env_keys_order_independent():
    fp1 = compute(command="run.sh", env_keys=["FOO", "BAR"])
    fp2 = compute(command="run.sh", env_keys=["BAR", "FOO"])
    assert fp1.matches(fp2)


def test_compute_different_commands_differ():
    fp1 = compute(command="python a.py")
    fp2 = compute(command="python b.py")
    assert not fp1.matches(fp2)


def test_compute_different_pipelines_differ():
    fp1 = compute(command="run.sh", pipeline="daily")
    fp2 = compute(command="run.sh", pipeline="hourly")
    assert not fp1.matches(fp2)


# ---------------------------------------------------------------------------
# short
# ---------------------------------------------------------------------------

def test_short_default_length():
    fp = compute(command="x")
    assert len(fp.short()) == 8


def test_short_custom_length():
    fp = compute(command="x")
    assert len(fp.short(12)) == 12


# ---------------------------------------------------------------------------
# to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

def test_roundtrip():
    fp = compute(command="etl.py", pipeline="nightly", tags=["prod"], env_keys=["DB_URL"])
    restored = Fingerprint.from_dict(fp.to_dict())
    assert restored.matches(fp)
    assert restored.components == fp.components


# ---------------------------------------------------------------------------
# changed
# ---------------------------------------------------------------------------

def test_changed_none_previous_returns_false():
    fp = compute(command="run.sh")
    assert changed(None, fp) is False


def test_changed_same_returns_false():
    fp = compute(command="run.sh")
    assert changed(fp, fp) is False


def test_changed_different_returns_true():
    fp1 = compute(command="run.sh")
    fp2 = compute(command="run2.sh")
    assert changed(fp1, fp2) is True


# ---------------------------------------------------------------------------
# describe_change
# ---------------------------------------------------------------------------

def test_describe_change_no_diff():
    fp = compute(command="run.sh")
    result = describe_change(fp, fp)
    assert "no differences" in result


def test_describe_change_shows_command_diff():
    fp1 = compute(command="old.sh")
    fp2 = compute(command="new.sh")
    result = describe_change(fp1, fp2)
    assert "command" in result
    assert "old.sh" in result
    assert "new.sh" in result
