"""
Tests for the parse_grafana_time function in the Grafana-Loki MCP Server.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grafana_loki_mcp.server import parse_grafana_time


def test_parse_grafana_time_empty() -> None:
    """Test parse_grafana_time with empty string input."""
    result = parse_grafana_time("")
    # Should return current time as Unix nanoseconds string
    assert result.isdigit()
    assert len(result) >= 18  # Unix nanoseconds should be 19 digits


def test_parse_grafana_time_now() -> None:
    """Test parse_grafana_time with 'now' input."""
    result = parse_grafana_time("now")
    # Should return current time as Unix nanoseconds string
    assert result.isdigit()
    assert len(result) >= 18  # Unix nanoseconds should be 19 digits


def test_parse_grafana_time_relative() -> None:
    """Test parse_grafana_time with relative time formats."""
    formats = ["now-1s", "now-5m", "now-2h", "now-1d", "now-1w", "now-1M", "now-1y"]
    for fmt in formats:
        result = parse_grafana_time(fmt)
        # Should return Unix nanoseconds string
        assert result.isdigit()
        assert len(result) >= 18  # Unix nanoseconds should be 19 digits


def test_parse_grafana_time_unix_timestamp() -> None:
    """Test parse_grafana_time with Unix timestamp."""
    result = parse_grafana_time("1609459200")
    # Should convert to nanoseconds
    assert result == "1609459200000000000"


def test_parse_grafana_time_iso_format() -> None:
    """Test parse_grafana_time with ISO format."""
    result = parse_grafana_time("2021-01-01T00:00:00")
    # Should return Unix nanoseconds string
    assert result.isdigit()
    # For 2021-01-01T00:00:00 UTC, this should be 1609459200000000000
    assert result == "1609459200000000000"


def test_parse_grafana_time_rfc3339() -> None:
    """Test parse_grafana_time with RFC3339 format."""
    result = parse_grafana_time("2021-01-01T00:00:00Z")
    # Should return Unix nanoseconds string
    assert result.isdigit()
    # For 2021-01-01T00:00:00Z UTC, this should be 1609459200000000000
    assert result == "1609459200000000000"


def test_parse_grafana_time_invalid() -> None:
    """Test parse_grafana_time with invalid format."""
    result = parse_grafana_time("invalid-format")
    # Should return current time as Unix nanoseconds string
    assert result.isdigit()
    assert len(result) >= 18  # Unix nanoseconds should be 19 digits
