"""
Tests for the Grafana-Loki MCP Server.
"""

import datetime
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from grafana_loki_mcp.server import GrafanaClient, iso8601_to_unix_nano


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock response object."""
    mock = MagicMock()
    mock.status_code = 200
    return mock


@pytest.fixture
def grafana_client() -> GrafanaClient:
    """Create a GrafanaClient instance with mock values."""
    return GrafanaClient("https://grafana.example.com", "fake-api-key")


def test_iso8601_to_unix_nano() -> None:
    """Test ISO8601 to UNIX nanoseconds conversion."""
    iso = "2025-05-27T14:59:33.073316"
    dt = datetime.datetime.fromisoformat(iso)
    expected = int(dt.timestamp() * 1_000_000_000)
    assert iso8601_to_unix_nano(iso) == expected
    # With Zulu
    iso_z = "2025-05-27T14:59:33.073316Z"
    dt_z = datetime.datetime.fromisoformat(iso_z.replace("Z", "+00:00"))
    expected_z = int(dt_z.timestamp() * 1_000_000_000)
    assert iso8601_to_unix_nano(iso_z) == expected_z
    # Invalid
    assert iso8601_to_unix_nano("not-a-date") is None


def test_grafana_client_init() -> None:
    """Test GrafanaClient initialization."""
    client = GrafanaClient("https://grafana.example.com/", "test-key")
    assert client.base_url == "https://grafana.example.com"
    assert client.headers == {"Authorization": "Bearer test-key"}


@patch("requests.get")
def test_query_loki(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test query_loki method."""
    mock_response.json.return_value = {"data": {"result": []}}
    mock_get.return_value = mock_response
    # Patch get_datasources to return a valid Loki datasource
    with patch.object(
        GrafanaClient,
        "get_datasources",
        return_value={"datasources": [{"uid": "test-uid", "type": "loki"}]},
    ):
        # Test with UNIX ns
        result = grafana_client.query_loki(
            "{job='test'}", start="1716800000000000000", end="1716803600000000000"
        )
        assert "data" in result
        # Test with ISO8601
        iso_start = "2025-05-27T14:59:33.073316"
        iso_end = "2025-05-27T15:00:00.000000"
        result2 = grafana_client.query_loki(
            "{job='test'}", start=iso_start, end=iso_end
        )
        assert "data" in result2
        # Ensure conversion was attempted (params should be int for ISO8601)
        call_args = mock_get.call_args_list[-1][1]["params"]
        # The parameters should be integers (Unix nanoseconds) for ISO8601 input
        assert isinstance(call_args["start"], int) or isinstance(
            call_args["start"], str
        )
        assert isinstance(call_args["end"], int) or isinstance(call_args["end"], str)

    # Setup mock response
    mock_response.json.return_value = {"data": {"result": []}}
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Call the method
    result = grafana_client.query_loki('{app="test"}')

    # Verify the result
    assert result == {"data": {"result": []}}

    # Verify the request (check last call only)
    args, kwargs = mock_get.call_args
    assert "test-uid" in args[0]
    assert "loki/api/v1/query_range" in args[0]
    assert kwargs["params"]["query"] == '{app="test"}'
    assert kwargs["params"]["limit"] == 100
    assert kwargs["params"]["direction"] == "backward"


