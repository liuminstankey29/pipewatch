"""Tests for pipewatch.healthcheck and pipewatch.cli_healthcheck."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.healthcheck import (
    HealthCheckPolicy,
    HealthCheckResult,
    run_healthcheck,
    _check_http,
    _check_tcp,
)
from pipewatch.cli_healthcheck import add_healthcheck_args, policy_from_args, resolve_healthcheck


# ---------------------------------------------------------------------------
# HealthCheckPolicy
# ---------------------------------------------------------------------------

def test_disabled_by_default():
    p = HealthCheckPolicy()
    assert not p.is_enabled()


def test_enabled_with_url():
    p = HealthCheckPolicy(url="http://localhost/health")
    assert p.is_enabled()


def test_enabled_with_host_port():
    p = HealthCheckPolicy(host="localhost", port=5432)
    assert p.is_enabled()


def test_describe_url():
    p = HealthCheckPolicy(url="http://x/h", timeout=3.0)
    assert "HTTP" in p.describe() and "3.0" in p.describe()


def test_describe_tcp():
    p = HealthCheckPolicy(host="db", port=5432)
    assert "TCP" in p.describe() and "5432" in p.describe()


def test_describe_disabled():
    assert HealthCheckPolicy().describe() == "disabled"


# ---------------------------------------------------------------------------
# run_healthcheck — no probe
# ---------------------------------------------------------------------------

def test_no_probe_returns_ok():
    result = run_healthcheck(HealthCheckPolicy())
    assert result.ok


# ---------------------------------------------------------------------------
# HTTP probe
# ---------------------------------------------------------------------------

def _mock_response(status: int):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_http_ok():
    with patch("urllib.request.urlopen", return_value=_mock_response(200)):
        r = _check_http("http://localhost/health", 5.0)
    assert r.ok


def test_http_server_error():
    with patch("urllib.request.urlopen", return_value=_mock_response(500)):
        r = _check_http("http://localhost/health", 5.0)
    assert not r.ok


def test_http_exception():
    with patch("urllib.request.urlopen", side_effect=OSError("refused")):
        r = _check_http("http://localhost/health", 5.0)
    assert not r.ok and "refused" in r.message


# ---------------------------------------------------------------------------
# TCP probe
# ---------------------------------------------------------------------------

def test_tcp_ok():
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = lambda s: s
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        r = _check_tcp("localhost", 5432, 5.0)
    assert r.ok


def test_tcp_fail():
    with patch("socket.create_connection", side_effect=OSError("timeout")):
        r = _check_tcp("localhost", 9999, 1.0)
    assert not r.ok


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*args):
    p = argparse.ArgumentParser()
    add_healthcheck_args(p)
    return p.parse_args(list(args))


def test_defaults():
    ns = _parse()
    pol = policy_from_args(ns)
    assert not pol.is_enabled()
    assert pol.timeout == 5.0
    assert pol.required is True


def test_url_flag():
    ns = _parse("--healthcheck-url", "http://svc/health")
    pol = policy_from_args(ns)
    assert pol.url == "http://svc/health"
    assert pol.is_enabled()


def test_optional_flag():
    ns = _parse("--healthcheck-url", "http://x", "--healthcheck-optional")
    pol = policy_from_args(ns)
    assert not pol.required
