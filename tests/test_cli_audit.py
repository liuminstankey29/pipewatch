"""Tests for pipewatch.cli_audit."""
from __future__ import annotations

import argparse
import pytest

from pipewatch.audit import append_event, AuditEvent
from pipewatch.cli_audit import add_audit_args, print_audit, _format_event


@pytest.fixture()
def adir(tmp_path):
    return str(tmp_path / "audit")


def _parse(args: list, log_dir: str) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    add_audit_args(p)
    ns = p.parse_args(args)
    ns.log_dir = log_dir
    return ns


def _seed(adir, pipeline="pipe", events=("run_start", "run_end")):
    for ev in events:
        append_event(AuditEvent(pipeline=pipeline, event=ev), log_dir=adir)


def test_print_all_events(adir, capsys):
    _seed(adir)
    args = _parse(["pipe"], log_dir=adir)
    print_audit(args)
    out = capsys.readouterr().out
    assert "run_start" in out
    assert "run_end" in out


def test_filter_event_type(adir, capsys):
    _seed(adir, events=["run_start", "alert_sent", "run_end"])
    args = _parse(["pipe", "--event", "alert_sent"], log_dir=adir)
    print_audit(args)
    out = capsys.readouterr().out
    assert "alert_sent" in out
    assert "run_start" not in out


def test_tail_limits_output(adir, capsys):
    _seed(adir, events=["e1", "e2", "e3", "e4"])
    args = _parse(["pipe", "--tail", "2"], log_dir=adir)
    print_audit(args)
    lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
    assert len(lines) == 2
    assert "e3" in lines[0]
    assert "e4" in lines[1]


def test_clear_flag(adir, capsys):
    _seed(adir)
    args = _parse(["pipe", "--clear"], log_dir=adir)
    print_audit(args)
    out = capsys.readouterr().out
    assert "cleared" in out.lower()
    # subsequent load returns nothing
    args2 = _parse(["pipe"], log_dir=adir)
    print_audit(args2)
    out2 = capsys.readouterr().out
    assert "no audit events" in out2.lower()


def test_no_events_message(adir, capsys):
    args = _parse(["empty_pipe"], log_dir=adir)
    print_audit(args)
    assert "no audit events" in capsys.readouterr().out.lower()


def test_format_event_with_detail():
    ev = AuditEvent(pipeline="p", event="run_end", ts="2024-01-01T00:00:00+00:00", detail={"exit_code": 0})
    s = _format_event(ev)
    assert "run_end" in s
    assert "exit_code=0" in s
    assert "2024-01-01" in s


def test_format_event_no_detail():
    ev = AuditEvent(pipeline="p", event="run_start", ts="T", detail={})
    s = _format_event(ev)
    assert s == "[T] run_start"
