"""Checkpoint support: persist and restore pipeline progress markers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


_DEFAULT_DIR = Path.home() / ".pipewatch" / "checkpoints"


@dataclass
class Checkpoint:
    pipeline: str
    step: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"pipeline": self.pipeline, "step": self.step, "metadata": self.metadata}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Checkpoint":
        return Checkpoint(
            pipeline=d["pipeline"],
            step=d["step"],
            metadata=d.get("metadata", {}),
        )


def _checkpoint_path(pipeline: str, directory: Path) -> Path:
    safe = pipeline.replace("/", "_").replace(" ", "_")
    return directory / f"{safe}.json"


def save_checkpoint(cp: Checkpoint, directory: Optional[Path] = None) -> Path:
    base = Path(directory) if directory else _DEFAULT_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(cp.pipeline, base)
    path.write_text(json.dumps(cp.to_dict(), indent=2))
    return path


def load_checkpoint(pipeline: str, directory: Optional[Path] = None) -> Optional[Checkpoint]:
    base = Path(directory) if directory else _DEFAULT_DIR
    path = _checkpoint_path(pipeline, base)
    if not path.exists():
        return None
    return Checkpoint.from_dict(json.loads(path.read_text()))


def clear_checkpoint(pipeline: str, directory: Optional[Path] = None) -> bool:
    base = Path(directory) if directory else _DEFAULT_DIR
    path = _checkpoint_path(pipeline, base)
    if path.exists():
        path.unlink()
        return True
    return False
