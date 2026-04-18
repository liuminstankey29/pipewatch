"""Tests for pipewatch.lockfile."""
import pytest
from pathlib import Path

from pipewatch.lockfile import LockFile, LockError


@pytest.fixture
def ldir(tmp_path):
    return tmp_path / "locks"


def _lock(name, ldir):
    return LockFile(pipeline=name, lock_dir=ldir)


def test_acquire_creates_file(ldir):
    lf = _lock("pipe1", ldir)
    lf.acquire()
    assert lf.path.exists()
    lf.release()


def test_release_removes_file(ldir):
    lf = _lock("pipe1", ldir)
    lf.acquire()
    lf.release()
    assert not lf.path.exists()


def test_double_acquire_raises(ldir):
    lf = _lock("pipe1", ldir)
    lf.acquire()
    with pytest.raises(LockError, match="already running"):
        _lock("pipe1", ldir).acquire()
    lf.release()


def test_is_locked(ldir):
    lf = _lock("pipe2", ldir)
    assert not lf.is_locked()
    lf.acquire()
    assert lf.is_locked()
    lf.release()
    assert not lf.is_locked()


def test_info_returns_pid_and_started(ldir):
    lf = _lock("pipe3", ldir)
    assert lf.info() is None
    lf.acquire()
    info = lf.info()
    assert "pid" in info
    assert "started" in info
    lf.release()


def test_context_manager(ldir):
    lf = _lock("pipe4", ldir)
    with lf:
        assert lf.is_locked()
    assert not lf.is_locked()


def test_context_manager_releases_on_exception(ldir):
    lf = _lock("pipe5", ldir)
    try:
        with lf:
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert not lf.is_locked()


def test_release_missing_is_safe(ldir):
    lf = _lock("pipe6", ldir)
    lf.release()  # should not raise


def test_slash_in_name_sanitized(ldir):
    lf = _lock("org/pipe", ldir)
    assert "/" not in lf.path.name
