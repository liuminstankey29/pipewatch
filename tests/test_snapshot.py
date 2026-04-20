"""Tests for pipewatch.snapshot."""
import os
import pytest

from pipewatch.snapshot import (
    Snapshot,
    SnapshotDiff,
    diff_snapshots,
    load_snapshot,
    make_snapshot,
    save_snapshot,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sdir(tmp_path):
    return str(tmp_path / "snapshots")


def _snap(pipeline="pipe", exit_code=0, elapsed=10.0, tags=None, extra=None):
    return make_snapshot(
        pipeline=pipeline,
        exit_code=exit_code,
        elapsed=elapsed,
        tags=tags or {},
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# Snapshot basics
# ---------------------------------------------------------------------------

def test_succeeded_zero():
    assert _snap(exit_code=0).succeeded() is True


def test_succeeded_nonzero():
    assert _snap(exit_code=1).succeeded() is False


def test_to_dict_roundtrip():
    s = _snap(tags={"env": "prod"}, extra={"rows": 42})
    d = s.to_dict()
    s2 = Snapshot.from_dict(d)
    assert s2.pipeline == s.pipeline
    assert s2.exit_code == s.exit_code
    assert s2.elapsed == s.elapsed
    assert s2.tags == {"env": "prod"}
    assert s2.extra == {"rows": 42}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_creates_file(sdir):
    s = _snap()
    save_snapshot(s, sdir)
    files = os.listdir(sdir)
    assert any(".snapshot.json" in f for f in files)


def test_save_and_load_roundtrip(sdir):
    s = _snap(pipeline="my-pipe", exit_code=2, elapsed=99.5)
    save_snapshot(s, sdir)
    loaded = load_snapshot("my-pipe", sdir)
    assert loaded is not None
    assert loaded.exit_code == 2
    assert loaded.elapsed == 99.5


def test_load_missing_returns_none(sdir):
    result = load_snapshot("nonexistent", sdir)
    assert result is None


def test_save_overwrites_previous(sdir):
    save_snapshot(_snap(exit_code=0, elapsed=5.0), sdir)
    save_snapshot(_snap(exit_code=1, elapsed=8.0), sdir)
    loaded = load_snapshot("pipe", sdir)
    assert loaded.exit_code == 1
    assert loaded.elapsed == 8.0


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def test_diff_no_changes():
    old = _snap(exit_code=0, elapsed=10.0, tags={"env": "prod"})
    new = _snap(exit_code=0, elapsed=10.0, tags={"env": "prod"})
    d = diff_snapshots(old, new)
    assert d.has_changes() is False
    assert d.summary() == "no changes"


def test_diff_exit_code_changed():
    d = diff_snapshots(_snap(exit_code=0), _snap(exit_code=1))
    assert d.exit_code_changed is True
    assert d.has_changes() is True
    assert "exit code changed" in d.summary()


def test_diff_elapsed_slower():
    d = diff_snapshots(_snap(elapsed=10.0), _snap(elapsed=15.5))
    assert d.elapsed_delta == pytest.approx(5.5)
    assert "slower" in d.summary()


def test_diff_elapsed_faster():
    d = diff_snapshots(_snap(elapsed=20.0), _snap(elapsed=12.0))
    assert d.elapsed_delta == pytest.approx(-8.0)
    assert "faster" in d.summary()


def test_diff_tags_added():
    old = _snap(tags={"env": "prod"})
    new = _snap(tags={"env": "prod", "region": "us-east"})
    d = diff_snapshots(old, new)
    assert d.tags_added == {"region": "us-east"}
    assert d.tags_removed == {}
    assert d.has_changes() is True


def test_diff_tags_removed():
    old = _snap(tags={"env": "prod", "region": "us-east"})
    new = _snap(tags={"env": "prod"})
    d = diff_snapshots(old, new)
    assert d.tags_removed == {"region": "us-east"}
    assert d.tags_added == {}
