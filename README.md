# Grafana-Loki MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that allows querying Loki logs from Grafana.

## Features

- Query Loki logs through Grafana API
- Get Loki labels and label values
- Format query results in different formats (text, JSON, markdown)
- Support for both stdio and SSE transport protocols

## Requirements

- Python 3.8+
- FastMCP
- Requests

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install fastmcp requests
```

## Usage

### Environment Variables

Set the following environment variables:

- `GRAFANA_URL`: URL of your Grafana instance
- `GRAFANA_API_KEY`: Grafana API key with appropriate permissions

### Command Line Arguments

You can also provide these values as command line arguments:

```bash
python server.py -u https://your-grafana-instance.com -k your-api-key
```

Additional options:
- `--transport`: Transport protocol to use (`stdio` or `sse`, default: `stdio`)

### Running the Server

```bash
# Using environment variables
export GRAFANA_URL=https://your-grafana-instance.com
export GRAFANA_API_KEY=your-api-key
python server.py

# Using command line arguments
python server.py -u https://your-grafana-instance.com -k your-api-key

# Using SSE transport
python server.py --transport sse
```

## Available Tools

### query_loki

Query Loki logs through Grafana.

Parameters:
- `query`: Loki query string
- `start`: Start time (ISO format, default: 1 hour ago)
- `end`: End time (ISO format, default: now)
- `limit`: Maximum number of log lines to return (default: 100)
- `direction`: Query direction ('forward' or 'backward', default: 'backward')

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

## Example Usage

```python
# Example client code
from mcp.client import Client

async with Client() as client:
    # Query Loki logs
    results = await client.call_tool(
        "query_loki",
        {
            "query": '{app="my-app"} |= "error"',
            "limit": 50
        }
    )
    
    # Format the results
    formatted = await client.call_tool(
        "format_loki_results",
        {
            "results": results,
            "format_type": "markdown"
        }
    )
    
    print(formatted)
```