"""Pipeline process monitor — runs a command and tracks duration/exit status."""

import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from pipewatch.slack import send_slack_alert, format_pipeline_message
from pipewatch.config import Config


@dataclass
class RunResult:
    command: str
    exit_code: int
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def run_pipeline(
    command: str,
    config: Config,
    timeout: Optional[float] = None,
    capture_output: bool = True,
) -> RunResult:
    """Run *command* in a shell, measure wall-clock time, and return a RunResult."""
    start = time.monotonic()
    timed_out = False

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = -1
        stdout = ""
        stderr = str(exc)

    duration = time.monotonic() - start

    result = RunResult(
        command=command,
        exit_code=exit_code,
        duration_seconds=round(duration, 3),
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )

    _maybe_alert(result, config)
    return result


def _maybe_alert(result: RunResult, config: Config) -> None:
    """Send a Slack alert when the pipeline fails or exceeds the duration threshold."""
    should_alert = not result.succeeded
    if config.alert_on_slow and config.slow_threshold_seconds is not None:
        if result.duration_seconds >= config.slow_threshold_seconds:
            should_alert = True

    if should_alert and config.webhook_url:
        message = format_pipeline_message(
            pipeline_name=config.pipeline_name,
            status="FAILED" if not result.succeeded else "SLOW",
            duration=result.duration_seconds,
            details=result.stderr or result.stdout,
        )
        send_slack_alert(config.webhook_url, message)
