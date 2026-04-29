"""Shadow mode: run a pipeline without acting on results (dry-run comparison)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ShadowPolicy:
    enabled: bool = False
    label: str = "shadow"

    def is_enabled(self) -> bool:
        return self.enabled

    def describe(self) -> str:
        if not self.enabled:
            return "shadow mode disabled"
        return f"shadow mode enabled (label={self.label!r})"


@dataclass
class ShadowResult:
    policy: ShadowPolicy
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    elapsed: Optional[float] = None
    notes: list[str] = field(default_factory=list)

    def succeeded(self) -> bool:
        return self.exit_code == 0

    def summary(self) -> str:
        status = "ok" if self.succeeded() else f"exit={self.exit_code}"
        elapsed_s = f", elapsed={self.elapsed:.1f}s" if self.elapsed is not None else ""
        return f"[{self.policy.label}] {status}{elapsed_s}"


def run_shadow(
    policy: ShadowPolicy,
    command: str,
    timeout: Optional[float] = None,
) -> Optional[ShadowResult]:
    """Execute *command* in shadow mode and return a ShadowResult.

    Returns None when shadow mode is disabled so callers can skip
    processing without checking the policy themselves.
    """
    import subprocess
    import time

    if not policy.is_enabled():
        return None

    start = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        return ShadowResult(
            policy=policy,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            elapsed=elapsed,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return ShadowResult(
            policy=policy,
            exit_code=-1,
            elapsed=elapsed,
            notes=["timed out"],
        )
