# Weather MCP Server

MCP server that provides real-time weather data from Open-Meteo. Supports both STDIO (local) and SSE (HTTP) transports. Includes Docker setup and a health endpoint for orchestration.

## Requirements
- Python 3.10+
- uv (optional, recommended) or pip

## Setup (uv)
```bash
brew install uv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Setup (pip)
```bash
python3 -m pip install -r requirements.txt
```

## Run (STDIO)
STDIO is meant for local development and Claude Desktop.
```bash
python server/run_stdio.py
```

## Run (SSE HTTP)
```bash
python server/run_http.py
```

Default endpoints:
- SSE: `http://localhost:8080/sse`
- Messages: `http://localhost:8080/messages/`
- Health: `http://localhost:8080/health`

## Docker
```bash
docker compose up --build
```

Health check:
```bash
curl http://localhost:8080/health
```

## MCP Tools
- `get_current_weather(city)`
- `get_forecast(city, days)` (days 1-7)
- `get_weather_alerts(city)`

## MCP Resource
- `weather://cities/supported`

## STDIO Test Example
This launches the server process and calls a tool over STDIO.
```bash
python - <<'PY'
import anyio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    params = StdioServerParameters(
        command="python",
        args=["server/run_stdio.py"],
        cwd=".",
    )
    async with stdio_client(params) as (read, write):
        session = ClientSession(read, write)
        await session.initialize()
        result = await session.call_tool("get_current_weather", {"city": "London"})
        print(result.content[0].text)

anyio.run(main)
PY
```

## SSE Test Example
```bash
python - <<'PY'
import anyio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    async with sse_client("http://localhost:8080/sse") as (read, write):
        session = ClientSession(read, write)
        await session.initialize()
        result = await session.call_tool("get_current_weather", {"city": "London"})
        print(result.content[0].text)

anyio.run(main)
PY
```

## Claude Desktop
Example config in `client/claude_desktop_config.json`.
