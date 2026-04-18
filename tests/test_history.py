"""Tests for pipewatch.history."""

import json
import pytest
from pathlib import Path
from pipewatch.history import HistoryEntry, RunHistory


@pytest.fixture
def tmp_history(tmp_path) -> RunHistory:
    return RunHistory(path=tmp_path / "history.json")


def _entry(pipeline="myjob", exit_code=0, timed_out=False, duration=1.5):
    return HistoryEntry(
        pipeline=pipeline,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=duration,
        timestamp="2024-01-01T00:00:00",
        stdout_tail="done",
        stderr_tail="",
    )


def test_record_and_last(tmp_history):
    tmp_history.record(_entry())
    tmp_history.record(_entry(pipeline="other"))
    assert len(tmp_history.last()) == 2


def test_last_for_filters(tmp_history):
    tmp_history.record(_entry(pipeline="a"))
    tmp_history.record(_entry(pipeline="b"))
    tmp_history.record(_entry(pipeline="a"))
    results = tmp_history.last_for("a")
    assert len(results) == 2
    assert all(e.pipeline == "a" for e in results)


def test_persists_to_disk(tmp_path):
    p = tmp_path / "h.json"
    h1 = RunHistory(path=p)
    h1.record(_entry())
    h2 = RunHistory(path=p)
    assert len(h2.last()) == 1
    assert h2.last()[0].pipeline == "myjob"


def test_succeeded_property():
    assert _entry(exit_code=0, timed_out=False).succeeded is True
    assert _entry(exit_code=1).succeeded is False
    assert _entry(exit_code=0, timed_out=True).succeeded is False


def test_clear(tmp_history):
    tmp_history.record(_entry())
    tmp_history.clear()
    assert tmp_history.last() == []


def test_last_n_limit(tmp_history):
    for i in range(15):
        tmp_history.record(_entry(duration=float(i)))
    assert len(tmp_history.last(5)) == 5


def test_corrupt_file_handled(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    h = RunHistory(path=p)
    assert h.last() == []
