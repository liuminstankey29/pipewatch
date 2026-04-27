"""Tests for pipewatch.maturity and pipewatch.cli_maturity."""
from __future__ import annotations

import argparse
import pytest
from unittest.mock import MagicMock

from pipewatch.maturity import (
    MaturityResult,
    _grade,
    _percentile,
    score_pipeline,
)
from pipewatch.cli_maturity import (
    add_maturity_args,
    evaluate_and_print,
    resolve_maturity,
    window_from_args,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(pipeline: str = "etl", exit_code: int = 0, elapsed: float = 10.0):
    e = MagicMock()
    e.pipeline = pipeline
    e.exit_code = exit_code
    e.elapsed = elapsed
    e.succeeded = lambda: exit_code == 0
    return e


def _history(entries):
    h = MagicMock()
    h.last_for = lambda pipeline, n=30: [e for e in entries if e.pipeline == pipeline][:n]
    return h


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (95, "A"), (90, "A"), (80, "B"), (75, "B"),
    (65, "C"), (60, "C"), (50, "D"), (40, "D"),
    (39, "F"), (0, "F"),
])
def test_grade(score, expected):
    assert _grade(score) == expected


# ---------------------------------------------------------------------------
# _percentile
# ---------------------------------------------------------------------------

def test_percentile_empty_returns_none():
    assert _percentile([], 50) is None


def test_percentile_single():
    assert _percentile([7.0], 50) == 7.0


def test_percentile_p50():
    assert _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == 3.0


def test_percentile_p95():
    values = list(range(1, 21))  # 1..20
    result = _percentile([float(v) for v in values], 95)
    assert result == 19.0


# ---------------------------------------------------------------------------
# score_pipeline
# ---------------------------------------------------------------------------

def test_score_no_history():
    h = _history([])
    r = score_pipeline(h, "etl", window=10)
    assert r.score == 0.0
    assert r.grade == "F"
    assert r.sample_size == 0
    assert r.success_rate == 0.0
    assert r.p50_elapsed is None


def test_score_all_success_full_window():
    entries = [_entry("etl", exit_code=0, elapsed=5.0) for _ in range(30)]
    h = _history(entries)
    r = score_pipeline(h, "etl", window=30)
    assert r.score == 100.0
    assert r.grade == "A"
    assert r.success_rate == 1.0
    assert r.sample_size == 30


def test_score_all_failures():
    entries = [_entry("etl", exit_code=1, elapsed=2.0) for _ in range(30)]
    h = _history(entries)
    r = score_pipeline(h, "etl", window=30)
    # success_rate=0, confidence=1 → score=30
    assert r.score == 30.0
    assert r.grade == "D"


def test_score_partial_window_reduces_confidence():
    entries = [_entry("etl", exit_code=0, elapsed=5.0) for _ in range(15)]
    h = _history(entries)
    r = score_pipeline(h, "etl", window=30)
    # success_rate=1, confidence=0.5 → 70 + 15 = 85
    assert r.score == 85.0
    assert r.grade == "B"


def test_score_message_contains_grade():
    entries = [_entry("etl", exit_code=0) for _ in range(30)]
    h = _history(entries)
    r = score_pipeline(h, "etl", window=30)
    assert "A" in r.message
    assert "100.0" in r.message


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*argv):
    p = argparse.ArgumentParser()
    add_maturity_args(p)
    return p.parse_args(list(argv))


def test_defaults():
    args = _parse()
    assert args.maturity is False
    assert args.maturity_window == 30


def test_maturity_flag():
    args = _parse("--maturity")
    assert args.maturity is True


def test_window_flag():
    args = _parse("--maturity-window", "10")
    assert args.maturity_window == 10


def test_window_from_args_default():
    args = _parse()
    assert window_from_args(args) == 30


def test_resolve_maturity_prefers_cli():
    args = _parse("--maturity-window", "5")
    cfg = MagicMock()
    cfg.get = lambda k, d=None: 20
    assert resolve_maturity(args, cfg) == 5


def test_evaluate_and_print_outputs_message(capsys):
    entries = [_entry("etl", exit_code=0, elapsed=3.0) for _ in range(30)]
    h = _history(entries)
    result = evaluate_and_print("etl", h, window=30)
    captured = capsys.readouterr()
    assert result.grade == "A"
    assert result.message in captured.out
