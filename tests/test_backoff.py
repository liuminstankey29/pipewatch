"""Tests for pipewatch.backoff."""
import pytest
from pipewatch.backoff import BackoffPolicy


def _no_sleep(s: float) -> None:
    pass


class TestBackoffPolicy:
    def test_defaults(self):
        p = BackoffPolicy()
        assert p.base == 2.0
        assert p.multiplier == 2.0
        assert p.max_delay == 300.0
        assert p.max_attempts == 5

    def test_enabled_when_multi_attempt(self):
        assert BackoffPolicy(max_attempts=3).is_enabled()

    def test_disabled_when_single_attempt(self):
        assert not BackoffPolicy(max_attempts=1).is_enabled()

    def test_describe_disabled(self):
        assert BackoffPolicy(max_attempts=1).describe() == "backoff disabled"

    def test_describe_enabled(self):
        desc = BackoffPolicy(base=1.0, multiplier=2.0, max_delay=60.0, max_attempts=4).describe()
        assert "backoff" in desc
        assert "1.0s" in desc
        assert "2.0x" in desc

    def test_invalid_base(self):
        with pytest.raises(ValueError, match="base"):
            BackoffPolicy(base=-1)

    def test_invalid_multiplier(self):
        with pytest.raises(ValueError, match="multiplier"):
            BackoffPolicy(multiplier=0.5)

    def test_invalid_max_delay(self):
        with pytest.raises(ValueError, match="max_delay"):
            BackoffPolicy(base=10.0, max_delay=5.0)

    def test_invalid_max_attempts(self):
        with pytest.raises(ValueError, match="max_attempts"):
            BackoffPolicy(max_attempts=0)

    def test_delays_count(self):
        p = BackoffPolicy(max_attempts=4)
        d = list(p.delays())
        assert len(d) == 3

    def test_delays_grow(self):
        p = BackoffPolicy(base=1.0, multiplier=2.0, max_delay=100.0, max_attempts=5)
        delays = list(p.delays())
        assert delays == [1.0, 2.0, 4.0, 8.0]

    def test_delays_capped(self):
        p = BackoffPolicy(base=10.0, multiplier=10.0, max_delay=50.0, max_attempts=4)
        for d in p.delays():
            assert d <= 50.0

    def test_run_succeeds_first(self):
        calls = []
        def fn():
            calls.append(1)
            return True
        p = BackoffPolicy(max_attempts=3)
        assert p.run(fn, _no_sleep) is True
        assert len(calls) == 1

    def test_run_succeeds_after_retry(self):
        results = [False, False, True]
        def fn():
            return results.pop(0)
        p = BackoffPolicy(base=0.0, max_attempts=3)
        assert p.run(fn, _no_sleep) is True

    def test_run_exhausts_attempts(self):
        p = BackoffPolicy(base=0.0, max_attempts=3)
        assert p.run(lambda: False, _no_sleep) is False

    def test_sleep_called_between_retries(self):
        slept = []
        p = BackoffPolicy(base=1.0, multiplier=2.0, max_delay=100.0, max_attempts=3)
        p.run(lambda: False, slept.append)
        assert len(slept) == 2
        assert slept[0] == 1.0
        assert slept[1] == 2.0
