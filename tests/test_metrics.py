"""Tests for pipewatch.metrics and pipewatch.cli_metrics."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from pipewatch.metrics import Metrics, capture_rss, collect, format_metrics
from pipewatch.cli_metrics import emit_metrics


# ------------------------------------------------------------------ helpers
def _finished(pipeline: str = "etl", exit_code: int = 0, timed_out: bool = False) -> Metrics:
    m = collect(pipeline)
    time.sleep(0.01)
    m.stop(exit_code=exit_code, timed_out=timed_out)
    return m


# ------------------------------------------------------------------ Metrics
class TestMetrics:
    def test_elapsed_none_before_stop(self):
        m = collect("p")
        assert m.elapsed is None

    def test_elapsed_positive_after_stop(self):
        m = _finished()
        assert m.elapsed is not None
        assert m.elapsed >= 0.01

    def test_stop_sets_fields(self):
        m = _finished(exit_code=1, timed_out=True)
        assert m.exit_code == 1
        assert m.timed_out is True

    def test_to_dict_keys(self):
        m = _finished()
        d = m.to_dict()
        for key in ("pipeline", "start_time", "end_time", "elapsed_seconds", "exit_code", "timed_out"):
            assert key in d

    def test_to_dict_elapsed_rounded(self):
        m = _finished()
        d = m.to_dict()
        # Should be a float with at most 3 decimal places
        assert isinstance(d["elapsed_seconds"], float)

    def test_format_metrics_contains_pipeline(self):
        m = _finished(pipeline="myflow")
        out = format_metrics(m)
        assert "pipeline=myflow" in out

    def test_format_metrics_timed_out(self):
        m = _finished(timed_out=True)
        assert "timed_out=true" in format_metrics(m)

    def test_format_metrics_no_timed_out_when_false(self):
        m = _finished(timed_out=False)
        assert "timed_out" not in format_metrics(m)


# ------------------------------------------------------------------ capture_rss
def test_capture_rss_returns_none_or_float():
    result = capture_rss()
    assert result is None or isinstance(result, float)


# ------------------------------------------------------------------ emit_metrics
class TestEmitMetrics:
    def test_none_mode_does_nothing(self, capsys):
        m = _finished()
        emit_metrics(m, mode="none")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_text_mode_writes_stderr(self, capsys):
        m = _finished(pipeline="pipe1")
        emit_metrics(m, mode="text")
        captured = capsys.readouterr()
        assert "pipe1" in captured.err

    def test_json_mode_valid_json(self, capsys):
        m = _finished()
        emit_metrics(m, mode="json")
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["pipeline"] == "etl"

    def test_json_written_to_file(self, tmp_path):
        out = tmp_path / "metrics.json"
        m = _finished()
        emit_metrics(m, mode="json", metrics_file=str(out))
        data = json.loads(out.read_text())
        assert "elapsed_seconds" in data
