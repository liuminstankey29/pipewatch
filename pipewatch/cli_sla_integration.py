"""Integration helpers: evaluate SLA after a pipeline run and emit alerts."""
from __future__ import annotations

import logging
from typing import Optional

from pipewatch.sla import SLAPolicy, SLAResult, check_sla
from pipewatch.slack import send_slack_alert, format_pipeline_message
from pipewatch.config import Config

log = logging.getLogger(__name__)


def evaluate_and_alert(
    elapsed: float,
    policy: SLAPolicy,
    cfg: Config,
    pipeline: str,
    exit_code: int = 0,
) -> Optional[SLAResult]:
    """Check SLA and send a Slack alert when the policy is breached or warns.

    Returns the SLAResult if the policy is enabled, else None.
    """
    if not policy.is_enabled():
        return None

    result = check_sla(elapsed=elapsed, policy=policy)

    if not (result.breached or result.warned):
        return result

    webhook = getattr(cfg, "slack_webhook", None)
    if not webhook:
        log.debug("SLA issue detected but no Slack webhook configured.")
        return result

    level = "breach" if result.breached else "warning"
    text = (
        f":alarm_clock: *SLA {level}* for pipeline `{pipeline}`\n"
        f"{result.message()}"
    )
    try:
        send_slack_alert(webhook, text)
        log.info("SLA alert sent to Slack (level=%s)", level)
    except Exception as exc:  # pragma: no cover
        log.error("Failed to send SLA Slack alert: %s", exc)

    return result


def sla_exit_code(result: Optional[SLAResult], base_exit: int = 0) -> int:
    """Return a non-zero exit code when an SLA has been breached.

    A warning does not affect the exit code; a breach returns 2.
    """
    if result is not None and result.breached:
        return 2
    return base_exit
