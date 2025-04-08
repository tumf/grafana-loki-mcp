# Grafana-Loki MCP Server

[![Test](https://github.com/tumf/grafana-loki-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/tumf/grafana-loki-mcp/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/grafana-loki-mcp.svg)](https://badge.fury.io/py/grafana-loki-mcp)
[![codecov](https://codecov.io/gh/tumf/grafana-loki-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/tumf/grafana-loki-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [FastMCP](https://github.com/jlowin/fastmcp) server that allows querying Loki logs from Grafana.

## MCP Server Settings

```json
{
  "mcpServers": {
    "loki": {
      "command": "uvx",
      "args": [
        "grafana-loki-mcp",
        "-u",
        "GRAFANA_URL",
        "-k",
        "GRAFANA_API_KEY"
      ]
    }
  }
}
```

- `GRAFANA_URL`: URL of your Grafana instance
- `GRAFANA_API_KEY`: Grafana API key with appropriate permissions

## Features

- Query Loki logs through Grafana API
- Get Loki labels and label values
- Format query results in different formats (text, JSON, markdown)
- Support for both stdio and SSE transport protocols

## Requirements

- Python 3.10+
- FastMCP
- Requests

## Installation

### Using pip

```bash
pip install grafana-loki-mcp
```

### Development Setup

1. Clone this repository
2. Install dependencies using uv:

```bash
# Install uv
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Usage

### Environment Variables

Set the following environment variables:

- `GRAFANA_URL`: URL of your Grafana instance
- `GRAFANA_API_KEY`: Grafana API key with appropriate permissions

### Command Line Arguments

You can also provide these values as command line arguments:

```bash
grafana-loki-mcp -u https://your-grafana-instance.com -k your-api-key
```

Additional options:
- `--transport`: Transport protocol to use (`stdio` or `sse`, default: `stdio`)

### Running the Server

```bash
# Using environment variables
export GRAFANA_URL=https://your-grafana-instance.com
export GRAFANA_API_KEY=your-api-key
grafana-loki-mcp

# Using command line arguments
grafana-loki-mcp -u https://your-grafana-instance.com -k your-api-key

# Using SSE transport
grafana-loki-mcp --transport sse
```

## Development

### Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=. --cov-report=term
```

### Linting and Formatting

```bash
# Run ruff linter
ruff check .

# Run black formatter
black .

# Run type checking
mypy .
```

## Available Tools

### query_loki

Query Loki logs through Grafana.

Parameters:
- `query`: Loki query string
- `start`: Start time (ISO format, Unix timestamp, or Grafana-style relative time like 'now-1h', default: 1 hour ago)
- `end`: End time (ISO format, Unix timestamp, or Grafana-style relative time like 'now', default: now)
- `limit`: Maximum number of log lines to return (default: 100)
- `direction`: Query direction ('forward' or 'backward', default: 'backward')
- `max_per_line`: Maximum characters per log line (0 for unlimited, default: 100)

### get_loki_labels

Get all label names from Loki.

### get_loki_label_values

Get values for a specific label from Loki.

Parameters:
- `label`: Label name

### format_loki_results

Format Loki query results in a more readable format.

Parameters:
- `results`: Loki query results from query_loki
- `format_type`: Output format ('text', 'json', or 'markdown', default: 'text')
- `max_per_line`: Maximum characters per log line (0 for unlimited, default: 0)

## Example Usage

```python
# Example client code
from mcp.client import Client

async with Client() as client:
    # Query Loki logs with max_per_line limit
    results = await client.call_tool(
        "query_loki",
        {
            "query": '{app="my-app"} |= "error"',
            "limit": 50,
            "max_per_line": 100,  # Limit log lines to 100 characters
            "start": "now-6h",    # Grafana-style relative time: 6 hours ago
            "end": "now"          # Current time
        }
    )

    # Format the results
    formatted = await client.call_tool(
        "format_loki_results",
        {
            "results": results,
            "format_type": "markdown",
            "max_per_line": 100  # Can also limit at formatting time
        }
    )

    print(formatted)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
