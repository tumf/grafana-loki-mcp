#!/usr/bin/env python3
"""
Script to move e2e test files to the e2e directory.
"""

import os
import shutil

# Define the source files and their destinations
files_to_move = [
    ("e2e_test.py", "e2e/e2e_test.py"),
    ("run_test.py", "e2e/run_test.py"),
    ("run_with_mcp_cli.py", "e2e/run_with_mcp_cli.py"),
    ("simple_client.py", "e2e/simple_client.py"),
    ("run_server.sh", "e2e/run_server.sh"),
    ("run_client.sh", "e2e/run_client.sh"),
    (".env", "e2e/.env"),
]

# Create the e2e directory if it doesn't exist
os.makedirs("e2e", exist_ok=True)

# Copy each file
for source, destination in files_to_move:
    if os.path.exists(source):
        print(f"Copying {source} to {destination}")
        shutil.copy2(source, destination)
    else:
        print(f"Warning: Source file {source} does not exist")

# Make shell scripts executable
for script in ["e2e/run_server.sh", "e2e/run_client.sh"]:
    if os.path.exists(script):
        print(f"Making {script} executable")
        os.chmod(script, 0o755)

print("Done moving e2e test files")
