#!/usr/bin/env python3
"""
Simple Grafana-Loki MCP Client

A simplified client for basic connection testing.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Get the absolute path to the parent directory
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_test():
    """Run a simple connection test."""
    # Load environment variables from .env file
    load_dotenv()

    # Create server parameters
    server_script = os.path.join(PARENT_DIR, "server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script, "--transport", "stdio"],
        env=dict(os.environ),  # Convert _Environ to dict
    )

    logger.info("Connecting to server...")

    try:
        # Connect to the server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                logger.info("Connected to server successfully")

                # List available tools
                tools = await session.list_tools()
                logger.info(f"Tools type: {type(tools)}")

                # Print tools in a safe way
                if hasattr(tools, "__iter__"):
                    for i, tool in enumerate(tools):
                        logger.info(f"Tool {i}: {tool}")
                else:
                    logger.info(f"Tools: {tools}")

                # Test a simple query
                logger.info("Testing a simple Loki query...")
                query_result = await session.call_tool(
                    "query_loki",
                    arguments={
                        "query": '{app="nextjs"}',
                        "limit": 5
                    }
                )
                logger.info(f"Query result: {query_result}")

                return True
    except Exception as e:
        logger.error(f"Error during test: {e}")
        return False


async def main():
    """Run the simple test."""
    success = await run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())