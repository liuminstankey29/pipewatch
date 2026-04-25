"""Tests for pipewatch.audit."""
from __future__ import annotations

import json
import pytest

from pipewatch.audit import (
    AuditEvent,
    append_event,
    load_events,
    clear_events,
    _log_path,
)


@pytest.fixture()
def adir(tmp_path):
    return str(tmp_path / "audit")


def _ev(pipeline="pipe", event="run_start", **detail) -> AuditEvent:
    return AuditEvent(pipeline=pipeline, event=event, detail=detail)


def test_append_and_load(adir):
    ev = _ev(exit_code=0)
    append_event(ev, log_dir=adir)
    events = load_events("pipe", log_dir=adir)
    assert len(events) == 1
    assert events[0].event == "run_start"
    assert events[0].detail["exit_code"] == 0


def test_multiple_events_ordered(adir):
    for name in ("run_start", "run_end", "alert_sent"):
        append_event(_ev(event=name), log_dir=adir)
    events = load_events("pipe", log_dir=adir)
    assert [e.event for e in events] == ["run_start", "run_end", "alert_sent"]


def test_filter_by_event_type(adir):
    append_event(_ev(event="run_start"), log_dir=adir)
    append_event(_ev(event="alert_sent"), log_dir=adir)
    append_event(_ev(event="run_end"), log_dir=adir)
    alerts = load_events("pipe", log_dir=adir, event_type="alert_sent")
    assert len(alerts) == 1
    assert alerts[0].event == "alert_sent"


def test_load_missing_returns_empty(adir):
    assert load_events("nonexistent", log_dir=adir) == []


def test_clear_removes_file(adir):
    append_event(_ev(), log_dir=adir)
    clear_events("pipe", log_dir=adir)
    assert load_events("pipe", log_dir=adir) == []


def test_clear_missing_is_noop(adir):
    clear_events("ghost", log_dir=adir)  # should not raise


def test_to_dict_roundtrip():
    ev = _ev(event="hook_fired", hook="pre_run")
    d = ev.to_dict()
    ev2 = AuditEvent.from_dict(d)
    assert ev2.pipeline == ev.pipeline
    assert ev2.event == ev.event
    assert ev2.detail == ev.detail
    assert ev2.ts == ev.ts


def test_separate_pipelines_isolated(adir):
    append_event(_ev(pipeline="alpha", event="run_start"), log_dir=adir)
    append_event(_ev(pipeline="beta", event="alert_sent"), log_dir=adir)
    assert len(load_events("alpha", log_dir=adir)) == 1
    assert len(load_events("beta", log_dir=adir)) == 1


def test_corrupt_line_skipped(adir):
    path = _log_path(adir, "pipe")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"pipeline":"pipe","event":"run_start","ts":"x","detail":{}}\nNOT_JSON\n')
    events = load_events("pipe", log_dir=adir)
    assert len(events) == 1
