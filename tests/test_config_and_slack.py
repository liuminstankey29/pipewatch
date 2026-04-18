import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from pipewatch.config import Config
from pipewatch.slack import format_pipeline_message, send_slack_alert


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = Config()
        self.assertIsNone(cfg.slack_webhook_url)
        self.assertTrue(cfg.alert_on_failure)
        self.assertFalse(cfg.alert_on_success)

    def test_from_dict(self):
        cfg = Config.from_dict({"slack_webhook_url": "https://hooks.slack.com/x", "unknown_key": 42})
        self.assertEqual(cfg.slack_webhook_url, "https://hooks.slack.com/x")
        self.assertEqual(cfg.extra["unknown_key"], 42)

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            cfg = Config(slack_webhook_url="https://hooks.slack.com/test", timeout_seconds=120)
            cfg.save(path)
            loaded = Config.load(path)
            self.assertEqual(loaded.slack_webhook_url, "https://hooks.slack.com/test")
            self.assertEqual(loaded.timeout_seconds, 120)

    def test_validate_missing_webhook(self):
        cfg = Config(alert_on_failure=True, slack_webhook_url=None)
        errors = cfg.validate()
        self.assertTrue(any("slack_webhook_url" in e for e in errors))

    def test_validate_bad_timeout(self):
        cfg = Config(slack_webhook_url="https://x", timeout_seconds=-5)
        errors = cfg.validate()
        self.assertTrue(any("timeout_seconds" in e for e in errors))

    def test_validate_ok(self):
        cfg = Config(slack_webhook_url="https://hooks.slack.com/x", timeout_seconds=60)
        self.assertEqual(cfg.validate(), [])


class TestSlack(unittest.TestCase):
    def test_format_success(self):
        msg = format_pipeline_message("etl_job", "success", 42.5, exit_code=0)
        self.assertIn("etl_job", msg)
        self.assertIn("SUCCESS", msg)
        self.assertIn("42.5s", msg)

    def test_format_failure(self):
        msg = format_pipeline_message("etl_job", "failure", 10.0, exit_code=1, extra="OOM error")
        self.assertIn(":x:", msg)
        self.assertIn("OOM error", msg)

    @patch("pipewatch.slack.urllib.request.urlopen")
    def test_send_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_urlopen.return_value = mock_resp
        result = send_slack_alert("https://hooks.slack.com/x", "hello")
        self.assertTrue(result)

    @patch("pipewatch.slack.urllib.request.urlopen", side_effect=Exception("network error"))
    def test_send_failure(self, _):
        result = send_slack_alert("https://hooks.slack.com/x", "hello")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
