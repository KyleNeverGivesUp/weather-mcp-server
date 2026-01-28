# Weather MCP Server

MCP server providing real-time weather data from Open-Meteo API. Supports STDIO and SSE transports.

## Setup

```bash
brew install uv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Testing

### Direct Function Test
Test weather functions without MCP protocol:
```bash
python test-client/test-stdio.py
```

### STDIO Transport Test
Test via MCP STDIO protocol (auto-starts server):
```bash
python test-client/host-stdio.py
```

### SSE Transport Test
Start HTTP server:
```bash
python server/run_http.py
```

In another terminal, run SSE client:
```bash
python test-client/test-sse.py
```

Endpoints:
- SSE: `http://localhost:8080/sse`
- Messages: `http://localhost:8080/messages/`
- Health: `http://localhost:8080/health`

## MCP Tools

- `get_current_weather(city)` - Current weather conditions
- `get_forecast(city, days)` - Weather forecast (1-7 days)
- `get_weather_alerts(city)` - Weather alerts and warnings

## MCP Resource

- `weather://cities/supported` - List of supported cities

## Supported Cities

London, New York, Tokyo, Paris, Beijing, Toronto, Singapore

## Docker

```bash
docker compose up --build
```

Health check:
```bash
curl http://localhost:8080/health
```
