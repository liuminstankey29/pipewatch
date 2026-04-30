"""Tests for pipewatch.cli_triage."""
import argparse
from io import StringIO
from unittest.mock import patch

import pytest

from pipewatch.cli_triage import (
    add_triage_args,
    evaluate_and_print,
    resolve_triage,
    triage_from_args,
    triage_from_config,
)
from pipewatch.triage import CATEGORY_TIMEOUT, CATEGORY_UNKNOWN


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(*argv: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_triage_args(p)
    return p.parse_args(list(argv))


# ---------------------------------------------------------------------------
# add_triage_args / triage_from_args
# ---------------------------------------------------------------------------

def test_defaults():
    args = _parse()
    assert triage_from_args(args) is False


def test_triage_flag_enables():
    args = _parse("--triage")
    assert triage_from_args(args) is True


# ---------------------------------------------------------------------------
# triage_from_config
# ---------------------------------------------------------------------------

def test_config_dict_disabled():
    assert triage_from_config({}) is False


def test_config_dict_enabled():
    assert triage_from_config({"triage": True}) is True


def test_config_object_enabled():
    class Cfg:
        triage = True
    assert triage_from_config(Cfg()) is True


# ---------------------------------------------------------------------------
# resolve_triage
# ---------------------------------------------------------------------------

def test_resolve_cli_wins_over_config():
    args = _parse("--triage")
    assert resolve_triage(args, {"triage": False}) is True


def test_resolve_falls_back_to_config():
    args = _parse()
    assert resolve_triage(args, {"triage": True}) is True


def test_resolve_both_false():
    args = _parse()
    assert resolve_triage(args, {}) is False


# ---------------------------------------------------------------------------
# evaluate_and_print
# ---------------------------------------------------------------------------

def test_evaluate_and_print_timeout(capsys):
    result = evaluate_and_print(exit_code=-1, timed_out=True)
    captured = capsys.readouterr()
    assert result.category == CATEGORY_TIMEOUT
    assert "timeout" in captured.out


def test_evaluate_and_print_unknown(capsys):
    result = evaluate_and_print(exit_code=99, timed_out=False)
    captured = capsys.readouterr()
    assert result.category == CATEGORY_UNKNOWN
    assert "unknown" in captured.out
    assert "note:" in captured.out


def test_evaluate_and_print_signals_shown(capsys):
    evaluate_and_print(exit_code=1, timed_out=False, stderr="connection refused")
    captured = capsys.readouterr()
    assert "signals:" in captured.out
