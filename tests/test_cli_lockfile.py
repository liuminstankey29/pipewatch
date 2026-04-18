"""Tests for pipewatch.cli_lockfile."""
import argparse
from pathlib import Path

from pipewatch.cli_lockfile import add_lock_args, lock_from_args, lock_from_config
from pipewatch.lockfile import LockFile, _DEFAULT_DIR


def _parse(*args):
    p = argparse.ArgumentParser()
    add_lock_args(p)
    return p.parse_args(list(args))


def test_defaults():
    ns = _parse()
    assert ns.no_lock is False
    assert ns.lock_dir is None


def test_no_lock_flag():
    ns = _parse("--no-lock")
    assert ns.no_lock is True


def test_lock_dir_flag(tmp_path):
    ns = _parse("--lock-dir", str(tmp_path))
    assert ns.lock_dir == str(tmp_path)


def test_lock_from_args_default(tmp_path):
    ns = _parse()
    lf = lock_from_args("mypipe", ns)
    assert isinstance(lf, LockFile)
    assert lf.pipeline == "mypipe"


def test_lock_from_args_no_lock():
    ns = _parse("--no-lock")
    assert lock_from_args("mypipe", ns) is None


def test_lock_from_args_custom_dir(tmp_path):
    ns = _parse("--lock-dir", str(tmp_path))
    lf = lock_from_args("mypipe", ns)
    assert lf.lock_dir == tmp_path


def test_lock_from_config_disabled():
    assert lock_from_config("p", {"no_lock": True}) is None


def test_lock_from_config_custom_dir(tmp_path):
    lf = lock_from_config("p", {"lock_dir": str(tmp_path)})
    assert lf.lock_dir == tmp_path


def test_lock_from_config_default():
    lf = lock_from_config("p", {})
    assert lf.lock_dir == _DEFAULT_DIR