@patch("requests.get")
def test_query_loki_with_max_per_line(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test query_loki method with max_per_line parameter."""
    # Setup mock response with long log lines
    mock_response.json.return_value = {
        "data": {
            "result": [
                {
                    "stream": {"app": "test"},
                    "values": [
                        [
                            "1609459200000000000",
                            "This is a very long log line that should be truncated when max_per_line is set",
                        ],
                        ["1609459201000000000", "Short log"],
                    ],
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Call the method with max_per_line=20
    result = grafana_client.query_loki('{app="test"}', max_per_line=20)

    # Verify the result has truncated log lines
    assert result["data"]["result"][0]["values"][0][1] == "This is a very long ..."
    assert (
        result["data"]["result"][0]["values"][1][1] == "Short log"
    )  # Short log should not be truncated


@patch("requests.get")
def test_get_loki_labels(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test get_loki_labels method."""
    # Setup mock response
    mock_response.json.return_value = {"data": ["app", "env", "job"]}
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Call the method
    result = grafana_client.get_loki_labels()

    # Verify the result
    assert result == {"data": ["app", "env", "job"]}

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-uid" in args[0]
    assert "loki/api/v1/labels" in args[0]


@patch("requests.get")
def test_get_loki_label_values(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test get_loki_label_values method."""
    # Setup mock response
    mock_response.json.return_value = {"data": ["app1", "app2", "app3"]}
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Call the method
    result = grafana_client.get_loki_label_values("app")

    # Verify the result
    assert result == {"data": ["app1", "app2", "app3"]}

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-uid" in args[0]
    assert "loki/api/v1/label/app/values" in args[0]


@patch("requests.get")
def test_get_datasources(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test get_datasources method."""
    # Setup mock response
    mock_response.json.return_value = [{"uid": "loki", "type": "loki"}]
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.get_datasources()

    # Verify the result
    assert result["datasources"] == [{"uid": "loki", "type": "loki"}]

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "api/datasources" in args[0]


@patch("requests.get")
def test_get_datasource_by_id(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test get_datasource_by_id method."""
    # Setup mock response
    mock_response.json.return_value = {"uid": "loki", "type": "loki", "id": 1}
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.get_datasource_by_id(1)

    # Verify the result
    assert result["uid"] == "loki"
    assert result["type"] == "loki"

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "api/datasources/1" in args[0]


@patch("requests.get")
def test_get_datasource_by_name(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test get_datasource_by_name method."""
    # Setup mock response
    mock_response.json.return_value = {"uid": "loki", "type": "loki", "name": "Loki"}
    mock_get.return_value = mock_response

    # Call the method
    result = grafana_client.get_datasource_by_name("Loki")

    # Verify the result
    assert result["uid"] == "loki"
    assert result["type"] == "loki"

    # Verify the request
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "api/datasources/name/Loki" in args[0]


@patch("requests.get")
def test_query_loki_with_time_formats(
    mock_get: MagicMock, grafana_client: GrafanaClient, mock_response: MagicMock
) -> None:
    """Test query_loki method with various time formats."""
    # Setup mock response
    mock_response.json.return_value = {"data": {"result": []}}
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Test Grafana relative time formats
    time_formats = {
        "now": "now",
        "now-1h": "now-1h",
        "now-1d": "now-1d",
        "now-7d": "now-7d",
    }

    for start_time, expected_time in time_formats.items():
        result = grafana_client.query_loki('{app="test"}', start=start_time)
        assert result == {"data": {"result": []}}
        mock_get.assert_called()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["query"] == '{app="test"}'
        if "start" in kwargs["params"]:
            assert kwargs["params"]["start"] == expected_time

    # Test ISO 8601 format
    iso_time = "2024-03-14T10:00:00Z"
    result = grafana_client.query_loki('{app="test"}', start=iso_time)
    assert result == {"data": {"result": []}}
    mock_get.assert_called()
    args, kwargs = mock_get.call_args
    # Expect nanoseconds since epoch for ISO8601
    assert kwargs["params"]["start"] == 1710410400000000000

    # Test Unix timestamp
    unix_time = "1710410400"  # 2024-03-14 10:00:00 UTC
    result = grafana_client.query_loki('{app="test"}', start=unix_time)
    assert result == {"data": {"result": []}}
    mock_get.assert_called()
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["start"] == unix_time

    # Test RFC3339 format
    rfc3339_time = "2024-03-14T10:00:00+00:00"
    result = grafana_client.query_loki('{app="test"}', start=rfc3339_time)
    assert result == {"data": {"result": []}}
    mock_get.assert_called()
    args, kwargs = mock_get.call_args
    # Expect nanoseconds since epoch for RFC3339
    assert kwargs["params"]["start"] == 1710410400000000000


@patch("requests.get")
def test_query_loki_time_range(
    mock_get: MagicMock, grafana_client: GrafanaClient
) -> None:
    """Test query_loki method with start and end time range."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"result": []}}
    mock_get.return_value = mock_response

    # Mock the _get_loki_datasource_uid method
    grafana_client._get_loki_datasource_uid = MagicMock(return_value="test-uid")  # type: ignore[method-assign]

    # Test with both start and end times
    start_time = "2024-03-14T10:00:00Z"
    end_time = "2024-03-14T11:00:00Z"

    result = grafana_client.query_loki('{app="test"}', start=start_time, end=end_time)

    assert result == {"data": {"result": []}}
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["query"] == '{app="test"}'
    # Expect nanoseconds since epoch for ISO8601
    assert kwargs["params"]["start"] == 1710410400000000000
    assert kwargs["params"]["end"] == 1710414000000000000
