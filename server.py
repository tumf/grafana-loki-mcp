#!/usr/bin/env python3
"""
Grafana-Loki MCP Server

A FastMCP server that queries Loki logs from Grafana.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests
from fastmcp import FastMCP

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
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def query_loki(
        self,
        query: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        direction: str = "backward",
    ) -> Dict[str, Any]:
        """
        Query Loki logs through Grafana.

        Args:
            query: Loki query string
            start: Start time (default: 1 hour ago)
            end: End time (default: now)
            limit: Maximum number of log lines to return
            direction: Query direction ('forward' or 'backward')

        Returns:
            Dict containing query results
        """
        # Set default time range if not provided
        if not start:
            start = (datetime.now() - timedelta(hours=1)).isoformat()
        if not end:
            end = datetime.now().isoformat()

        # Construct the Loki query API endpoint
        url = f"{self.base_url}/api/datasources/proxy/loki/loki/api/v1/query_range"

        params: Dict[str, Any] = {
            "query": query,
            "start": start,
            "end": end,
            "limit": limit,
            "direction": direction,
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.RequestException as e:
            return {"error": str(e), "status": "error"}

    def get_loki_labels(self) -> Dict[str, Any]:
        """Get all label names from Loki."""
        url = f"{self.base_url}/api/datasources/proxy/loki/loki/api/v1/labels"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.RequestException as e:
            return {"error": str(e), "status": "error"}

    def get_loki_label_values(self, label: str) -> Dict[str, Any]:
        """Get values for a specific label from Loki."""
        endpoint = f"/api/datasources/proxy/loki/loki/api/v1/label/{label}/values"
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.RequestException as e:
            return {"error": str(e), "status": "error"}


# Global client instance
grafana_client = None


def get_grafana_client() -> GrafanaClient:
    """Get or create the Grafana client."""
    global grafana_client
    if grafana_client is None:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="Grafana-Loki MCP Server")
        parser.add_argument(
            "-u", "--grafana_url", default=DEFAULT_GRAFANA_URL, help="Grafana URL"
        )
        parser.add_argument(
            "-k",
            "--grafana_key",
            default=DEFAULT_GRAFANA_API_KEY,
            help="Grafana API key",
        )
        parser.add_argument(
            "--transport",
            choices=["stdio", "sse"],
            default="stdio",
            help="Transport protocol (stdio or sse)",
        )

        # Parse only known args to avoid conflicts with other arguments
        args, _ = parser.parse_known_args()

        if not args.grafana_url:
            print("Error: Grafana URL is required.")
            print("Set GRAFANA_URL environment variable or use --grafana_url")
            sys.exit(1)

        if not args.grafana_key:
            print("Error: Grafana API key is required.")
            print("Set GRAFANA_API_KEY environment variable or use --grafana_key")
            sys.exit(1)

        grafana_client = GrafanaClient(args.grafana_url, args.grafana_key)

    return grafana_client


@mcp.tool()
def query_loki(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    direction: str = "backward",
) -> Dict[str, Any]:
    """
    Query Loki logs through Grafana.

    Args:
        query: Loki query string
        start: Start time (ISO format, default: 1 hour ago)
        end: End time (ISO format, default: now)
        limit: Maximum number of log lines to return
        direction: Query direction ('forward' or 'backward')

    Returns:
        Dict containing query results
    """
    client = get_grafana_client()
    return client.query_loki(query, start, end, limit, direction)


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
def format_loki_results(results: Dict[str, Any], format_type: str = "text") -> str:
    """
    Format Loki query results in a more readable format.

    Args:
        results: Loki query results from query_loki
        format_type: Output format ('text', 'json', or 'markdown')

    Returns:
        Formatted results as a string
    """
    if "error" in results:
        return f"Error: {results['error']}"

    if "data" not in results or "result" not in results["data"]:
        return "No data found in results"

    streams = results["data"]["result"]

    if not streams:
        return "No log streams found"

    if format_type == "json":
        return json.dumps(streams, indent=2)

    output = []

    if format_type == "markdown":
        for stream in streams:
            labels = stream.get("stream", {})
            label_str = ", ".join([f"{k}={v}" for k, v in labels.items()])
            output.append(f"### Stream: {label_str}\n")

            for entry in stream.get("values", []):
                timestamp, log = entry
                # Convert nanosecond timestamp to readable format
                dt = datetime.fromtimestamp(int(timestamp[:10]))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                output.append(f"**{time_str}**: {log}\n")

            output.append("\n")
    else:  # text format
        for stream in streams:
            labels = stream.get("stream", {})
            label_str = ", ".join([f"{k}={v}" for k, v in labels.items()])
            output.append(f"Stream: {label_str}")

            for entry in stream.get("values", []):
                timestamp, log = entry
                # Convert nanosecond timestamp to readable format
                dt = datetime.fromtimestamp(int(timestamp[:10]))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                output.append(f"{time_str}: {log}")

            output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Grafana-Loki MCP Server")
    parser.add_argument(
        "-u", "--grafana_url", default=DEFAULT_GRAFANA_URL, help="Grafana URL"
    )
    parser.add_argument(
        "-k", "--grafana_key", default=DEFAULT_GRAFANA_API_KEY, help="Grafana API key"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (stdio or sse)",
    )

    args = parser.parse_args()

    # Initialize the Grafana client
    grafana_client = GrafanaClient(args.grafana_url, args.grafana_key)

    # Run the server
    mcp.run(transport=args.transport)
