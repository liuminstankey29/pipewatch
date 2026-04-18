import os
import json
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.pipewatch/config.json")


@dataclass
class Config:
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    alert_on_failure: bool = True
    alert_on_success: bool = False
    timeout_seconds: Optional[int] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        known_fields = {f for f in cls.__dataclass_fields__}
        known = {k: v for k, v in data.items() if k in known_fields}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        return cls(**known, extra=extra)

    @classmethod
    def load(cls, path: str = DEFAULT_CONFIG_PATH) -> "Config":
        if not os.path.exists(path):
            return cls()
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save(self, path: str = DEFAULT_CONFIG_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "slack_webhook_url": self.slack_webhook_url,
            "slack_channel": self.slack_channel,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_success": self.alert_on_success,
            "timeout_seconds": self.timeout_seconds,
            **self.extra,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def validate(self) -> list[str]:
        errors = []
        if (self.alert_on_failure or self.alert_on_success) and not self.slack_webhook_url:
            errors.append("slack_webhook_url is required when Slack alerting is enabled")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be a positive integer")
        return errors
