#!/usr/bin/env python3
"""
Grafana-Loki MCP Server

A FastMCP server that queries Loki logs from Grafana.
"""

import argparse
import datetime
import json
import os
import re
import sys
from typing import Annotated, Any, Dict, Optional, Union, cast

# mypy: ignore-errors
import requests
from fastmcp import FastMCP

# Define version directly instead of importing
__version__ = "0.1.0"

# Create server
mcp = FastMCP(
    "Grafana-Loki Query Server",
    host="0.0.0.0",
    port=52229,
    allow_iframe=True,
    allow_cors=True,
)

# Default configuration
DEFAULT_GRAFANA_URL = os.environ.get("GRAFANA_URL", "")
DEFAULT_GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY", "")


def iso8601_to_unix_nano(ts: str) -> Optional[int]:
    """Convert ISO8601 string to UNIX nanoseconds. Return None if not ISO8601."""
    try:
        # Accepts e.g. 2025-05-27T14:59:33.073316 or 2025-05-27T14:59:33.073316Z
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1_000_000_000)
    except Exception:
        return None


class GrafanaClient:
    """Client for interacting with Grafana API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize the Grafana client.

        Args:
            base_url: Base URL of the Grafana instance
            api_key: Grafana API key
        """
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self._loki_datasource_uid: Optional[str] = None

    def _get_loki_datasource_uid(self) -> str:
        """Get the UID of the Loki datasource.

        Returns:
            UID of the Loki datasource
        """
        if self._loki_datasource_uid is not None:
            return self._loki_datasource_uid

        datasources = self.get_datasources()
        for ds in datasources.get("datasources", []):
            if ds.get("type") == "loki":
                # Try to get ID first, then UID
                ds_id = ds.get("id")
                if ds_id is not None:
                    # Convert ID to string for use in URL
                    self._loki_datasource_uid = str(ds_id)
                    return self._loki_datasource_uid

                # Fallback to UID if ID is not available
                uid = ds.get("uid")
                if uid is not None:
                    self._loki_datasource_uid = uid
                    return cast(str, uid)

        raise ValueError("No Loki datasource found")

    def query_loki(
        self,
        query: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        direction: str = "backward",
        max_per_line: int = 100,
    ) -> Dict[str, Any]:
        """Query Loki logs through Grafana.

        Args:
            query: Loki query string
            start: Start time (ISO format or UNIX ns, default: 1 hour ago)
            end: End time (ISO format or UNIX ns, default: now)
            limit: Maximum number of log lines to return
            direction: Query direction ('forward' or 'backward')
            max_per_line: Maximum characters per log line (0 for unlimited, default: 100)

        Returns:
            Dict containing query results
        """
        # Ensure we have valid time range
        if start is not None and end is None:
            # If start is provided but end is not, default end to current time
            end = "now"
        elif start is None and end is None:
            # If neither start nor end is provided, use default range
            start = "now-1h"
            end = "now"

        # Get Loki datasource UID
        datasource_id = self._get_loki_datasource_uid()

        # Prepare query
        base_url = f"{self.base_url}/api/datasources/proxy/{datasource_id}"

        url = f"{base_url}/loki/api/v1/query_range"
        params = {
            "query": query,
            "limit": limit,
            "direction": direction,
        }
        if start is not None:
            # Accept ISO8601 or UNIX ns or Grafana relative time
            if start.startswith("now") or start.isdigit():
                # Keep Grafana relative time or Unix timestamp as is
                params["start"] = start
            else:
                # Convert ISO8601 to UNIX nanoseconds
                unix_start = iso8601_to_unix_nano(start)
                params["start"] = unix_start if unix_start is not None else start
        if end is not None:
            # Accept ISO8601 or UNIX ns or Grafana relative time
            if end.startswith("now") or end.isdigit():
                # Keep Grafana relative time or Unix timestamp as is
                params["end"] = end
            else:
                # Convert ISO8601 to UNIX nanoseconds
                unix_end = iso8601_to_unix_nano(end)
                params["end"] = unix_end if unix_end is not None else end

        # Send request
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Apply max_per_line limit if specified
            if "data" in data and "result" in data["data"]:
                for stream in data["data"]["result"]:
                    if "values" in stream:
                        for i, value in enumerate(stream["values"]):
                            if (
                                len(value) > 1
                            ):  # Make sure we have [timestamp, log] format
                                # Truncate log line if it exceeds max_per_line
                                if len(value[1]) > max_per_line:
                                    stream["values"][i] = [
                                        value[0],
                                        value[1][:max_per_line] + "...",
                                    ]

            return cast(Dict[str, Any], data)
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error querying Loki: {error_detail}") from e

    def get_loki_labels(self) -> Dict[str, Any]:
        """Get all label names from Loki.

        Returns:
            Dict containing label names
        """
        url = f"{self.base_url}/api/datasources/proxy/{self._get_loki_datasource_uid()}/loki/api/v1/labels"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

        # ... rest of the file unchanged ...

        datasource_id = self._get_loki_datasource_uid()

        # Set base URL for API request
        base_url = f"{self.base_url}/api/datasources/proxy/{datasource_id}"

        url = f"{base_url}/loki/api/v1/labels"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error getting Loki labels: {error_detail}") from e

    def get_loki_label_values(self, label: str) -> Dict[str, Any]:
        """Get values for a specific label from Loki.

        Args:
            label: Label name

        Returns:
            Dict containing label values
        """
        datasource_id = self._get_loki_datasource_uid()

        # Set base URL for API request
        base_url = f"{self.base_url}/api/datasources/proxy/{datasource_id}"

        url = f"{base_url}/loki/api/v1/label/{label}/values"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error getting Loki label values: {error_detail}") from e

    def get_datasources(self) -> Dict[str, Any]:
        """Get all datasources from Grafana.

        Returns:
            Dict containing all datasources
        """
        url = f"{self.base_url}/api/datasources"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return {"datasources": cast(list, response.json())}
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error getting datasources: {error_detail}") from e

    def get_datasource_by_id(self, datasource_id: int) -> Dict[str, Any]:
        """Get a specific datasource by ID from Grafana.

        Args:
            datasource_id: ID of the datasource to retrieve

        Returns:
            Dict containing the datasource details
        """
        url = f"{self.base_url}/api/datasources/{datasource_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error getting datasource by ID: {error_detail}") from e

    def get_datasource_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific datasource by name from Grafana.

        Args:
            name: Name of the datasource to retrieve

        Returns:
            Dict containing the datasource details
        """
        url = f"{self.base_url}/api/datasources/name/{name}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            # Get more detailed error information
            error_detail = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_detail = f"{error_detail} - Details: {json.dumps(error_json)}"
                except Exception:
                    if e.response.text:
                        error_detail = f"{error_detail} - Response: {e.response.text}"

            # Raise a ValueError with the detailed error message
            raise ValueError(f"Error getting datasource by name: {error_detail}") from e


def get_grafana_client() -> GrafanaClient:
    """Get a configured Grafana client.

    Returns:
        Configured GrafanaClient instance
    """
    # Get configuration from environment variables or command line arguments
    parser = argparse.ArgumentParser(description="Grafana-Loki MCP Server")
    parser.add_argument(
        "-u",
        "--url",
        dest="grafana_url",
        default=DEFAULT_GRAFANA_URL,
        help="Grafana URL",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        dest="grafana_api_key",
        default=DEFAULT_GRAFANA_API_KEY,
        help="Grafana API key",
    )
    parser.add_argument(
        "-t",
        "--transport",
        dest="transport",
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport protocol (stdio or sse)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Grafana-Loki MCP Server {__version__}",
        help="Show version and exit",
    )

    args = parser.parse_args()

    # Check if required configuration is provided
    if not args.grafana_url:
        print("Error: Grafana URL is required", file=sys.stderr)
        print(
            "Set GRAFANA_URL environment variable or use --url command line argument",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.grafana_api_key:
        print("Error: Grafana API key is required", file=sys.stderr)
        msg = "Set GRAFANA_API_KEY environment variable"
        msg += " or use --api-key command line argument"
        print(msg, file=sys.stderr)
        sys.exit(1)

    # Set transport protocol
    # FastMCP doesn't have a transport attribute in the type stubs,
    # but it does in runtime
    mcp.transport = args.transport

    # Create and return client
    return GrafanaClient(args.grafana_url, args.grafana_api_key)


def parse_grafana_time(time_str: str) -> Union[str, datetime.datetime]:
    """Parse time string in various formats.

    Args:
        time_str: Time string in various formats:
            - Grafana relative time (e.g., 'now-1h', 'now')
            - ISO format (e.g., '2024-03-01T00:00:00')
            - Unix timestamp (e.g., '1709251200')
            - RFC3339 format

    Returns:
        Original string if it's a Grafana relative time or Unix timestamp,
        or datetime object for other formats
    """
    if not time_str:
        return "now"

    # Grafana relative time format - return as-is for Loki API
    if time_str == "now" or re.match(r"^now-\d+[smhdwMy]$", time_str):
        return time_str

    # Unix timestamp (numeric string) - return as-is
    if time_str.isdigit():
        return time_str

    # Try to parse as ISO format
    try:
        return datetime.datetime.fromisoformat(time_str)
    except ValueError:
        pass

    # Try to parse RFC3339 format
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", time_str):
        try:
            iso_str = (
                time_str.replace("Z", "+00:00") if time_str.endswith("Z") else time_str
            )
            return datetime.datetime.fromisoformat(iso_str)
        except ValueError:
            pass

    # If all parsing fails, return as Grafana relative time
    return "now"


def get_custom_query_loki_description() -> str:
    """Generate a custom description for the query_loki tool with available labels."""
    base_description = """
    Query Loki logs through Grafana.

    Args:
        query: Loki query string (LogQL). LogQL is Loki's query language that supports log filtering and extraction.
            Examples:
            - Simple log stream selection: `{app="frontend"}`
            - Filtering logs with pattern: `{app="frontend"} |= "error"`
            - Multiple filters: `{app="frontend"} |= "error" != "timeout"`
            - Regular expression: `{app="frontend"} |~ "error.*timeout"`
            - Extracting fields: `{app="frontend"} | json`
            - Extracting specific fields: `{app="frontend"} | json message,level`
            - Filtering on extracted fields: `{app="frontend"} | json | level="error"`
            - Counting logs: `count_over_time({app="frontend"} [5m])`
            - Rate of logs: `rate({app="frontend"} [5m])`
        start: Start time (Grafana format like 'now-1h', ISO format, Unix timestamp, or RFC3339, default: 1 hour ago)
        end: End time (Grafana format like 'now', ISO format, Unix timestamp, or RFC3339, default: now)
        limit: Maximum number of log lines to return
        direction: Query direction ('forward' or 'backward')
        max_per_line: Maximum characters per log line (0 for unlimited, default: 100)
    """

    # Add labels dynamically if possible
    try:
        client = get_grafana_client()
        labels_data = client.get_loki_labels()
        if "data" in labels_data and isinstance(labels_data["data"], list):
            available_labels = labels_data["data"]
            if available_labels:
                labels_str = ", ".join(
                    [f"`{label}`" for label in available_labels[:20]]
                )
                if len(available_labels) > 20:
                    labels_str += f", ... and {len(available_labels) - 20} more"
                base_description += f"\n\nAvailable labels: {labels_str}"
    except Exception:
        pass

    base_description += "\n\nReturns:\n    Dict containing query results"
    return base_description


# Use static description to avoid calling Grafana API at module load time
STATIC_LOKI_DESCRIPTION = """
Query Loki logs through Grafana.

