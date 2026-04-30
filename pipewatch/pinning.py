"""Pipeline version pinning — record and enforce a pinned command fingerprint."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PinningPolicy:
    enabled: bool = False
    pin_file: str = ".pipewatch_pin"
    strict: bool = False  # if True, mismatch is a hard error; else a warning

    def is_enabled(self) -> bool:
        return self.enabled

    def describe(self) -> str:
        if not self.enabled:
            return "pinning disabled"
        mode = "strict" if self.strict else "warn"
        return f"pinning enabled ({mode}, pin_file={self.pin_file})"


@dataclass
class PinningResult:
    pinned_hash: Optional[str]
    current_hash: str
    mismatch: bool
    created: bool = False  # True when the pin file was just written

    def message(self) -> str:
        if self.created:
            return f"pinned pipeline at {self.current_hash[:12]}"
        if self.mismatch:
            short_pin = (self.pinned_hash or "")[:12]
            short_cur = self.current_hash[:12]
            return f"fingerprint mismatch: pinned={short_pin} current={short_cur}"
        return f"fingerprint matches pin {self.current_hash[:12]}"


def _pin_path(pin_file: str, state_dir: str = ".") -> Path:
    p = Path(pin_file)
    if not p.is_absolute():
        p = Path(state_dir) / p
    return p


def load_pin(pin_file: str, state_dir: str = ".") -> Optional[str]:
    path = _pin_path(pin_file, state_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data.get("hash")
    except (json.JSONDecodeError, OSError):
        return None


def save_pin(hash_value: str, pin_file: str, state_dir: str = ".") -> None:
    path = _pin_path(pin_file, state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"hash": hash_value}))


def check_pin(
    policy: PinningPolicy,
    current_hash: str,
    state_dir: str = ".",
) -> PinningResult:
    """Compare *current_hash* against the stored pin.

    If no pin exists yet, write one and return a ``created`` result.
    """
    pinned = load_pin(policy.pin_file, state_dir)
    if pinned is None:
        save_pin(current_hash, policy.pin_file, state_dir)
        return PinningResult(pinned_hash=None, current_hash=current_hash, mismatch=False, created=True)
    mismatch = pinned != current_hash
    return PinningResult(pinned_hash=pinned, current_hash=current_hash, mismatch=mismatch)
