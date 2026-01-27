"""Configuration for Weather MCP Server."""
from __future__ import annotations

import os
# from dotenv import load_dotenv

# Load environment variables from .env if present
# load_dotenv()

OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_API_KEY = os.getenv("OPEN_METEO_API_KEY")


def _parse_timeout(value: str | None, default: float) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


OPEN_METEO_TIMEOUT = _parse_timeout(os.getenv("OPEN_METEO_TIMEOUT"), 30.0)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
