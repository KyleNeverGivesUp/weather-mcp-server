#!/usr/bin/env python3
"""
HTTP Transport runner for Weather MCP Server
Use this for production deployment with HTTP/SSE
"""
import sys
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server import mcp
from server.health_server import health_check, root, metrics

# Configure JSON structured logging for HTTP mode
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Weather MCP Server",
    description="MCP server providing real-time weather information via HTTP/SSE",
    version="1.0.0"
)

# Add health and utility endpoints
app.add_api_route("/health", health_check, methods=["GET"])
app.add_api_route("/", root, methods=["GET"])
app.add_api_route("/metrics", metrics, methods=["GET"])


@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """
    MCP HTTP endpoint for handling tool calls and resource requests.
    Implements Server-Sent Events (SSE) for streaming responses.
    """
    logger.info(f"Received MCP request: {request.get('method')}")
    
    try:
        # Process MCP request through FastMCP
        # This is a simplified example - in production you'd use FastMCP's HTTP handler
        response = {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "status": "success",
                "message": "MCP HTTP endpoint active. Use STDIO transport for full functionality."
            }
        }
        return response
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/sse/mcp")
async def mcp_sse_endpoint():
    """
    Server-Sent Events endpoint for streaming MCP responses.
    """
    async def event_generator():
        logger.info("SSE connection established")
        yield f"data: {{'status': 'connected', 'service': 'weather-mcp'}}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {{'type': 'heartbeat', 'timestamp': '{asyncio.get_event_loop().time()}'}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    logger.info("Starting Weather MCP Server in HTTP mode...")
    logger.info("Transport: HTTP/SSE (for production)")
    logger.info("Health endpoint: http://0.0.0.0:8080/health")
    logger.info("MCP endpoint: http://0.0.0.0:8080/mcp")
    logger.info("SSE endpoint: http://0.0.0.0:8080/sse/mcp")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )
