#!/usr/bin/env python3
"""Command-line entry point for the Grafana-Loki MCP package."""

from grafana_loki_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
