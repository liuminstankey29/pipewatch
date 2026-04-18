"""Tests for pipewatch.tags and pipewatch.cli_tags."""
import argparse
import pytest
from pipewatch.tags import TagFilter, parse_tags, format_tags, tags_from_config
from pipewatch.cli_tags import add_tag_args, tags_from_args, filter_from_args


# ---------------------------------------------------------------------------
# parse_tags
# ---------------------------------------------------------------------------

def test_parse_tags_basic():
    assert parse_tags("etl,nightly") == ["etl", "nightly"]


def test_parse_tags_deduplicates():
    assert parse_tags("a,a,b") == ["a", "b"]


def test_parse_tags_strips_whitespace():
    assert parse_tags(" etl , nightly ") == ["etl", "nightly"]


def test_parse_tags_none_returns_empty():
    assert parse_tags(None) == []


def test_parse_tags_empty_string_returns_empty():
    assert parse_tags("") == []


# ---------------------------------------------------------------------------
# TagFilter
# ---------------------------------------------------------------------------

def test_filter_no_required_matches_anything():
    assert TagFilter().matches(["a", "b"]) is True
    assert TagFilter().matches([]) is True


def test_filter_all_present():
    assert TagFilter(required=["etl", "nightly"]).matches(["etl", "nightly", "prod"]) is True


def test_filter_missing_one():
    assert TagFilter(required=["etl", "nightly"]).matches(["etl"]) is False


# ---------------------------------------------------------------------------
# format_tags
# ---------------------------------------------------------------------------

def test_format_tags_sorted():
    assert format_tags(["z", "a"]) == "[a] [z]"


def test_format_tags_empty():
    assert format_tags([]) == ""


# ---------------------------------------------------------------------------
# tags_from_config
# ---------------------------------------------------------------------------

def test_tags_from_config_deduplicates():
    assert tags_from_config(["b", "a", "a"]) == ["a", "b"]


def test_tags_from_config_none():
    assert tags_from_config(None) == []


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _parse(*argv):
    p = argparse.ArgumentParser()
    add_tag_args(p)
    return p.parse_args(list(argv))


def test_tags_from_args_parses_csv():
    args = _parse("--tags", "etl,nightly")
    assert tags_from_args(args) == ["etl", "nightly"]


def test_tags_from_args_default_empty():
    args = _parse()
    assert tags_from_args(args) == []


def test_filter_from_args_builds_filter():
    args = _parse("--filter-tags", "etl")
    f = filter_from_args(args)
    assert f.required == ["etl"]
    assert f.matches(["etl", "prod"]) is True
    assert f.matches(["prod"]) is False


def test_filter_from_args_no_flag_matches_all():
    args = _parse()
    f = filter_from_args(args)
    assert f.matches([]) is True
