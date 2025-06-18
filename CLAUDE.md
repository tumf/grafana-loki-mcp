# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastMCP server that allows querying Loki logs from Grafana through the Model Context Protocol (MCP). The server provides tools to query logs, get label information, and format results for Grafana/Loki log analysis.

## Development Commands

### Setup and Installation
```bash
# Install dependencies using uv (preferred package manager)
uv pip install -e ".[dev]"

# Install uv if not available
pip install uv
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term

# Run specific test files
pytest tests/test_server.py
pytest tests/test_parse_grafana_time.py
```

### Code Quality and Linting
```bash
# Run ruff linter
ruff check .

# Run black formatter
black .

# Run type checking
mypy .
```

### Running the Server
```bash
# Development mode with environment variables
export GRAFANA_URL=https://your-grafana-instance.com
export GRAFANA_API_KEY=your-api-key
python -m grafana_loki_mcp

# With command line arguments
python -m grafana_loki_mcp -u https://your-grafana-instance.com -k your-api-key

# Using uvx (for production)
uvx grafana-loki-mcp -u GRAFANA_URL -k GRAFANA_API_KEY
```

## Architecture

### Core Components

1. **GrafanaClient** (`grafana_loki_mcp/server.py`): Main client class that handles communication with Grafana API
   - Manages Loki datasource discovery and proxying
   - Handles time format conversion (ISO8601, Unix timestamps, Grafana relative times)
   - Provides error handling with detailed error messages

2. **FastMCP Server** (`grafana_loki_mcp/server.py`): MCP server implementation using FastMCP framework
   - Exposes tools for querying Loki logs, getting labels, and formatting results
   - Handles dynamic tool description updates with available labels
   - Supports both stdio and SSE transport protocols

3. **Time Parsing** (`parse_grafana_time` function): Handles multiple time formats
   - Grafana relative times (e.g., 'now-1h', 'now')
   - ISO8601 format
   - Unix timestamps
   - RFC3339 format

### Available MCP Tools

- `query_loki`: Query Loki logs with LogQL syntax
- `get_loki_labels`: Get all available label names from Loki
- `get_loki_label_values`: Get values for a specific label
- `format_loki_results`: Format query results in text, JSON, or markdown
- `get_datasources`: Get all Grafana datasources
- `get_datasource_by_id/name`: Get specific datasource information

### Key Configuration

- **Environment Variables**: `GRAFANA_URL`, `GRAFANA_API_KEY`
- **Transport Protocols**: stdio (default), sse
- **Server Port**: 52229 (for SSE mode)

## Test Structure

Tests use pytest with the following setup:
- `conftest.py`: Provides session-scoped mocks for Grafana API calls during testing
- Mock clients prevent actual API calls during test runs
- Tests cover time parsing, server functionality, and error handling

## Package Management

This project uses `uv` as the preferred package manager. Key dependencies:
- `fastmcp>=0.1.0`: FastMCP framework for MCP server implementation
- `requests>=2.25.0`: HTTP client for Grafana API communication
- Development dependencies include: black, ruff, mypy, pytest, pytest-cov

## Important Notes

- The server automatically discovers Loki datasources from Grafana
- Time handling supports both Grafana-style relative times and absolute timestamps
- Log line truncation is configurable via `max_per_line` parameter
- Error handling provides detailed information including response details from failed API calls
