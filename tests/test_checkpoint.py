"""Tests for pipewatch.checkpoint."""
from __future__ import annotations

import pytest
from pathlib import Path

from pipewatch.checkpoint import (
    Checkpoint,
    clear_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def cpdir(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints"


def test_save_and_load(cpdir: Path) -> None:
    cp = Checkpoint(pipeline="etl", step="transform", metadata={"rows": 42})
    save_checkpoint(cp, cpdir)
    loaded = load_checkpoint("etl", cpdir)
    assert loaded is not None
    assert loaded.pipeline == "etl"
    assert loaded.step == "transform"
    assert loaded.metadata == {"rows": 42}


def test_load_missing_returns_none(cpdir: Path) -> None:
    result = load_checkpoint("nonexistent", cpdir)
    assert result is None


def test_clear_existing(cpdir: Path) -> None:
    cp = Checkpoint(pipeline="pipe", step="load")
    save_checkpoint(cp, cpdir)
    removed = clear_checkpoint("pipe", cpdir)
    assert removed is True
    assert load_checkpoint("pipe", cpdir) is None


def test_clear_missing(cpdir: Path) -> None:
    removed = clear_checkpoint("ghost", cpdir)
    assert removed is False


def test_overwrite_checkpoint(cpdir: Path) -> None:
    cp1 = Checkpoint(pipeline="pipe", step="step1")
    cp2 = Checkpoint(pipeline="pipe", step="step2", metadata={"x": 1})
    save_checkpoint(cp1, cpdir)
    save_checkpoint(cp2, cpdir)
    loaded = load_checkpoint("pipe", cpdir)
    assert loaded is not None
    assert loaded.step == "step2"
    assert loaded.metadata == {"x": 1}


def test_pipeline_name_with_slashes(cpdir: Path) -> None:
    cp = Checkpoint(pipeline="team/etl", step="extract")
    save_checkpoint(cp, cpdir)
    loaded = load_checkpoint("team/etl", cpdir)
    assert loaded is not None
    assert loaded.pipeline == "team/etl"


def test_to_dict_roundtrip() -> None:
    cp = Checkpoint(pipeline="p", step="s", metadata={"k": "v"})
    assert Checkpoint.from_dict(cp.to_dict()).metadata == {"k": "v"}
