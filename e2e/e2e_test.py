#!/usr/bin/env python3
"""
Grafana-Loki MCP E2E Test

A complete end-to-end test for the Grafana-Loki MCP server.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

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


async def run_e2e_tests():
    """Run end-to-end tests for the Grafana-Loki MCP server."""
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

    # Track test results
    test_results = {}
    
    try:
        # Connect to the server using async with for proper context management
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

                # Run test: get_loki_labels
                test_results["get_loki_labels"] = await test_get_loki_labels(session)
                
                # Run test: get_loki_label_values
                test_results["get_loki_label_values"] = await test_get_loki_label_values(session)
                
                # Run test: query_loki
                test_results["query_loki"] = await test_query_loki(session)
                
                # Run test: format_loki_results
                test_results["format_loki_results"] = await test_format_loki_results(session)
                
                # Print summary
                logger.info("Test Summary:")
                for test_name, result in test_results.items():
                    status = "PASSED" if result else "FAILED"
                    logger.info(f"  {test_name}: {status}")
                
                # Overall result
                all_passed = all(test_results.values())
                logger.info(f"Overall result: {'PASSED' if all_passed else 'FAILED'}")
                
                return all_passed
    except Exception as e:
        logger.error(f"Error during tests: {e}")
        return False


async def test_get_loki_labels(session):
    """Test the get_loki_labels tool."""
    logger.info("Testing get_loki_labels tool...")
    try:
        result = await session.call_tool("get_loki_labels")
        logger.info(f"get_loki_labels result: {result}")
        return True
    except Exception as e:
        logger.error(f"Error testing get_loki_labels: {e}")
        return False


async def test_get_loki_label_values(session):
    """Test the get_loki_label_values tool."""
    logger.info("Testing get_loki_label_values tool...")
    try:
        # Use a sample label
        sample_label = "app"
        result = await session.call_tool("get_loki_label_values", arguments={"label": sample_label})
        logger.info(f"get_loki_label_values result for '{sample_label}': {result}")
        return True
    except Exception as e:
        logger.error(f"Error testing get_loki_label_values: {e}")
        return False


async def test_query_loki(session):
    """Test the query_loki tool."""
    logger.info("Testing query_loki tool...")
    try:
        # Use a sample query
        query = '{app="nextjs"}'
        result = await session.call_tool(
            "query_loki", 
            arguments={
                "query": query,
                "limit": 5
            }
        )
        logger.info(f"query_loki result for '{query}': {result}")
        return True
    except Exception as e:
        logger.error(f"Error testing query_loki: {e}")
        return False


async def test_format_loki_results(session):
    """Test the format_loki_results tool."""
    logger.info("Testing format_loki_results tool...")
    try:
        # First get some results to format
        query_result = await session.call_tool(
            "query_loki", 
            arguments={
                "query": '{app="nextjs"}',
                "limit": 5
            }
        )
        
        # Extract the content from the result
        content = None
        if hasattr(query_result, "content"):
            for item in query_result.content:
                if hasattr(item, "type") and item.type == "text" and hasattr(item, "text"):
                    try:
                        content = json.loads(item.text)
                        break
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON: {item.text}")
        
        if not content:
            logger.warning("No content to format")
            return False
        
        # Format the results
        format_result = await session.call_tool(
            "format_loki_results",
            arguments={
                "results": content,
                "format_type": "markdown"
            }
        )
        logger.info(f"format_loki_results result: {format_result}")
        return True
    except Exception as e:
        logger.error(f"Error testing format_loki_results: {e}")
        return False


async def main():
    """Run the e2e tests."""
    success = await run_e2e_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 