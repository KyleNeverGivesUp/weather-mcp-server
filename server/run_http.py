#!/usr/bin/env python3
"""
HTTP Transport runner for Weather MCP Server
Use this for production deployment with SSE transport
"""
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

LOG_LEVEL = "INFO"

from server.server import mcp

# Configure JSON structured logging for HTTP mode
logging.basicConfig(
    level=LOG_LEVEL,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    stream=sys.stdout,
    force=True,
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting Weather MCP Server in HTTP mode...")
    logger.info("Transport: SSE (FastMCP built-in server)")
    logger.info("Health endpoint: http://0.0.0.0:8080/health")
    logger.info("MCP SSE endpoint: http://0.0.0.0:8080/sse")
    logger.info("MCP message endpoint: http://0.0.0.0:8080/messages/")

    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8080
    mcp.settings.log_level = LOG_LEVEL
    mcp.run(transport="sse")
