"""Tests for pipewatch.pinning and pipewatch.cli_pinning."""
from __future__ import annotations

import argparse
import json

import pytest

from pipewatch.pinning import (
    PinningPolicy,
    PinningResult,
    check_pin,
    load_pin,
    save_pin,
)
from pipewatch.cli_pinning import (
    add_pinning_args,
    policy_from_args,
    policy_from_config,
    resolve_pinning,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path)


def _policy(strict=False) -> PinningPolicy:
    return PinningPolicy(enabled=True, pin_file=".pin", strict=strict)


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_pinning_args(p)
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# PinningPolicy
# ---------------------------------------------------------------------------

def test_disabled_by_default():
    pol = PinningPolicy()
    assert not pol.is_enabled()


def test_enabled_when_flag_set():
    pol = PinningPolicy(enabled=True)
    assert pol.is_enabled()


def test_describe_disabled():
    assert "disabled" in PinningPolicy().describe()


def test_describe_warn():
    desc = PinningPolicy(enabled=True, strict=False).describe()
    assert "warn" in desc


def test_describe_strict():
    desc = PinningPolicy(enabled=True, strict=True).describe()
    assert "strict" in desc


# ---------------------------------------------------------------------------
# save_pin / load_pin
# ---------------------------------------------------------------------------

def test_save_and_load(sdir):
    save_pin("abc123", ".pin", sdir)
    assert load_pin(".pin", sdir) == "abc123"


def test_load_missing_returns_none(sdir):
    assert load_pin(".pin", sdir) is None


# ---------------------------------------------------------------------------
# check_pin
# ---------------------------------------------------------------------------

def test_first_call_creates_pin(sdir):
    pol = _policy()
    result = check_pin(pol, "deadbeef", sdir)
    assert result.created is True
    assert result.mismatch is False
    assert load_pin(pol.pin_file, sdir) == "deadbeef"


def test_matching_hash_no_mismatch(sdir):
    pol = _policy()
    save_pin("deadbeef", pol.pin_file, sdir)
    result = check_pin(pol, "deadbeef", sdir)
    assert result.mismatch is False
    assert result.created is False


def test_different_hash_is_mismatch(sdir):
    pol = _policy()
    save_pin("aaaa", pol.pin_file, sdir)
    result = check_pin(pol, "bbbb", sdir)
    assert result.mismatch is True


def test_mismatch_message_contains_hashes(sdir):
    pol = _policy()
    save_pin("a" * 40, pol.pin_file, sdir)
    result = check_pin(pol, "b" * 40, sdir)
    msg = result.message()
    assert "pinned=" in msg and "current=" in msg


def test_created_message(sdir):
    pol = _policy()
    result = check_pin(pol, "c" * 40, sdir)
    assert "pinned" in result.message()


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def test_defaults():
    ns = _parse([])
    assert ns.pin is False
    assert ns.pin_file == ".pipewatch_pin"
    assert ns.pin_strict is False


def test_pin_flag():
    ns = _parse(["--pin"])
    assert ns.pin is True


def test_pin_strict_flag():
    ns = _parse(["--pin", "--pin-strict"])
    pol = policy_from_args(ns)
    assert pol.strict is True


def test_policy_from_config_defaults():
    pol = policy_from_config({})
    assert not pol.is_enabled()


def test_policy_from_config_custom():
    pol = policy_from_config({"pinning": {"enabled": True, "strict": True, "pin_file": "my.pin"}})
    assert pol.is_enabled()
    assert pol.strict is True
    assert pol.pin_file == "my.pin"


def test_resolve_pinning_cli_wins():
    ns = _parse(["--pin", "--pin-strict"])
    pol = resolve_pinning(ns, {"pinning": {"enabled": False}})
    assert pol.is_enabled()
    assert pol.strict is True


def test_resolve_pinning_falls_back_to_config():
    ns = _parse([])
    pol = resolve_pinning(ns, {"pinning": {"enabled": True, "strict": False}})
    assert pol.is_enabled()