Args:
    query: Loki query string (LogQL), Loki's domain-specific language for filtering and extracting logs.
        Note: Separate multiple labels with commas. E.g.: `{app="frontend", source="user"}`
        Examples:
        - Simple log stream selection: `{app="frontend"}`
        - Multiple labels: `{app="frontend", source="user"}`
        - Filtering logs with pattern: `{app="frontend"} |= "error"`
        - Multiple filters: `{app="frontend"} |= "error" != "timeout"`
        - Regular expression: `{app="frontend"} |~ "error.*timeout"`
        - Extracting fields: `{app="frontend"} | json`
        - Extracting specific fields: `{app="frontend"} | json message, level`
        - Filtering on extracted fields: `{app="frontend"} | json | level="error"`
        - Counting logs: `count_over_time({app="frontend"}[5m])`
        - Rate of logs: `rate({app="frontend"}[5m])`
    start: Start time, accepts Grafana time format (e.g., 'now-1h'), ISO8601, Unix timestamp, or RFC3339. Default: 1 hour ago.
    end: End time, accepts Grafana time format (e.g., 'now'), ISO8601, Unix timestamp, or RFC3339. Default: now.
    limit: Maximum number of log lines to return.
    direction: Query direction, either 'forward' or 'backward'.
    max_per_line: Maximum characters per log line (0 for unlimited). Default: 100.

