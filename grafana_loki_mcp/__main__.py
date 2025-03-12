"""Main entry point for the Grafana-Loki MCP package."""

# coverage: ignore


from grafana_loki_mcp.server import mcp


def main() -> None:
    """Run the Grafana-Loki MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
