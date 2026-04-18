import json
import urllib.request
import urllib.error
from typing import Optional


def _build_payload(text: str, channel: Optional[str] = None) -> dict:
    payload: dict = {"text": text}
    if channel:
        payload["channel"] = channel
    return payload


def send_slack_alert(
    webhook_url: str,
    message: str,
    channel: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """
    Send a message to Slack via an Incoming Webhook.
    Returns True on success, False on failure.
    """
    payload = _build_payload(message, channel)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(f"[pipewatch] Slack alert failed: HTTP {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"[pipewatch] Slack alert failed: {e.reason}")
    except Exception as e:
        print(f"[pipewatch] Slack alert failed: {e}")
    return False


def format_pipeline_message(
    job_name: str,
    status: str,
    duration_seconds: float,
    exit_code: Optional[int] = None,
    extra: Optional[str] = None,
) -> str:
    icon = ":white_check_mark:" if status == "success" else ":x:"
    lines = [
        f"{icon} *pipewatch* | Job: `{job_name}`",
        f"Status: *{status.upper()}*",
        f"Duration: {duration_seconds:.1f}s",
    ]
    if exit_code is not None:
        lines.append(f"Exit code: `{exit_code}`")
    if extra:
        lines.append(extra)
    return "\n".join(lines)
