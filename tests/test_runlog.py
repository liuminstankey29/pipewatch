"""Tests for pipewatch.runlog."""
import json
from pathlib import Path

import pytest

from pipewatch.runlog import (
    RunLog,
    list_logs,
    load_log,
    log_path,
    save_log,
)


def _entry(**kw) -> RunLog:
    defaults = dict(
        pipeline="etl",
        started_at="2024-01-01T10:00:00",
        finished_at="2024-01-01T10:01:00",
        exit_code=0,
        timed_out=False,
        duration=60.0,
        tags=["prod"],
        notes="",
    )
    defaults.update(kw)
    return RunLog(**defaults)


def test_succeeded_zero_exit():
    assert _entry(exit_code=0, timed_out=False).succeeded() is True


def test_failed_nonzero_exit():
    assert _entry(exit_code=1).succeeded() is False


def test_failed_timed_out():
    assert _entry(timed_out=True).succeeded() is False


def test_to_dict_roundtrip():
    e = _entry()
    assert RunLog.from_dict(e.to_dict()) == e


def test_save_and_load(tmp_path):
    e = _entry()
    p = save_log(e, log_dir=str(tmp_path))
    assert p.exists()
    loaded = load_log(str(p))
    assert loaded == e


def test_save_creates_dir(tmp_path):
    d = tmp_path / "nested" / "logs"
    e = _entry()
    save_log(e, log_dir=str(d))
    assert d.exists()


def test_list_logs_empty(tmp_path):
    assert list_logs(log_dir=str(tmp_path)) == []


def test_list_logs_returns_entries(tmp_path):
    save_log(_entry(pipeline="a"), log_dir=str(tmp_path))
    save_log(_entry(pipeline="b", started_at="2024-01-01T11:00:00"), log_dir=str(tmp_path))
    logs = list_logs(log_dir=str(tmp_path))
    assert len(logs) == 2


def test_list_logs_filter_pipeline(tmp_path):
    save_log(_entry(pipeline="a"), log_dir=str(tmp_path))
    save_log(_entry(pipeline="b", started_at="2024-01-01T11:00:00"), log_dir=str(tmp_path))
    logs = list_logs(log_dir=str(tmp_path), pipeline="a")
    assert all(e.pipeline == "a" for e in logs)
    assert len(logs) == 1


def test_list_logs_missing_dir(tmp_path):
    assert list_logs(log_dir=str(tmp_path / "nope")) == []


def test_log_path_safe_chars():
    p = log_path("/tmp", "my pipeline", "2024-01-01T10:00:00")
    assert " " not in p.name
    assert "/" not in p.name
