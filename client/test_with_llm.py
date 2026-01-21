#!/usr/bin/env python3
"""
Test Weather MCP Server with OpenRouter LLM
Uses a free LLM to interact with the MCP tools
"""
import asyncio
import json
import os
import sys
import shutil
import logging
from typing import Dict, Any, List
import httpx
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check if .env file exists, if not create from template
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')
env_example_path = os.path.join(project_root, 'env_example')
log_path = os.path.join(project_root, "server.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_path,
    filemode="a",
)
logger = logging.getLogger(__name__)

if not os.path.exists(dotenv_path):
    if os.path.exists(env_example_path):
        shutil.copy(env_example_path, dotenv_path)
        print(f"Created .env file from template: {dotenv_path}")
        print(f"Please edit .env and add your OPENROUTER_KEY")
        print(f"Get a free key from: https://openrouter.ai/keys")
        print()
    else:
        print(f"Error: Neither .env nor env_example found!")
        print(f"Please create a .env file with OPENROUTER_KEY")
        sys.exit(1)

# Load environment variables from .env file
load_dotenv(dotenv_path)

# OpenRouter configuration - read from .env, no defaults
OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
APP_NAME = os.getenv("APP_NAME")
APP_ORIGIN = os.getenv("APP_ORIGIN")

# Require API key for LLM mode
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "placeholder":
    print("Error: OPENROUTER_KEY not configured in .env file")
    print("Set OPENROUTER_KEY in .env to run LLM tests.")
    sys.exit(1)

# Import MCP tools
from server.server import (
    get_current_weather,
    get_forecast,
    get_weather_alerts,
    get_supported_cities,
    SUPPORTED_CITIES
)

# Define MCP tools for the LLM
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather for a specified city including temperature, conditions, humidity, and wind",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city (e.g., 'London', 'New York', 'Tokyo')"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Get weather forecast for a specified city for 1-7 days",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to forecast (1-7, default: 3)"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_alerts",
            "description": "Get active weather alerts and warnings for a specified city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supported_cities",
            "description": "Get the list of supported cities for weather queries",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute MCP tool and return result"""
    print(f"🔧 Calling tool: {tool_name}")
    print(f"   Arguments: {json.dumps(arguments, indent=2)}")
    
    try:
        if tool_name == "get_current_weather":
            result = await get_current_weather(arguments["city"])
        elif tool_name == "get_forecast":
            city = arguments["city"]
            days = arguments.get("days", 3)
            result = await get_forecast(city, days)
        elif tool_name == "get_weather_alerts":
            result = await get_weather_alerts(arguments["city"])
        elif tool_name == "get_supported_cities":
            result = get_supported_cities()
        else:
            result = f"Error: Unknown tool '{tool_name}'"
        
        print(f"Tool result received\n")
        return result
    except Exception as e:
        error_msg = f"Error executing tool: {str(e)}"
        print(f"{error_msg}\n")
        return error_msg


async def chat_with_llm(user_message: str, api_key: str = None) -> str:
    """
    Send message to OpenRouter LLM with tool calling capability
    """
    print(f"User: {user_message}\n")
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful weather assistant. You have access to weather tools. "
                "When users ask about weather, use the appropriate tools to get real-time data. "
                f"Supported cities: {', '.join(SUPPORTED_CITIES.keys())}. "
                "Always use tool calls to get weather data instead of making up information."
            )
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # Call OpenRouter API
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": APP_ORIGIN,
                    "X-Title": APP_NAME,
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": messages,
                    "tools": TOOLS_SCHEMA,
                    "tool_choice": "auto",
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Check if LLM wants to call a tool
            message = result["choices"][0]["message"]
            
            if message.get("tool_calls"):
                # LLM wants to use a tool
                tool_call = message["tool_calls"][0]
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                # Execute the tool
                tool_result = await call_tool(function_name, function_args)
                
                # Send tool result back to LLM
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })
                
                # Get final response
                response2 = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": APP_ORIGIN,
                        "X-Title": APP_NAME,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": messages,
                        "stream": False
                    }
                )
                response2.raise_for_status()
                final_result = response2.json()
                return final_result["choices"][0]["message"]["content"]
            else:
                # Direct response without tool
                return message["content"]
                
        except httpx.HTTPStatusError as e:
            response = e.response
            logger.error(
                "OpenRouter request failed: status=%s body=%s",
                response.status_code,
                response.text,
            )
            return f"Error calling OpenRouter API: {str(e)}"
        except httpx.HTTPError as e:
            logger.error("OpenRouter request failed: %s", e)
            return f"Error calling OpenRouter API: {str(e)}"


async def interactive_mode():
    """
    Interactive chat mode with the LLM
    """
    print("=" * 70)
    print("Weather MCP Server + OpenRouter LLM Test")
    print("=" * 70)
    print()
    print(f"Model: {OPENROUTER_MODEL}")
    print("API Key: Configured")
    print()
    print("Supported cities:", ", ".join(SUPPORTED_CITIES.keys()))
    print()
    print("Try asking:")
    print("  - What's the weather in London?")
    print("  - Give me a 5-day forecast for Tokyo")
    print("  - Are there any weather alerts in New York?")
    print("  - What cities do you support?")
    print()
    print("Type 'quit' or 'exit' to stop")
    print("=" * 70)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Get response from LLM
            response = await chat_with_llm(user_input, OPENROUTER_API_KEY)
            
            print(f"Assistant: {response}\n")
            print("-" * 70)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


async def run_single_query(query: str) -> None:
    """
    Run one LLM query
    """
    print("=" * 70)
    print("Weather MCP Server + LLM Single Query")
    print("=" * 70)
    print()
    print(f"Query: {query}")
    print()
    
    response = await chat_with_llm(query, OPENROUTER_API_KEY)
    print(f"Assistant: {response}\n")
    print("=" * 70)


async def main():
    """
    Main entry point
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_mode()
    else:
        # Select one query by uncommenting it.
        queries = [
            "What's the current weather in London?",
            "Give me a 3-day forecast for Tokyo",
            "Are there any weather alerts in New York?",
            "What cities are supported?"
        ]
        # selected_query = queries[0]
        # selected_query = queries[1]
        # selected_query = queries[2]
        selected_query = queries[3]
        
        await run_single_query(selected_query)
        
        print("\nRun 'python test_with_llm.py interactive' for interactive chat mode")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user")
