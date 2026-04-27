"""Tests for pipewatch.precheck."""
import subprocess
from unittest.mock import patch

import pytest

from pipewatch.precheck import (
    PrecheckPolicy,
    PrecheckResult,
    _check_binary,
    _run_command,
    run_prechecks,
)


# ---------------------------------------------------------------------------
# PrecheckPolicy
# ---------------------------------------------------------------------------

def test_disabled_by_default():
    p = PrecheckPolicy()
    assert not p.is_enabled()


def test_enabled_with_command():
    p = PrecheckPolicy(commands=["echo hi"])
    assert p.is_enabled()


def test_enabled_with_binary():
    p = PrecheckPolicy(require_binaries=["python"])
    assert p.is_enabled()


def test_describe_disabled():
    assert "disabled" in PrecheckPolicy().describe()


def test_describe_binaries():
    p = PrecheckPolicy(require_binaries=["git", "curl"])
    desc = p.describe()
    assert "git" in desc
    assert "curl" in desc


def test_describe_commands():
    p = PrecheckPolicy(commands=["true", "false"])
    desc = p.describe()
    assert "2 command" in desc


# ---------------------------------------------------------------------------
# PrecheckResult
# ---------------------------------------------------------------------------

def test_result_passed_message():
    r = PrecheckResult(passed=True)
    assert "passed" in r.message


def test_result_failed_message():
    r = PrecheckResult(passed=False, failures=["binary not found: foo"])
    assert "failed" in r.message
    assert "foo" in r.message


# ---------------------------------------------------------------------------
# _check_binary
# ---------------------------------------------------------------------------

def test_check_binary_found():
    # 'python' or 'python3' must exist in a test environment
    import sys
    import os
    binary = os.path.basename(sys.executable)
    assert _check_binary(binary) is None


def test_check_binary_missing():
    err = _check_binary("__no_such_binary_xyz__")
    assert err is not None
    assert "not found" in err


# ---------------------------------------------------------------------------
# _run_command
# ---------------------------------------------------------------------------

def test_run_command_success():
    assert _run_command("exit 0", timeout=5) is None


def test_run_command_failure():
    err = _run_command("exit 1", timeout=5)
    assert err is not None
    assert "exited 1" in err


def test_run_command_timeout():
    err = _run_command("sleep 60", timeout=1)
    assert err is not None
    assert "timed out" in err


# ---------------------------------------------------------------------------
# run_prechecks
# ---------------------------------------------------------------------------

def test_run_prechecks_disabled_passes():
    result = run_prechecks(PrecheckPolicy())
    assert result.passed
    assert result.failures == []


def test_run_prechecks_all_pass():
    p = PrecheckPolicy(commands=["exit 0"], require_binaries=["python"])
    # python is always available in tests
    import shutil
    if shutil.which("python") is None:
        pytest.skip("python binary not on PATH")
    result = run_prechecks(p)
    assert result.passed


def test_run_prechecks_missing_binary_fails():
    p = PrecheckPolicy(require_binaries=["__no_such_binary_xyz__"])
    result = run_prechecks(p)
    assert not result.passed
    assert len(result.failures) == 1


def test_run_prechecks_failing_command_fails():
    p = PrecheckPolicy(commands=["exit 42"])
    result = run_prechecks(p)
    assert not result.passed
    assert "42" in result.failures[0]


def test_run_prechecks_multiple_failures_collected():
    p = PrecheckPolicy(
        commands=["exit 1"],
        require_binaries=["__no_such_binary_xyz__"],
    )
    result = run_prechecks(p)
    assert not result.passed
    assert len(result.failures) == 2
