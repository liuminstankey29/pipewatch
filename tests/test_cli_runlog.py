"""Tests for pipewatch.cli_runlog."""
import argparse
import types

import pytest

from pipewatch.cli_runlog import add_runlog_args, log_dir_from_config, print_runlogs
from pipewatch.runlog import DEFAULT_LOG_DIR, save_log, RunLog


def _parse(*args):
    p = argparse.ArgumentParser()
    add_runlog_args(p)
    return p.parse_args(list(args))


def _entry(**kw):
    defaults = dict(
        pipeline="etl",
        started_at="2024-01-01T10:00:00",
        finished_at="2024-01-01T10:01:00",
        exit_code=0,
        timed_out=False,
        duration=60.0,
        tags=["prod"],
    )
    defaults.update(kw)
    return RunLog(**defaults)


def test_defaults():
    ns = _parse()
    assert ns.log_dir == DEFAULT_LOG_DIR
    assert ns.log_pipeline is None
    assert ns.log_limit == 20


def test_log_dir_flag():
    ns = _parse("--log-dir", "/tmp/logs")
    assert ns.log_dir == "/tmp/logs"


def test_log_pipeline_flag():
    ns = _parse("--log-pipeline", "etl")
    assert ns.log_pipeline == "etl"


def test_log_limit_flag():
    ns = _parse("--log-limit", "5")
    assert ns.log_limit == 5


def test_print_runlogs_empty(tmp_path, capsys):
    ns = _parse("--log-dir", str(tmp_path))
    print_runlogs(ns)
    assert "No run logs" in capsys.readouterr().out


def test_print_runlogs_shows_entries(tmp_path, capsys):
    save_log(_entry(), log_dir=str(tmp_path))
    ns = _parse("--log-dir", str(tmp_path))
    print_runlogs(ns)
    out = capsys.readouterr().out
    assert "etl" in out
    assert "OK" in out


def test_log_dir_from_config():
    cfg = types.SimpleNamespace(log_dir="/custom")
    assert log_dir_from_config(cfg) == "/custom"


def test_log_dir_from_config_default():
    cfg = types.SimpleNamespace()
    assert log_dir_from_config(cfg) == DEFAULT_LOG_DIR
