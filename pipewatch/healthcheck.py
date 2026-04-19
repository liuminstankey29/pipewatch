"""HTTP/TCP health-check probes that can gate pipeline execution."""
from __future__ import annotations

import socket
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthCheckPolicy:
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    timeout: float = 5.0
    required: bool = True

    def is_enabled(self) -> bool:
        return bool(self.url or (self.host and self.port))

    def describe(self) -> str:
        if self.url:
            return f"HTTP {self.url} (timeout={self.timeout}s)"
        if self.host and self.port:
            return f"TCP {self.host}:{self.port} (timeout={self.timeout}s)"
        return "disabled"


@dataclass
class HealthCheckResult:
    ok: bool
    message: str
    policy: HealthCheckPolicy = field(repr=False)

    def succeeded(self) -> bool:
        return self.ok


def _check_http(url: str, timeout: float) -> HealthCheckResult:
    policy = HealthCheckPolicy(url=url, timeout=timeout)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status < 400:
                return HealthCheckResult(ok=True, message=f"HTTP {resp.status}", policy=policy)
            return HealthCheckResult(ok=False, message=f"HTTP {resp.status}", policy=policy)
    except Exception as exc:
        return HealthCheckResult(ok=False, message=str(exc), policy=policy)


def _check_tcp(host: str, port: int, timeout: float) -> HealthCheckResult:
    policy = HealthCheckPolicy(host=host, port=port, timeout=timeout)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return HealthCheckResult(ok=True, message=f"TCP {host}:{port} reachable", policy=policy)
    except Exception as exc:
        return HealthCheckResult(ok=False, message=str(exc), policy=policy)


def run_healthcheck(policy: HealthCheckPolicy) -> HealthCheckResult:
    if not policy.is_enabled():
        return HealthCheckResult(ok=True, message="no check configured", policy=policy)
    if policy.url:
        return _check_http(policy.url, policy.timeout)
    return _check_tcp(policy.host, policy.port, policy.timeout)  # type: ignore[arg-type]
