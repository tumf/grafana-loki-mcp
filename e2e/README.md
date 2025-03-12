# Grafana-Loki MCP E2E Tests

This directory contains end-to-end tests for the Grafana-Loki MCP server.

## Prerequisites

- Python 3.10 or higher
- `uv` package manager
- Grafana instance with Loki datasource

## Environment Setup

Create a `.env` file in this directory with the following variables:

```
GRAFANA_URL=http://your-grafana-url:port
GRAFANA_API_KEY=your-grafana-api-key
```

## Running the Tests

There are several ways to run the e2e tests:

### 1. Using the run_test.py script

This script starts the server and runs the client in sequence:

```bash
python run_test.py
```

### 2. Using the run_with_mcp_cli.py script

This script uses the MCP CLI to start the server and then runs the client:

```bash
python run_with_mcp_cli.py
```

### 3. Using the shell scripts

Start the server in one terminal:

```bash
./run_server.sh
```

Then run the client in another terminal:

```bash
./run_client.sh
```

### 4. Running the e2e_test.py directly

This runs a complete end-to-end test:

```bash
python e2e_test.py
```

### 5. Using the simple client

For basic connection testing:

```bash
python simple_client.py
```

## Test Output

The tests will output logs to the console showing the progress and results of each test case.
