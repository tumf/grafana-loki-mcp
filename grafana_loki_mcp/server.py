#!/usr/bin/env python3
"""
Grafana-Loki MCP Server

A FastMCP server that queries Loki logs from Grafana.
"""

import argparse
import json
import os
import sys
from typing import Annotated, Any, Dict, Optional, cast

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
            start: Start time (ISO format, default: 1 hour ago)
            end: End time (ISO format, default: now)
            limit: Maximum number of log lines to return
            direction: Query direction ('forward' or 'backward')
            max_per_line: Maximum characters per log line (0 for unlimited, default: 100)

        Returns:
            Dict containing query results
        """
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
            params["start"] = start
        if end is not None:
            params["end"] = end

        # Send request
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            # Parse response
            data = response.json()
            
            # Apply max_per_line limit if specified
            if max_per_line > 0:
                if "data" in data and "result" in data["data"]:
                    for stream in data["data"]["result"]:
                        if "values" in stream:
                            for i, value in enumerate(stream["values"]):
                                if len(value) > 1:  # Make sure we have [timestamp, log] format
                                    # Truncate log line if it exceeds max_per_line
                                    if len(value[1]) > max_per_line:
                                        stream["values"][i] = [value[0], value[1][:max_per_line] + "..."]
            
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


# Tool definitions
@mcp.tool()
def query_loki(
    query: Annotated[str, "Loki query string (LogQL) to execute"],
    start: Annotated[
        Optional[str],
        "Start time (ISO format, Unix timestamp, or another supported format like RFC3339)",
    ] = None,
    end: Annotated[
        Optional[str],
        "End time (ISO format, Unix timestamp, or another supported format like RFC3339)",
    ] = None,
    limit: Annotated[int, "Maximum number of log lines to return"] = 100,
    direction: Annotated[str, "Query direction ('forward' or 'backward')"] = "backward",
    max_per_line: Annotated[int, "Maximum characters per log line (0 for unlimited)"] = 100,
) -> Dict[str, Any]:
    """
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
        start: Start time (ISO format, Unix timestamp, or another supported format like RFC3339, default: 1 hour ago)
        end: End time (ISO format, Unix timestamp, or another supported format like RFC3339, default: now)
        limit: Maximum number of log lines to return
        direction: Query direction ('forward' or 'backward')
        max_per_line: Maximum characters per log line (0 for unlimited, default: 100)

    Returns:
        Dict containing query results
    """
    client = get_grafana_client()
    return client.query_loki(query, start, end, limit, direction, max_per_line)


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


@mcp.tool()
def format_loki_results(
    results: Dict[str, Any],
    format_type: Annotated[str, "Output format ('text', 'json', or 'markdown')"] = "text",
    max_per_line: Annotated[int, "Maximum characters per log line (0 for unlimited)"] = 0
) -> str:
    """
    Format Loki query results in a more readable format.

    Args:
        results: Loki query results from query_loki
        format_type: Output format ('text', 'json', or 'markdown')
        max_per_line: Maximum characters per log line (0 for unlimited)

    Returns:
        Formatted results as a string
    """
    if format_type not in ["text", "json", "markdown"]:
        raise ValueError("Format type must be 'text', 'json', or 'markdown'")

    # Return JSON string if format is json
    if format_type == "json":
        return json.dumps(results, indent=2)

    # Extract streams from results
    streams = results.get("data", {}).get("result", [])
    if not streams:
        return "No results found"

    # Format results based on format_type
    if format_type == "text":
        output = []
        for stream in streams:
            labels = stream.get("stream", {})
            values = stream.get("values", [])
            output.append(f"Stream: {labels}")
            for value in values:
                timestamp, log = value
                # Truncate log if max_per_line is specified and > 0
                if max_per_line > 0 and len(log) > max_per_line:
                    log = log[:max_per_line] + "..."
                output.append(f"[{timestamp}] {log}")
            output.append("")
        return "\n".join(output)
    else:  # markdown
        output = []
        for stream in streams:
            labels = stream.get("stream", {})
            values = stream.get("values", [])
            output.append(f"### Stream: {labels}")
            output.append("")
            output.append("| Timestamp | Log |")
            output.append("| --- | --- |")
            for value in values:
                timestamp, log = value
                # Truncate log if max_per_line is specified and > 0
                if max_per_line > 0 and len(log) > max_per_line:
                    log = log[:max_per_line] + "..."
                # Escape pipe characters in log
                log = log.replace("|", "\\|")
                output.append(f"| {timestamp} | {log} |")
            output.append("")
        return "\n".join(output)


@mcp.tool()
def format_datasources_results(
    results: Dict[str, Any], format_type: str = "text"
) -> str:
    """
    Format datasources results in a more readable format.

    Args:
        results: Datasources results from get_datasources or get_datasource_by_id/name
        format_type: Output format ('text', 'json', or 'markdown')

    Returns:
        Formatted results as a string
    """
    if format_type not in ["text", "json", "markdown"]:
        raise ValueError("Format type must be 'text', 'json', or 'markdown'")

    # Return JSON string if format is json
    if format_type == "json":
        return json.dumps(results, indent=2)

    # Extract datasources from results
    datasources = results.get("datasources", [])
    if not datasources:
        # Check if results is a single datasource
        if "id" in results:
            datasources = [results]
        else:
            return "No datasources found"

    # Format results based on format_type
    if format_type == "text":
        output = []
        for ds in datasources:
            output.append(f"ID: {ds.get('id')}")
            output.append(f"Name: {ds.get('name')}")
            output.append(f"Type: {ds.get('type')}")
            output.append(f"URL: {ds.get('url')}")
            output.append("")
        return "\n".join(output)
    else:  # markdown
        output = []
        output.append("| ID | Name | Type | URL |")
        output.append("| --- | --- | --- | --- |")
        for ds in datasources:
            ds_id = ds.get("id", "")
            name = ds.get("name", "").replace("|", "\\|")
            ds_type = ds.get("type", "").replace("|", "\\|")
            url = ds.get("url", "").replace("|", "\\|")
            output.append(f"| {ds_id} | {name} | {ds_type} | {url} |")
        return "\n".join(output)


if __name__ == "__main__":
    # Start server
    mcp.run()
