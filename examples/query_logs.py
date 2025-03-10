#!/usr/bin/env python3
"""
Example script to query logs from Grafana-Loki MCP Server.
"""

import asyncio
import json
import os
import sys

# Add the parent directory to the path so we can import the client
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from fastmcp.client import Client
except ImportError:
    print("Error: fastmcp package not found.")
    print("Please install it with 'pip install fastmcp'")
    sys.exit(1)


async def main():
    """Query logs from Grafana-Loki MCP Server."""
    # Connect to the MCP server
    async with Client() as client:
        # Get available labels
        print("Getting available labels...")
        labels = await client.call_tool("get_loki_labels")
        print(f"Available labels: {json.dumps(labels, indent=2)}")

        # Query logs
        print("\nQuerying logs...")
        query = '{app="example"} |= "error"'
        results = await client.call_tool("query_loki", {"query": query, "limit": 10})

        # Format the results
        print("\nFormatting results...")
        formatted = await client.call_tool(
            "format_loki_results", {"results": results, "format_type": "markdown"}
        )

        print("\nResults:")
        print(formatted)


if __name__ == "__main__":
    asyncio.run(main())
