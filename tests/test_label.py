"""Tests for pipewatch.label."""
from __future__ import annotations

import pytest

from pipewatch.label import (
    LabelSet,
    filter_from_labels,
    labels_from_config,
    parse_labels,
)


# ---------------------------------------------------------------------------
# parse_labels
# ---------------------------------------------------------------------------

def test_parse_labels_basic():
    ls = parse_labels(["env=prod", "team=data"])
    assert ls.get("env") == "prod"
    assert ls.get("team") == "data"


def test_parse_labels_none_returns_empty():
    ls = parse_labels(None)
    assert ls.to_dict() == {}


def test_parse_labels_empty_list_returns_empty():
    ls = parse_labels([])
    assert ls.to_dict() == {}


def test_parse_labels_value_contains_equals():
    ls = parse_labels(["url=http://x.com/a=b"])
    assert ls.get("url") == "http://x.com/a=b"


def test_parse_labels_missing_equals_raises():
    with pytest.raises(ValueError, match="key=value"):
        parse_labels(["noequalssign"])


def test_parse_labels_empty_key_raises():
    with pytest.raises(ValueError, match="empty"):
        parse_labels(["=value"])


# ---------------------------------------------------------------------------
# LabelSet.matches
# ---------------------------------------------------------------------------

def test_matches_all_present():
    ls = LabelSet({"env": "prod", "team": "data"})
    assert ls.matches({"env": "prod"}) is True


def test_matches_wrong_value():
    ls = LabelSet({"env": "prod"})
    assert ls.matches({"env": "staging"}) is False


def test_matches_missing_key():
    ls = LabelSet({"env": "prod"})
    assert ls.matches({"team": "data"}) is False


def test_matches_empty_filter_always_true():
    ls = LabelSet({"env": "prod"})
    assert ls.matches({}) is True


# ---------------------------------------------------------------------------
# LabelSet.format
# ---------------------------------------------------------------------------

def test_format_empty():
    assert LabelSet().format() == ""


def test_format_sorted():
    ls = LabelSet({"z": "last", "a": "first"})
    assert ls.format() == "a=first z=last"


# ---------------------------------------------------------------------------
# labels_from_config / filter_from_labels
# ---------------------------------------------------------------------------

def test_labels_from_config_dict():
    ls = labels_from_config({"env": "prod"})
    assert ls.get("env") == "prod"


def test_labels_from_config_none():
    ls = labels_from_config(None)
    assert ls.to_dict() == {}


def test_filter_from_labels_roundtrip():
    f = filter_from_labels(["env=prod", "team=data"])
    assert f == {"env": "prod", "team": "data"}
