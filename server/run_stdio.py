#!/usr/bin/env python3
"""
STDIO Transport runner for Weather MCP Server
Use this for local development with Claude Desktop
"""
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server import mcp

# Configure logging to stderr (STDIO transport requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Weather MCP Server in STDIO mode...")
    logger.info("Transport: STDIO")
    
    try:
        # Run with STDIO transport
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
