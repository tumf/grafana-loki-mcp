"""
Pytest configuration file for Grafana-Loki MCP tests.
"""

import os
import sys
from typing import Generator
from unittest.mock import patch

import pytest

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True, scope="session")
def mock_description_function() -> Generator[None, None, None]:
    """
    Mock the get_custom_query_loki_description function to prevent calls to Grafana API during tests.
    This is applied automatically to all tests.
    """
    description = """
    Query Loki logs through Grafana.

    Args:
        query: Loki query string (LogQL)
        start: Start time
        end: End time
        limit: Maximum number of log lines to return
        direction: Query direction
        max_per_line: Maximum characters per log line

    Available labels: `app`, `env`, `job`, `level`

    Returns:
        Dict containing query results
    """

    with patch(
        "grafana_loki_mcp.server.get_custom_query_loki_description",
        return_value=description,
    ):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_get_grafana_client() -> Generator[None, None, None]:
    """
    Mock the get_grafana_client function during imports to prevent SystemExit calls during tests.
    """
    from grafana_loki_mcp.server import GrafanaClient

    mock_client = GrafanaClient("http://mock-grafana", "mock-api-key")
    with patch("grafana_loki_mcp.server.get_grafana_client", return_value=mock_client):
        yield
