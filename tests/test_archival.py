"""Tests for pipewatch.archival and pipewatch.cli_archival."""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipewatch.archival import ArchivalPolicy, archive_file, run_archival
from pipewatch.cli_archival import policy_from_args, policy_from_config


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_entry(path: Path, started_at: str) -> None:
    path.write_text(json.dumps({"started_at": started_at, "exit_code": 0}))


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
OLD = "2024-04-01T10:00:00+00:00"   # >30 days before NOW
RECENT = "2024-05-31T10:00:00+00:00"  # <30 days before NOW


# ---------------------------------------------------------------------------
# ArchivalPolicy
# ---------------------------------------------------------------------------

class TestArchivalPolicy:
    def test_disabled_by_default(self):
        p = ArchivalPolicy()
        assert not p.is_enabled()

    def test_enabled_when_flag_set(self):
        p = ArchivalPolicy(enabled=True, older_than_days=7)
        assert p.is_enabled()

    def test_disabled_when_zero_days(self):
        p = ArchivalPolicy(enabled=True, older_than_days=0)
        assert not p.is_enabled()

    def test_describe_disabled(self):
        assert "disabled" in ArchivalPolicy().describe()

    def test_describe_enabled(self):
        p = ArchivalPolicy(enabled=True, older_than_days=14, compress=True)
        desc = p.describe()
        assert "14d" in desc
        assert "compressed" in desc

    def test_cutoff_is_correct(self):
        p = ArchivalPolicy(enabled=True, older_than_days=30)
        cutoff = p.cutoff(NOW)
        assert cutoff.year == 2024
        assert cutoff.month == 5
        assert cutoff.day == 2


# ---------------------------------------------------------------------------
# archive_file
# ---------------------------------------------------------------------------

def test_archive_file_compressed(tmp_path):
    src = tmp_path / "run.json"
    src.write_text(json.dumps({"ok": True}))
    dest = archive_file(src, tmp_path / "archive", compress=True)
    assert dest.suffix == ".gz"
    assert not src.exists()
    with gzip.open(dest, "rb") as f:
        data = json.loads(f.read())
    assert data["ok"] is True


def test_archive_file_plain(tmp_path):
    src = tmp_path / "run.json"
    src.write_text(json.dumps({"ok": True}))
    dest = archive_file(src, tmp_path / "archive", compress=False)
    assert dest.suffix == ".json"
    assert not src.exists()
    assert json.loads(dest.read_text())["ok"] is True


# ---------------------------------------------------------------------------
# run_archival
# ---------------------------------------------------------------------------

def test_run_archival_disabled(tmp_path):
    _write_entry(tmp_path / "a.json", OLD)
    policy = ArchivalPolicy(enabled=False)
    result = run_archival(policy, tmp_path, now=NOW)
    assert result.archived == 0
    assert (tmp_path / "a.json").exists()


def test_run_archival_moves_old_file(tmp_path):
    _write_entry(tmp_path / "old.json", OLD)
    policy = ArchivalPolicy(
        enabled=True, older_than_days=30,
        archive_dir=str(tmp_path / "archive"), compress=False,
    )
    result = run_archival(policy, tmp_path, now=NOW)
    assert result.archived == 1
    assert result.skipped == 0
    assert not (tmp_path / "old.json").exists()
    assert (tmp_path / "archive" / "old.json").exists()


def test_run_archival_skips_recent_file(tmp_path):
    _write_entry(tmp_path / "new.json", RECENT)
    policy = ArchivalPolicy(
        enabled=True, older_than_days=30,
        archive_dir=str(tmp_path / "archive"), compress=False,
    )
    result = run_archival(policy, tmp_path, now=NOW)
    assert result.archived == 0
    assert result.skipped == 1
    assert (tmp_path / "new.json").exists()


def test_run_archival_skips_missing_timestamp(tmp_path):
    (tmp_path / "no_ts.json").write_text(json.dumps({"exit_code": 0}))
    policy = ArchivalPolicy(
        enabled=True, older_than_days=1,
        archive_dir=str(tmp_path / "archive"), compress=False,
    )
    result = run_archival(policy, tmp_path, now=NOW)
    assert result.skipped == 1
    assert result.archived == 0


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

class _FakeArgs:
    archive = True
    archive_older_than = 7
    archive_dir = "/tmp/arch"
    no_compress = True


def test_policy_from_args():
    p = policy_from_args(_FakeArgs())
    assert p.is_enabled()
    assert p.older_than_days == 7
    assert p.compress is False


def test_policy_from_config_defaults():
    p = policy_from_config({})
    assert not p.is_enabled()
    assert p.older_than_days == 30
    assert p.compress is True


def test_policy_from_config_custom():
    cfg = {"archival": {"enabled": True, "older_than_days": 60, "compress": False}}
    p = policy_from_config(cfg)
    assert p.is_enabled()
    assert p.older_than_days == 60
    assert p.compress is False
