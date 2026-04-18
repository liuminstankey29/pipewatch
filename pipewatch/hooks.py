"""Pre/post pipeline hook support for pipewatch."""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

log = logging.getLogger(__name__)


@dataclass
class HookConfig:
    pre: List[str] = field(default_factory=list)
    post: List[str] = field(default_factory=list)
    on_failure: List[str] = field(default_factory=list)
    timeout: Optional[int] = 30


@dataclass
class HookResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def run_hook(command: str, timeout: Optional[int] = 30) -> HookResult:
    """Run a single hook command and return its result."""
    log.debug("Running hook: %s", command)
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return HookResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        log.warning("Hook timed out: %s", command)
        return HookResult(command=command, returncode=-1, stdout="", stderr="timeout")


def run_hooks(commands: List[str], timeout: Optional[int] = 30) -> List[HookResult]:
    """Run a list of hook commands sequentially."""
    results = []
    for cmd in commands:
        result = run_hook(cmd, timeout=timeout)
        results.append(result)
        if not result.succeeded:
            log.warning("Hook failed (rc=%d): %s", result.returncode, cmd)
    return results


def hooks_from_config(cfg_dict: dict) -> HookConfig:
    hooks = cfg_dict.get("hooks", {})
    return HookConfig(
        pre=hooks.get("pre", []),
        post=hooks.get("post", []),
        on_failure=hooks.get("on_failure", []),
        timeout=hooks.get("timeout", 30),
    )
