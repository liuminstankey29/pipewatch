"""Output drain: capture, truncate, and forward stdout/stderr from pipeline runs."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB


@dataclass
class DrainPolicy:
    enabled: bool = False
    log_dir: str = ".pipewatch/drain"
    max_bytes: int = _DEFAULT_MAX_BYTES
    capture_stdout: bool = True
    capture_stderr: bool = True

    def is_enabled(self) -> bool:
        return self.enabled

    def describe(self) -> str:
        if not self.enabled:
            return "drain disabled"
        parts = []
        if self.capture_stdout:
            parts.append("stdout")
        if self.capture_stderr:
            parts.append("stderr")
        streams = "+".join(parts) or "none"
        kb = self.max_bytes // 1024
        return f"drain {streams} → {self.log_dir} (max {kb} KB)"


@dataclass
class DrainResult:
    pipeline: str
    run_id: str
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    bytes_written: int = 0

    def any_truncated(self) -> bool:
        """Return True if either stream was truncated due to the size limit."""
        return self.stdout_truncated or self.stderr_truncated


def _write_stream(data: bytes, dest: Path, max_bytes: int) -> tuple[int, bool]:
    """Write data to dest, truncating if needed. Returns (bytes_written, truncated)."""
    truncated = False
    if len(data) > max_bytes:
        data = data[-max_bytes:]  # keep the tail (most recent output)
        truncated = True
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data), truncated


def save_drain(
    policy: DrainPolicy,
    pipeline: str,
    run_id: str,
    stdout: Optional[bytes] = None,
    stderr: Optional[bytes] = None,
) -> Optional[DrainResult]:
    """Persist captured output according to *policy*. Returns None when disabled."""
    if not policy.is_enabled():
        return None

    result = DrainResult(pipeline=pipeline, run_id=run_id)
    base = Path(policy.log_dir) / pipeline / run_id
    total = 0

    if policy.capture_stdout and stdout is not None:
        p = base.with_suffix(".stdout")
        n, trunc = _write_stream(stdout, p, policy.max_bytes)
        result.stdout_path = str(p)
        result.stdout_truncated = trunc
        total += n

    if policy.capture_stderr and stderr is not None:
        p = base.with_suffix(".stderr")
        n, trunc = _write_stream(stderr, p, policy.max_bytes)
        result.stderr_path = str(p)
        result.stderr_truncated = trunc
        total += n

    result.bytes_written = total
    return result
