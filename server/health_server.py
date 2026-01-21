"""
Health check endpoint and HTTP server for Weather MCP
Combines health checks with MCP server functionality
"""
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncio

# Configure logging for HTTP mode (JSON structured logging)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Weather MCP Server", version="1.0.0")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    Returns server status and basic metrics.
    """
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "weather-mcp-server",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/")
async def root():
    """
    Root endpoint with server information.
    """
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "description": "MCP server providing real-time weather information",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        },
        "mcp_tools": [
            "get_current_weather",
            "get_forecast",
            "get_weather_alerts"
        ],
        "mcp_resources": [
            "weather://cities/supported"
        ]
    }


@app.get("/metrics")
async def metrics():
    """
    Basic metrics endpoint for monitoring.
    """
    return {
        "server": "weather-mcp",
        "uptime": "available via container stats",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Weather MCP Health Server on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
