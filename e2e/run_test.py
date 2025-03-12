#!/usr/bin/env python3
"""
E2E Test Runner for Grafana-Loki MCP Server

This script runs the server and client in sequence for e2e testing.
"""

import os
import subprocess
import sys
import time

# Get the absolute path to the parent directory
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    """Run the e2e test."""
    # Ensure we have the required packages
    print("Ensuring required packages are installed...")
    subprocess.run(
        ["uv", "pip", "install", "fastmcp", "mcp", "python-dotenv"], check=True
    )

    # Start the server in a separate process
    print("Starting the server...")
    server_script = os.path.join(PARENT_DIR, "grafana_loki_mcp", "server.py")
    server_process = subprocess.Popen(
        [sys.executable, server_script, "--transport", "stdio"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give the server a moment to start
    time.sleep(2)

    # Check if the server is running
    if server_process.poll() is not None:
        print("Server failed to start!")
        stdout, stderr = server_process.communicate()
        print("Server stdout:", stdout)
        print("Server stderr:", stderr)
        return 1

    try:
        # Run the e2e_test.py instead of client.py
        print("Running the e2e test...")
        e2e_test_script = os.path.join(os.path.dirname(__file__), "e2e_test.py")
        e2e_test_result = subprocess.run(
            [sys.executable, e2e_test_script],
            capture_output=True,
            text=True,
        )

        # Print e2e test output
        print("E2E test stdout:", e2e_test_result.stdout)
        if e2e_test_result.stderr:
            print("E2E test stderr:", e2e_test_result.stderr)

        # Return the e2e test's exit code
        return e2e_test_result.returncode
    finally:
        # Terminate the server
        print("Terminating the server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Server did not terminate gracefully, killing...")
            server_process.kill()

        # Print server output
        stdout, stderr = server_process.communicate()
        print("Server stdout:", stdout)
        print("Server stderr:", stderr)


if __name__ == "__main__":
    sys.exit(main())
