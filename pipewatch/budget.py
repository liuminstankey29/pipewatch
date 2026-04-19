"""Runtime budget: warn or fail when a pipeline exceeds a cost/time budget."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BudgetPolicy:
    max_seconds: Optional[float] = None
    warn_seconds: Optional[float] = None
    hard_fail: bool = False

    def is_enabled(self) -> bool:
        return self.max_seconds is not None or self.warn_seconds is not None

    def describe(self) -> str:
        parts = []
        if self.warn_seconds:
            parts.append(f"warn>{self.warn_seconds}s")
        if self.max_seconds:
            parts.append(f"max={self.max_seconds}s hard_fail={self.hard_fail}")
        return ", ".join(parts) if parts else "disabled"


@dataclass
class BudgetResult:
    elapsed: float
    warned: bool = False
    exceeded: bool = False
    hard_fail: bool = False
    message: str = ""

    def succeeded(self) -> bool:
        return not (self.exceeded and self.hard_fail)


def check_budget(policy: BudgetPolicy, elapsed: float) -> BudgetResult:
    """Evaluate elapsed time against the budget policy."""
    if not policy.is_enabled():
        return BudgetResult(elapsed=elapsed)

    warned = policy.warn_seconds is not None and elapsed > policy.warn_seconds
    exceeded = policy.max_seconds is not None and elapsed > policy.max_seconds
    hard_fail = exceeded and policy.hard_fail

    msg = ""
    if exceeded:
        msg = f"Budget exceeded: {elapsed:.1f}s > max {policy.max_seconds}s"
    elif warned:
        msg = f"Budget warning: {elapsed:.1f}s > warn {policy.warn_seconds}s"

    return BudgetResult(
        elapsed=elapsed,
        warned=warned,
        exceeded=exceeded,
        hard_fail=hard_fail,
        message=msg,
    )
