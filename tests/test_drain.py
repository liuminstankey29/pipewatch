"""Tests for pipewatch.drain and pipewatch.cli_drain."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from pipewatch.drain import DrainPolicy, DrainResult, save_drain, _write_stream
from pipewatch.cli_drain import (
    add_drain_args,
    policy_from_args,
    policy_from_config,
    resolve_drain,
)


# ---------------------------------------------------------------------------
# DrainPolicy
# ---------------------------------------------------------------------------

def test_disabled_by_default():
    p = DrainPolicy()
    assert not p.is_enabled()


def test_enabled_flag():
    p = DrainPolicy(enabled=True)
    assert p.is_enabled()


def test_describe_disabled():
    assert DrainPolicy().describe() == "drain disabled"


def test_describe_enabled():
    p = DrainPolicy(enabled=True, log_dir="/tmp/drain", max_bytes=32768)
    desc = p.describe()
    assert "stdout" in desc
    assert "stderr" in desc
    assert "32 KB" in desc


def test_describe_stdout_only():
    p = DrainPolicy(enabled=True, capture_stderr=False)
    assert "stdout" in p.describe()
    assert "stderr" not in p.describe()


# ---------------------------------------------------------------------------
# _write_stream
# ---------------------------------------------------------------------------

def test_write_stream_no_truncation(tmp_path):
    dest = tmp_path / "out.log"
    data = b"hello world"
    n, trunc = _write_stream(data, dest, max_bytes=1024)
    assert n == len(data)
    assert not trunc
    assert dest.read_bytes() == data


def test_write_stream_truncates_to_tail(tmp_path):
    dest = tmp_path / "out.log"
    data = b"A" * 10 + b"B" * 10
    n, trunc = _write_stream(data, dest, max_bytes=10)
    assert trunc
    assert dest.read_bytes() == b"B" * 10


# ---------------------------------------------------------------------------
# save_drain
# ---------------------------------------------------------------------------

def test_save_drain_disabled_returns_none(tmp_path):
    policy = DrainPolicy(enabled=False)
    result = save_drain(policy, "mypipe", "run1", stdout=b"out", stderr=b"err")
    assert result is None


def test_save_drain_creates_files(tmp_path):
    policy = DrainPolicy(enabled=True, log_dir=str(tmp_path / "drain"))
    result = save_drain(policy, "mypipe", "abc123", stdout=b"hello", stderr=b"world")
    assert result is not None
    assert result.stdout_path and Path(result.stdout_path).exists()
    assert result.stderr_path and Path(result.stderr_path).exists()
    assert result.bytes_written == 10


def test_save_drain_skips_stdout_when_disabled(tmp_path):
    policy = DrainPolicy(enabled=True, log_dir=str(tmp_path), capture_stdout=False)
    result = save_drain(policy, "p", "r", stdout=b"ignored", stderr=b"kept")
    assert result.stdout_path is None
    assert result.stderr_path is not None


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*argv):
    parser = argparse.ArgumentParser()
    add_drain_args(parser)
    return parser.parse_args(list(argv))


def test_defaults():
    args = _parse()
    policy = policy_from_args(args)
    assert not policy.is_enabled()


def test_drain_flag_enables():
    args = _parse("--drain")
    policy = policy_from_args(args)
    assert policy.is_enabled()


def test_drain_max_kb():
    args = _parse("--drain", "--drain-max-kb", "128")
    policy = policy_from_args(args)
    assert policy.max_bytes == 128 * 1024


def test_policy_from_config():
    cfg = {"drain": {"enabled": True, "max_kb": 32, "log_dir": "/tmp/x"}}
    policy = policy_from_config(cfg)
    assert policy.is_enabled()
    assert policy.max_bytes == 32 * 1024
    assert policy.log_dir == "/tmp/x"


def test_policy_from_config_empty():
    policy = policy_from_config({})
    assert not policy.is_enabled()


def test_resolve_drain_prefers_cli(tmp_path):
    args = _parse("--drain", "--drain-dir", str(tmp_path))
    cfg = {"drain": {"enabled": False}}
    policy = resolve_drain(args, cfg)
    assert policy.is_enabled()
