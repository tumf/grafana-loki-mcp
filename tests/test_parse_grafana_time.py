"""
Tests for the parse_grafana_time function in the Grafana-Loki MCP Server.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grafana_loki_mcp.server import parse_grafana_time


def test_parse_grafana_time_empty() -> None:
    """Test parse_grafana_time with empty string input."""
    result = parse_grafana_time("")
    assert result == "now"


def test_parse_grafana_time_now() -> None:
    """Test parse_grafana_time with 'now' input."""
    result = parse_grafana_time("now")
    assert result == "now"


def test_parse_grafana_time_relative() -> None:
    """Test parse_grafana_time with relative time formats."""
    formats = ["now-1s", "now-5m", "now-2h", "now-1d", "now-1w", "now-1M", "now-1y"]
    for fmt in formats:
        result = parse_grafana_time(fmt)
        assert result == fmt


def test_parse_grafana_time_unix_timestamp() -> None:
    """Test parse_grafana_time with Unix timestamp."""
    result = parse_grafana_time("1609459200")
    assert result == "1609459200"


def test_parse_grafana_time_iso_format() -> None:
    """Test parse_grafana_time with ISO format."""
    result = parse_grafana_time("2021-01-01T00:00:00")
    assert isinstance(result, datetime.datetime)
    assert result.year == 2021
    assert result.month == 1
    assert result.day == 1


def test_parse_grafana_time_rfc3339() -> None:
    """Test parse_grafana_time with RFC3339 format."""
    result = parse_grafana_time("2021-01-01T00:00:00Z")
    assert isinstance(result, datetime.datetime)
    assert result.year == 2021
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 0
    assert result.minute == 0
    assert result.second == 0


def test_parse_grafana_time_invalid() -> None:
    """Test parse_grafana_time with invalid format."""
    result = parse_grafana_time("invalid-format")
    assert result == "now"
