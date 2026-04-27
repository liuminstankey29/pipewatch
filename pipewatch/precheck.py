"""Pre-run condition checks before a pipeline executes."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PrecheckPolicy:
    commands: List[str] = field(default_factory=list)
    require_binaries: List[str] = field(default_factory=list)
    timeout: int = 10

    def is_enabled(self) -> bool:
        return bool(self.commands or self.require_binaries)

    def describe(self) -> str:
        if not self.is_enabled():
            return "precheck disabled"
        parts = []
        if self.require_binaries:
            parts.append(f"binaries={self.require_binaries}")
        if self.commands:
            parts.append(f"{len(self.commands)} command(s)")
        return "precheck: " + ", ".join(parts)


@dataclass
class PrecheckResult:
    passed: bool
    failures: List[str] = field(default_factory=list)

    @property
    def message(self) -> str:
        if self.passed:
            return "all pre-run checks passed"
        return "pre-run checks failed: " + "; ".join(self.failures)


def _check_binary(name: str) -> Optional[str]:
    if shutil.which(name) is None:
        return f"required binary not found: {name}"
    return None


def _run_command(cmd: str, timeout: int) -> Optional[str]:
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            return f"command exited {result.returncode}: {cmd}"
        return None
    except subprocess.TimeoutExpired:
        return f"command timed out after {timeout}s: {cmd}"
    except Exception as exc:  # pragma: no cover
        return f"command error ({exc}): {cmd}"


def run_prechecks(policy: PrecheckPolicy) -> PrecheckResult:
    if not policy.is_enabled():
        return PrecheckResult(passed=True)

    failures: List[str] = []

    for binary in policy.require_binaries:
        err = _check_binary(binary)
        if err:
            failures.append(err)

    for cmd in policy.commands:
        err = _run_command(cmd, policy.timeout)
        if err:
            failures.append(err)

    return PrecheckResult(passed=not failures, failures=failures)
