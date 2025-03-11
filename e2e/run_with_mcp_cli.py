#!/usr/bin/env python3
"""
E2E Test Runner for Grafana-Loki MCP Server using MCP CLI

This script runs the server using MCP CLI and then runs the client for e2e testing.
"""

import json
import os
import subprocess
import sys
import tempfile
import time

# Get the absolute path to the parent directory
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    """Run the e2e test."""
    # Ensure we have the required packages
    print("Ensuring required packages are installed...")
    subprocess.run(["uv", "pip", "install", "fastmcp", "mcp[cli]", "python-dotenv"], check=True)
    
    # Create a temporary file for server info
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
        server_info_path = tmp.name
    
    try:
        # Start the server using MCP CLI
        print("Starting the server using MCP CLI...")
        server_script = os.path.join(PARENT_DIR, "server.py")
        server_process = subprocess.Popen(
            ["mcp", "serve", server_script, "--info-path", server_info_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Give the server a moment to start and write its info
        time.sleep(2)
        
        # Check if the server is running
        if server_process.poll() is not None:
            print("Server failed to start!")
            stdout, stderr = server_process.communicate()
            print("Server stdout:", stdout)
            print("Server stderr:", stderr)
            return 1
        
        # Read the server info
        server_info = None
        for _ in range(10):  # Try a few times in case the file is not written yet
            try:
                with open(server_info_path, 'r') as f:
                    server_info = json.load(f)
                if server_info:
                    break
            except (json.JSONDecodeError, FileNotFoundError):
                time.sleep(0.5)
        
        if not server_info:
            print("Failed to read server info!")
            return 1
        
        print(f"Server info: {server_info}")
        
        try:
            # Run the client with the server info
            print("Running the client...")
            client_script = os.path.join(PARENT_DIR, "client.py")
            client_env = os.environ.copy()
            client_env["MCP_SERVER_INFO"] = json.dumps(server_info)
            client_result = subprocess.run(
                [sys.executable, client_script],
                env=client_env,
                capture_output=True,
                text=True,
            )
            
            # Print client output
            print("Client stdout:", client_result.stdout)
            if client_result.stderr:
                print("Client stderr:", client_result.stderr)
            
            # Return the client's exit code
            return client_result.returncode
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
    finally:
        # Clean up the temporary file
        try:
            os.unlink(server_info_path)
        except (FileNotFoundError, PermissionError):
            pass

if __name__ == "__main__":
    sys.exit(main()) 