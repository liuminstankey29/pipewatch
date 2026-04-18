"""Tests for pipewatch.hooks and pipewatch.cli_hooks."""
from __future__ import annotations

import argparse
import sys
import pytest

from pipewatch.hooks import (
    HookConfig,
    HookResult,
    run_hook,
    run_hooks,
    hooks_from_config,
)
from pipewatch.cli_hooks import add_hook_args, hooks_from_args, resolve_hooks


# ---------------------------------------------------------------------------
# run_hook
# ---------------------------------------------------------------------------

def test_run_hook_success():
    result = run_hook(f"{sys.executable} -c 'print(1)'")
    assert result.succeeded
    assert result.returncode == 0
    assert result.stdout == "1"


def test_run_hook_failure():
    result = run_hook(f"{sys.executable} -c 'raise SystemExit(2)'")
    assert not result.succeeded
    assert result.returncode == 2


def test_run_hook_timeout():
    result = run_hook(f"{sys.executable} -c 'import time; time.sleep(10)'», timeout=1)
    # fallback: use short timeout via direct call
    result = run_hook(f"{sys.executable} -c 'import time; time.sleep(10)'")


def test_run_hook_timeout_returns_minus1(monkeypatch):
    import subprocess
    def _raise(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)
    monkeypatch.setattr(subprocess, "run", _raise)
    result = run_hook("anything", timeout=1)
    assert result.returncode == -1
    assert result.stderr == "timeout"
    assert not result.succeeded


# ---------------------------------------------------------------------------
# run_hooks
# ---------------------------------------------------------------------------

def test_run_hooks_all_succeed():
    results = run_hooks([f"{sys.executable} -c 'pass'", f"{sys.executable} -c 'pass'"])
    assert all(r.succeeded for r in results)
    assert len(results) == 2


def test_run_hooks_continues_after_failure():
    results = run_hooks([
        f"{sys.executable} -c 'raise SystemExit(1)'",
        f"{sys.executable} -c 'pass'",
    ])
    assert not results[0].succeeded
    assert results[1].succeeded


# ---------------------------------------------------------------------------
# hooks_from_config
# ---------------------------------------------------------------------------

def test_hooks_from_config_defaults():
    hc = hooks_from_config({})
    assert hc.pre == []
    assert hc.post == []
    assert hc.on_failure == []
    assert hc.timeout == 30


def test_hooks_from_config_values():
    hc = hooks_from_config({"hooks": {"pre": ["echo start"], "timeout": 10}})
    assert hc.pre == ["echo start"]
    assert hc.timeout == 10


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*argv):
    p = argparse.ArgumentParser()
    add_hook_args(p)
    return p.parse_args(list(argv))


def test_hooks_from_args_defaults():
    args = _parse()
    hc = hooks_from_args(args)
    assert hc.pre == []
    assert hc.timeout == 30


def test_hooks_from_args_values():
    args = _parse("--pre-hook", "echo hi", "--hook-timeout", "5")
    hc = hooks_from_args(args)
    assert hc.pre == ["echo hi"]
    assert hc.timeout == 5


def test_resolve_hooks_cli_overrides_config():
    args = _parse("--pre-hook", "echo cli")
    hc = resolve_hooks(args, {"hooks": {"pre": ["echo cfg"], "timeout": 20}})
    assert hc.pre == ["echo cli"]
    assert hc.timeout == 20


def test_resolve_hooks_falls_back_to_config():
    args = _parse()
    hc = resolve_hooks(args, {"hooks": {"post": ["echo done"]}})
    assert hc.post == ["echo done"]
