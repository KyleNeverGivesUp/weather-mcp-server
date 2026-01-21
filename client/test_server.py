#!/usr/bin/env python3
"""
Test script for Weather MCP Server
Tests all tools and resources
"""
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.server import (
    get_current_weather,
    get_forecast,
    get_weather_alerts,
    get_supported_cities,
    SUPPORTED_CITIES
)


async def test_current_weather():
    """Test get_current_weather tool"""
    print("\n" + "=" * 60)
    print("TEST: get_current_weather")
    print("=" * 60)
    
    # Test valid city
    print("\n1. Testing with valid city (London)...")
    result = await get_current_weather("London")
    print(result)
    assert "London" in result, "City name should be in result"
    assert "Temperature" in result, "Temperature should be in result"
    print("✓ Valid city test passed")
    
    # Test invalid city
    print("\n2. Testing with invalid city...")
    result = await get_current_weather("InvalidCity123")
    print(result)
    assert "Error" in result or "not supported" in result, "Should return error"
    print("✓ Invalid city test passed")
    
    # Test case insensitivity
    print("\n3. Testing case insensitivity...")
    result = await get_current_weather("TOKYO")
    print(result[:200] + "...")
    assert "Tokyo" in result, "Should handle uppercase"
    print("✓ Case insensitivity test passed")


async def test_forecast():
    """Test get_forecast tool"""
    print("\n" + "=" * 60)
    print("TEST: get_forecast")
    print("=" * 60)
    
    # Test default days
    print("\n1. Testing with default days (3)...")
    result = await get_forecast("Paris")
    print(result[:300] + "...")
    assert "Paris" in result, "City name should be in result"
    assert "Forecast" in result, "Should contain forecast data"
    print("✓ Default days test passed")
    
    # Test custom days
    print("\n2. Testing with custom days (7)...")
    result = await get_forecast("Tokyo", days=7)
    print(result[:300] + "...")
    assert "7 days" in result, "Should show 7 days"
    print("✓ Custom days test passed")
    
    # Test invalid days (too high)
    print("\n3. Testing with invalid days (10)...")
    result = await get_forecast("Berlin", days=10)
    print(result)
    assert "Error" in result or "between 1 and 7" in result, "Should validate days"
    print("✓ Invalid days test passed")
    
    # Test invalid days (zero)
    print("\n4. Testing with zero days...")
    result = await get_forecast("Sydney", days=0)
    print(result)
    assert "Error" in result or "between 1 and 7" in result, "Should validate days"
    print("✓ Zero days test passed")


async def test_weather_alerts():
    """Test get_weather_alerts tool"""
    print("\n" + "=" * 60)
    print("TEST: get_weather_alerts")
    print("=" * 60)
    
    # Test valid city
    print("\n1. Testing with valid city (New York)...")
    result = await get_weather_alerts("New York")
    print(result)
    assert "New York" in result, "City name should be in result"
    assert "Alerts" in result or "alerts" in result, "Should contain alert info"
    print("✓ Valid city test passed")
    
    # Test another city
    print("\n2. Testing with another city (Singapore)...")
    result = await get_weather_alerts("Singapore")
    print(result[:300] + "...")
    assert "Singapore" in result, "City name should be in result"
    print("✓ Another city test passed")


def test_supported_cities():
    """Test get_supported_cities resource"""
    print("\n" + "=" * 60)
    print("TEST: get_supported_cities (Resource)")
    print("=" * 60)
    
    print("\n1. Testing supported cities resource...")
    result = get_supported_cities()
    print(result)
    assert "Supported Cities" in result, "Should have title"
    assert "London" in result, "Should list cities"
    assert len(SUPPORTED_CITIES) > 0, "Should have cities"
    print(f"✓ Resource test passed ({len(SUPPORTED_CITIES)} cities)")


async def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "WEATHER MCP SERVER TEST SUITE" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # Test all tools
        await test_current_weather()
        await test_forecast()
        await test_weather_alerts()
        test_supported_cities()
        
        # Summary
        print("\n" + "=" * 60)
        print(" ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\n✓ Tested {len(SUPPORTED_CITIES)} supported cities")
        print("✓ All tools working correctly")
        print("✓ Input validation working")
        print("✓ Error handling working")
        print("\n Weather MCP Server is ready to use!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting Weather MCP Server tests...")
    print("This will make real API calls to Open-Meteo")
    print("Make sure you have internet connectivity")
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
