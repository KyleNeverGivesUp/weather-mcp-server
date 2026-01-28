#!/usr/bin/env python3

import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_sse():
    """Test Weather MCP Server over SSE transport"""
    
    logger.info("Connecting to Weather MCP Server via SSE...")
    
    async with sse_client("http://localhost:8080/sse") as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            logger.info("✅ Connected and initialized")
            
            # List available tools
            tools_response = await session.list_tools()
            logger.info(f"📋 Available tools:")
            for tool in tools_response.tools:
                logger.info(f"  - {tool.name}: {tool.description}")
            
            # List resources
            resources_response = await session.list_resources()
            logger.info(f"📚 Available resources:")
            for resource in resources_response.resources:
                logger.info(f"  - {resource.uri}: {resource.name}")
            
            # Test 1: Get current weather
            print("\n" + "="*60)
            print("TEST 1: Get Current Weather for Beijing")
            print("="*60)
            result = await session.call_tool(
                "get_current_weather",
                arguments={"city": "Beijing"}
            )
            print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
            
            # Test 2: Get forecast
            print("\n" + "="*60)
            print("TEST 2: Get 3-Day Forecast for Tokyo")
            print("="*60)
            result = await session.call_tool(
                "get_forecast",
                arguments={"city": "Tokyo", "days": 3}
            )
            print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
            
            # Test 3: Read resource
            print("\n" + "="*60)
            print("TEST 3: Read Supported Cities Resource")
            print("="*60)
            resource = await session.read_resource("weather://cities/supported")
            print(resource.contents[0].text)

if __name__ == "__main__":
    asyncio.run(test_sse())