Returns:
    A dictionary containing the query results.

References:
    - Introduction to LogQL: https://grafana.com/docs/loki/latest/logql/
    - LogQL filter expressions: https://grafana.com/docs/loki/latest/logql/filter-expr/
"""


class DescriptionManager:
    """
    Class to manage tool descriptions with label information.
    Delays actual Grafana API calls until needed during server execution.
    """

    def __init__(self):
        self._dynamic_description = None

    def get_description(self) -> str:
        """
        Returns dynamically generated description. Generates it if not already generated.
        """
        if self._dynamic_description is None:
            try:
                self._dynamic_description = get_custom_query_loki_description()
            except Exception:
                # Use static description if an error occurs
                self._dynamic_description = STATIC_LOKI_DESCRIPTION
        return self._dynamic_description


# Create description manager instance
description_manager = DescriptionManager()


@mcp.tool(
    description=STATIC_LOKI_DESCRIPTION
)  # Use static description as initial value
def query_loki(
    query: Annotated[str, "Loki query string (LogQL) to execute"],
    start: Annotated[
        Optional[str],
        "Start time (Grafana format like 'now-1h', ISO format, Unix timestamp, or RFC3339)",
    ] = None,
    end: Annotated[
        Optional[str],
        "End time (Grafana format like 'now', ISO format, Unix timestamp, or RFC3339)",
    ] = None,
    limit: Annotated[int, "Maximum number of log lines to return"] = 100,
    direction: Annotated[str, "Query direction ('forward' or 'backward')"] = "backward",
    max_per_line: Annotated[
        int, "Maximum characters per log line (0 for unlimited)"
    ] = 100,
) -> Dict[str, Any]:
    # Parse start and end times
    # Ensure end is set to current time if start is provided but end is not
    if start is not None and end is None:
        end = "now"  # Default end to current time when start is specified

    # Parse start time
    if start:
        parsed_start = parse_grafana_time(start)
        if isinstance(parsed_start, str):
            # Grafana relative time or Unix timestamp - use as-is
            start = parsed_start
        else:
            # Convert datetime to Unix nanoseconds
            start = str(int(parsed_start.timestamp() * 1_000_000_000))

    # Parse end time
    if end:
        parsed_end = parse_grafana_time(end)
        if isinstance(parsed_end, str):
            # Grafana relative time or Unix timestamp - use as-is
            end = parsed_end
        else:
            # Convert datetime to Unix nanoseconds
            end = str(int(parsed_end.timestamp() * 1_000_000_000))

    client = get_grafana_client()
    return client.query_loki(query, start, end, limit, direction, max_per_line)


# Update description when server starts
def update_query_loki_description():
    """Updates tool description with dynamic content when server starts"""
    try:
        # Get dynamic description after server is ready
        description = description_manager.get_description()
        mcp._tools["query_loki"].description = description
    except Exception:
        # Do nothing if an error occurs
        pass


# Fallback for when add_post_init_hook is not available
try:
    # Update description after server initialization
    mcp.add_post_init_hook(update_query_loki_description)
except AttributeError:
    # If FastMCP doesn't support add_post_init_hook,
    # override the run() method to update description after initialization
    original_run = mcp.run

    def patched_run(*args, **kwargs):
        """Patch for mcp.run to update tool descriptions"""
        # Update description before original execution
        update_query_loki_description()
        # Execute original run()
        return original_run(*args, **kwargs)

    # Override original method
    mcp.run = patched_run


@mcp.tool()
def get_loki_labels() -> Dict[str, Any]:
    """
    Get all label names from Loki.

    Returns:
        Dict containing label names
    """
    client = get_grafana_client()
    return client.get_loki_labels()


@mcp.tool()
def get_loki_label_values(label: str) -> Dict[str, Any]:
    """
    Get values for a specific label from Loki.

    Args:
        label: Label name

    Returns:
        Dict containing label values
    """
    client = get_grafana_client()
    return client.get_loki_label_values(label)


@mcp.tool()
def get_datasources() -> Dict[str, Any]:
    """
    Get all datasources from Grafana.

    Returns:
        Dict containing all datasources
    """
    client = get_grafana_client()
    return client.get_datasources()


@mcp.tool()
def get_datasource_by_id(datasource_id: int) -> Dict[str, Any]:
    """
    Get a specific datasource by ID from Grafana.

    Args:
        datasource_id: ID of the datasource to retrieve

    Returns:
        Dict containing the datasource details
    """
    client = get_grafana_client()
    return client.get_datasource_by_id(datasource_id)


@mcp.tool()
def get_datasource_by_name(name: str) -> Dict[str, Any]:
    """
    Get a specific datasource by name from Grafana.

    Args:
        name: Name of the datasource to retrieve

    Returns:
        Dict containing the datasource details
    """
    client = get_grafana_client()
    return client.get_datasource_by_name(name)
