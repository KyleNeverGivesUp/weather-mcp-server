"""
Weather MCP Server using FastMCP
Provides real-time weather information using Open-Meteo API
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env if present
load_dotenv()

# Init FastMCP server
mcp = FastMCP("weather-server")

# Open-Meteo config (env-driven, no API key)
OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_TIMEOUT = float(os.getenv("OPEN_METEO_TIMEOUT", "30"))

SUPPORTED_CITIES = {
    "london": {"lat": 51.5074, "lon": -0.1278, "name": "London, UK"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, USA"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, Japan"},
    "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris, France"},
    "beijing": {"lat": 39.9042, "lon": 116.4074, "name": "Beijing, China"},
    "toronto": {"lat": 43.6532, "lon": -79.3832, "name": "Toronto, Canada"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "name": "Singapore"},
}

def get_city_coords(city: str) -> Optional[Dict[str, Any]]:
    """Get coordinates for a city"""
    city_lower = city.lower().strip()
    if city_lower in SUPPORTED_CITIES:
        return SUPPORTED_CITIES[city_lower]
    return None


async def fetch_weather_data(lat: float, lon: float, params: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch weather data from Open-Meteo API"""
    base_params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto"
    }
    base_params.update(params)
    
    async with httpx.AsyncClient(timeout=OPEN_METEO_TIMEOUT) as client:
        try:
            response = await client.get(OPEN_METEO_BASE_URL, params=base_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather data: {e}")
            raise Exception(f"Failed to fetch weather data: {str(e)}")


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Get current weather for a specified city.
    
    Args:
        city: Name of the city (e.g., "London", "New York", "Tokyo")
    
    Returns:
        Current weather information including temperature, conditions, humidity, and wind
    """
    logger.info(f"Fetching current weather for {city}")
    
    coords = get_city_coords(city)
    if not coords:
        supported = ", ".join(SUPPORTED_CITIES.keys())
        return f"Error: City '{city}' not supported. Supported cities: {supported}"
    
    try:
        # Request current weather parameters
        params = {
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m"
        }
        
        data = await fetch_weather_data(coords["lat"], coords["lon"], params)
        current = data.get("current", {})
        
        # Map weather codes to descriptions
        weather_code = current.get("weather_code", 0)
        condition = get_weather_condition(weather_code)
        
        result = f"""Current Weather for {coords['name']}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Temperature: {current.get('temperature_2m')}°C
Conditions: {condition}
Humidity: {current.get('relative_humidity_2m')}%
Wind: {current.get('wind_speed_10m')} km/h at {current.get('wind_direction_10m')}°
Time: {current.get('time')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching current weather: {e}")
        return f"Error fetching weather data: {str(e)}"


@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """
    Get weather forecast for a specified city.
    
    Args:
        city: Name of the city (e.g., "London", "New York", "Tokyo")
        days: Number of days to forecast (1-7, default: 3)
    
    Returns:
        Weather forecast for the specified number of days
    """
    logger.info(f"Fetching {days}-day forecast for {city}")
    
    # Validate days parameter
    if not isinstance(days, int) or days < 1 or days > 7:
        return "Error: 'days' parameter must be an integer between 1 and 7"
    
    coords = get_city_coords(city)
    if not coords:
        supported = ", ".join(SUPPORTED_CITIES.keys())
        return f"Error: City '{city}' not supported. Supported cities: {supported}"
    
    try:
        # Request daily forecast parameters
        params = {
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "forecast_days": days
        }
        
        data = await fetch_weather_data(coords["lat"], coords["lon"], params)
        daily = data.get("daily", {})
        
        result = [f"Weather Forecast for {coords['name']} ({days} days):"]
        result.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        times = daily.get("time", [])
        for i in range(min(days, len(times))):
            date = times[i]
            weather_code = daily.get("weather_code", [])[i]
            temp_max = daily.get("temperature_2m_max", [])[i]
            temp_min = daily.get("temperature_2m_min", [])[i]
            precipitation = daily.get("precipitation_sum", [])[i]
            wind_max = daily.get("wind_speed_10m_max", [])[i]
            
            condition = get_weather_condition(weather_code)
            
            result.append(f"\n{date}")
            result.append(f"   {condition}")
            result.append(f"   High: {temp_max} degree | Low: {temp_min} degree")
            result.append(f"   Precipitation: {precipitation} mm")
            result.append(f"   Max Wind: {wind_max} km/h")
        
        result.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error fetching forecast: {e}")
        return f"Error fetching forecast data: {str(e)}"


@mcp.tool()
async def get_weather_alerts(city: str) -> str:
    """
    Get active weather alerts and warnings for a specified city.
    
    Args:
        city: Name of the city (e.g., "London", "New York", "Tokyo")
    
    Returns:
        Active weather alerts and warnings, or notification if none exist
    """
    logger.info(f"Fetching weather alerts for {city}")
    
    coords = get_city_coords(city)
    if not coords:
        supported = ", ".join(SUPPORTED_CITIES.keys())
        return f"Error: City '{city}' not supported. Supported cities: {supported}"
    
    try:
        # Get current and forecast data to check for alert conditions
        params = {
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "forecast_days": 3
        }
        
        data = await fetch_weather_data(coords["lat"], coords["lon"], params)
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        alerts = []
        
        # Check for extreme temperature
        temp = current.get("temperature_2m", 0)
        if temp > 35:
            alerts.append(" HIGH TEMPERATURE WARNING: Extreme heat detected")
        elif temp < -10:
            alerts.append(" LOW TEMPERATURE WARNING: Extreme cold detected")
        
        # Check for high wind
        wind = current.get("wind_speed_10m", 0)
        if wind > 50:
            alerts.append(" HIGH WIND WARNING: Strong winds detected")
        
        # Check for heavy precipitation forecast
        precip = daily.get("precipitation_sum", [])
        if precip and any(p > 50 for p in precip[:3]):
            alerts.append(" HEAVY RAIN WARNING: Significant precipitation expected")
        
        # Check severe weather codes
        weather_code = current.get("weather_code", 0)
        if weather_code in [95, 96, 99]:  # Thunderstorm codes
            alerts.append(" THUNDERSTORM WARNING: Severe weather detected")
        
        result = [f"Weather Alerts for {coords['name']}:"]
        result.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if alerts:
            result.append("\n  ACTIVE ALERTS:")
            for alert in alerts:
                result.append(f"   • {alert}")
        else:
            result.append("\n No active weather alerts or warnings")
        
        result.append(f"\n Current Conditions:")
        result.append(f"   Temperature: {temp}°C")
        result.append(f"   Wind Speed: {wind} km/h")
        result.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        return f"Error fetching weather alerts: {str(e)}"


@mcp.resource("weather://cities/supported")
def get_supported_cities() -> str:
    """
    Returns the list of supported cities with their coordinates.
    
    Returns:
        Formatted list of all supported cities
    """
    logger.info("Fetching supported cities list")
    
    result = ["Supported Cities for Weather Queries:"]
    result.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    for city_key, info in sorted(SUPPORTED_CITIES.items()):
        result.append(f"\n {info['name']}")
        result.append(f"   Coordinates: {info['lat']}, {info['lon']}")
        result.append(f"   Query name: '{city_key}'")
    
    result.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    result.append(f"Total: {len(SUPPORTED_CITIES)} cities")
    
    return "\n".join(result)


def get_weather_condition(code: int) -> str:
    """
    Map Open-Meteo weather codes to human-readable conditions.
    
    WMO Weather interpretation codes (WW):
    https://open-meteo.com/en/docs
    """
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return conditions.get(code, f"Unknown ({code})")


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(_: Request) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "weather-mcp-server",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        },
    )

if __name__ == "__main__":
    # Run the MCP server
    logger.info("Starting Weather MCP Server...")
    mcp.run(transport="stdio")
