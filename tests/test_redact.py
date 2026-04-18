"""Tests for pipewatch.redact."""
import pytest
from pipewatch.redact import redact_dict, redact_str, sensitive_values, REDACTED


_SAMPLE: dict[str, str] = {
    "DATABASE_PASSWORD": "s3cr3t",
    "API_KEY": "abc123",
    "SLACK_TOKEN": "xoxb-999",
    "AUTH_HEADER": "Bearer xyz",
    "HOST": "localhost",
    "PORT": "5432",
}


def test_redact_dict_masks_sensitive():
    result = redact_dict(_SAMPLE)
    assert result["DATABASE_PASSWORD"] == REDACTED
    assert result["API_KEY"] == REDACTED
    assert result["SLACK_TOKEN"] == REDACTED
    assert result["AUTH_HEADER"] == REDACTED


def test_redact_dict_preserves_safe():
    result = redact_dict(_SAMPLE)
    assert result["HOST"] == "localhost"
    assert result["PORT"] == "5432"


def test_redact_dict_does_not_mutate_original():
    original = dict(_SAMPLE)
    redact_dict(_SAMPLE)
    assert _SAMPLE == original


def test_redact_dict_extra_patterns():
    data = {"MY_PRIVATE_VAR": "hidden", "PUBLIC": "visible"}
    result = redact_dict(data, extra_patterns=[r"(?i)private"])
    assert result["MY_PRIVATE_VAR"] == REDACTED
    assert result["PUBLIC"] == "visible"


def test_redact_dict_empty():
    assert redact_dict({}) == {}


def test_redact_str_replaces_known_values():
    text = "connecting with password=s3cr3t and token=xoxb-999"
    result = redact_str(text, ["s3cr3t", "xoxb-999"])
    assert "s3cr3t" not in result
    assert "xoxb-999" not in result
    assert REDACTED in result


def test_redact_str_ignores_empty_values():
    text = "hello world"
    result = redact_str(text, ["", None])  # type: ignore[list-item]
    assert result == "hello world"


def test_sensitive_values_returns_correct_values():
    vals = sensitive_values(_SAMPLE)
    assert "s3cr3t" in vals
    assert "abc123" in vals
    assert "localhost" not in vals


def test_sensitive_values_extra_patterns():
    data = {"MY_PRIV": "secret_val", "SAFE": "ok"}
    vals = sensitive_values(data, extra_patterns=[r"(?i)priv"])
    assert "secret_val" in vals
    assert "ok" not in vals
