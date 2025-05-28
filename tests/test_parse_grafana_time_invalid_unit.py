"""
Tests for the parse_grafana_time function with invalid unit.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grafana_loki_mcp.server import parse_grafana_time


def test_parse_grafana_time_invalid_unit() -> None:
    """Test parse_grafana_time with invalid unit."""
    result = parse_grafana_time("now-1z")  # Invalid unit 'z'
    assert result == "now"
