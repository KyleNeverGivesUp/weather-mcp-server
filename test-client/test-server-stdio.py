#!/usr/bin/env python3
"""
Comprehensive Weather MCP Server Test
Tests all tools and cities
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server import (
    get_current_weather,
    get_forecast,
    get_weather_alerts,
    get_supported_cities,
    SUPPORTED_CITIES
)

async def test_current_weather():
    """Test current weather for multiple cities"""
    print("\n" + "=" * 70)
    print("TEST: Current Weather")
    print("=" * 70)
    
    cities = ["beijing", "tokyo", "london"]
    
    for city in cities:
        print(f"\n📍 {city.upper()}")
        print("-" * 70)
        result = await get_current_weather(city)
        print(result)

async def test_forecast():
    """Test weather forecast"""
    print("\n" + "=" * 70)
    print("TEST: Weather Forecast")
    print("=" * 70)
    
    print("\n📍 TOKYO (3 days)")
    print("-" * 70)
    result = await get_forecast("tokyo", 3)
    print(result)

async def test_alerts():
    """Test weather alerts"""
    print("\n" + "=" * 70)
    print("TEST: Weather Alerts")
    print("=" * 70)
    
    print("\n📍 NEW YORK")
    print("-" * 70)
    result = await get_weather_alerts("new york")
    print(result)

def test_supported_cities():
    """Test supported cities resource"""
    print("\n" + "=" * 70)
    print("TEST: Supported Cities")
    print("=" * 70)
    
    result = get_supported_cities()
    print(result)
    print(f"\nTotal cities: {len(SUPPORTED_CITIES)}")

async def main():
    print("Weather MCP Server - Comprehensive Test Suite")
    print("=" * 70)
    
    # Run all tests
    await test_current_weather()
    await test_forecast()
    await test_alerts()
    test_supported_cities()
    
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())