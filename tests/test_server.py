"""
Tests for the Grafana-Loki MCP Server.
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add the parent directory to the path so we can import the server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import GrafanaClient, format_loki_results


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = MagicMock()
    mock.status_code = 200
    return mock


@pytest.fixture
def grafana_client():
    """Create a GrafanaClient instance with mock values."""
    return GrafanaClient("https://grafana.example.com", "fake-api-key")


def test_grafana_client_init():
    """Test GrafanaClient initialization."""
    client = GrafanaClient("https://grafana.example.com/", "test-key")
    assert client.base_url == "https://grafana.example.com"
    assert client.headers == {
        "Authorization": "Bearer test-key",
        "Content-Type": "application/json",
    }


@patch("requests.get")
def test_query_loki(mock_get, grafana_client, mock_response):
    """Test query_loki method."""
    # Setup mock response
    mock_response.json.return_value = {"data": {"result": []}}
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.query_loki('{app="test"}')

    # Verify the result
    assert result == {"data": {"result": []}}

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0].endswith("/api/datasources/proxy/loki/loki/api/v1/query_range")
    assert kwargs["params"]["query"] == '{app="test"}'
    assert kwargs["params"]["limit"] == 100
    assert kwargs["params"]["direction"] == "backward"


@patch("requests.get")
def test_get_loki_labels(mock_get, grafana_client, mock_response):
    """Test get_loki_labels method."""
    # Setup mock response
    mock_response.json.return_value = {"data": ["app", "env", "job"]}
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.get_loki_labels()

    # Verify the result
    assert result == {"data": ["app", "env", "job"]}

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0].endswith("/api/datasources/proxy/loki/loki/api/v1/labels")


@patch("requests.get")
def test_get_loki_label_values(mock_get, grafana_client, mock_response):
    """Test get_loki_label_values method."""
    # Setup mock response
    mock_response.json.return_value = {"data": ["app1", "app2", "app3"]}
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.get_loki_label_values("app")

    # Verify the result
    assert result == {"data": ["app1", "app2", "app3"]}

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0].endswith("/api/datasources/proxy/loki/loki/api/v1/label/app/values")


@patch("requests.get")
def test_query_loki_error(mock_get, grafana_client):
    """Test query_loki method with error."""
    # Setup mock to raise an exception
    mock_get.side_effect = requests.RequestException("Connection error")

    # Call the method
    result = grafana_client.query_loki('{app="test"}')

    # Verify the result contains the error
    assert result["status"] == "error"
    assert "Connection error" in result["error"]


def test_format_loki_results_text():
    """Test format_loki_results with text format."""
    # Sample Loki query result
    results = {
        "data": {
            "result": [
                {
                    "stream": {"app": "test", "env": "prod"},
                    "values": [
                        ["1609459200000000000", "Log line 1"],
                        ["1609459201000000000", "Log line 2"],
                    ],
                }
            ]
        }
    }

    # Format the results
    formatted = format_loki_results(results, "text")

    # Verify the formatted output
    assert "Stream: app=test, env=prod" in formatted
    assert "Log line 1" in formatted
    assert "Log line 2" in formatted


def test_format_loki_results_markdown():
    """Test format_loki_results with markdown format."""
    # Sample Loki query result
    results = {
        "data": {
            "result": [
                {
                    "stream": {"app": "test", "env": "prod"},
                    "values": [
                        ["1609459200000000000", "Log line 1"],
                        ["1609459201000000000", "Log line 2"],
                    ],
                }
            ]
        }
    }

    # Format the results
    formatted = format_loki_results(results, "markdown")

    # Verify the formatted output
    assert "### Stream: app=test, env=prod" in formatted
    assert "**" in formatted  # Check for bold timestamp
    assert "Log line 1" in formatted
    assert "Log line 2" in formatted


def test_format_loki_results_json():
    """Test format_loki_results with json format."""
    # Sample Loki query result
    results = {
        "data": {
            "result": [
                {
                    "stream": {"app": "test", "env": "prod"},
                    "values": [
                        ["1609459200000000000", "Log line 1"],
                        ["1609459201000000000", "Log line 2"],
                    ],
                }
            ]
        }
    }

    # Format the results
    formatted = format_loki_results(results, "json")

    # Verify the formatted output is valid JSON
    parsed = json.loads(formatted)
    assert isinstance(parsed, list)
    assert parsed[0]["stream"]["app"] == "test"
    assert parsed[0]["values"][0][1] == "Log line 1"


def test_format_loki_results_error():
    """Test format_loki_results with error result."""
    # Sample error result
    results = {"error": "Connection error", "status": "error"}

    # Format the results
    formatted = format_loki_results(results)

    # Verify the formatted output
    assert "Error: Connection error" in formatted


def test_format_loki_results_empty():
    """Test format_loki_results with empty result."""
    # Sample empty result
    results = {"data": {"result": []}}

    # Format the results
    formatted = format_loki_results(results)

    # Verify the formatted output
    assert "No log streams found" in formatted
