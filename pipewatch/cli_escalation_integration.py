"""Integration helpers: check escalation state and fire Slack alerts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pipewatch.escalation import EscalationPolicy
from pipewatch.slack import send_slack_alert


@dataclass
class EscalationOutcome:
    checked: bool
    escalated: bool
    message: str = ""


def check_and_escalate(
    policy: EscalationPolicy,
    pipeline: str,
    webhook_url: Optional[str],
    extra_text: str = "",
) -> EscalationOutcome:
    """Check whether an escalation is due and, if so, send the Slack alert."""
    if not policy.is_enabled():
        return EscalationOutcome(checked=False, escalated=False)

    if not policy.should_escalate(pipeline):
        return EscalationOutcome(checked=True, escalated=False)

    msg = f":rotating_light: *Escalation* — `{pipeline}` has been failing for over {policy.after_seconds}s."
    if extra_text:
        msg += f"\n{extra_text}"

    if webhook_url:
        send_slack_alert(webhook_url, msg)

    policy.record_ping(pipeline)
    return EscalationOutcome(checked=True, escalated=True, message=msg)


def handle_run_result(
    policy: EscalationPolicy,
    pipeline: str,
    succeeded: bool,
    webhook_url: Optional[str] = None,
) -> EscalationOutcome:
    """Update escalation state based on run result and optionally escalate."""
    if not policy.is_enabled():
        return EscalationOutcome(checked=False, escalated=False)

    if succeeded:
        policy.clear(pipeline)
        return EscalationOutcome(checked=True, escalated=False)

    policy.record_failure(pipeline)
    return check_and_escalate(policy, pipeline, webhook_url)
