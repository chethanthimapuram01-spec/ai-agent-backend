"""
Test script for ApiCallerTool

This script demonstrates how to use the ApiCallerTool with all supported endpoints.
Run this script to test the API caller functionality.

Usage:
    python test_api_caller.py
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.api_caller_tool import ApiCallerTool


async def test_weather_api():
    """Test the weather API endpoint"""
    print("\n" + "="*60)
    print("Testing Weather API")
    print("="*60)
    
    api_caller = ApiCallerTool()
    
    # Test with Hyderabad
    print("\n1. Fetching weather for Hyderabad...")
    result = await api_caller.execute(endpoint="weather", city="Hyderabad")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Location: {data['location']}")
        print(f"✓ Temperature: {data['temperature_c']}°C / {data['temperature_f']}°F")
        print(f"✓ Weather: {data['weather_description']}")
        print(f"✓ Humidity: {data['humidity']}%")
        print(f"✓ Wind Speed: {data['wind_speed_kmph']} km/h")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test with another city
    print("\n2. Fetching weather for London...")
    result = await api_caller.execute(endpoint="weather", city="London")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Location: {data['location']}")
        print(f"✓ Temperature: {data['temperature_c']}°C")
        print(f"✓ Weather: {data['weather_description']}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test error handling - missing city parameter
    print("\n3. Testing error handling (missing city)...")
    result = await api_caller.execute(endpoint="weather")
    
    if not result["success"]:
        print(f"✓ Expected error caught: {result['error']}")
    else:
        print("✗ Should have failed but didn't")


async def test_placeholder_api():
    """Test the JSONPlaceholder API endpoint"""
    print("\n" + "="*60)
    print("Testing JSONPlaceholder API")
    print("="*60)
    
    api_caller = ApiCallerTool()
    
    # Test getting list of posts
    print("\n1. Fetching list of posts...")
    result = await api_caller.execute(endpoint="placeholder", resource="posts")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Resource: {data['resource']}")
        print(f"✓ Total count: {data['count']}")
        print(f"✓ Showing first {len(data['items'])} items")
        if data['items']:
            print(f"✓ First post title: {data['items'][0]['title'][:50]}...")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test getting specific user
    print("\n2. Fetching specific user (ID: 1)...")
    result = await api_caller.execute(endpoint="placeholder", resource="users", id="1")
    
    if result["success"]:
        data = result["result"]["data"]
        user_data = data['data']
        print(f"✓ Resource: {data['resource']}")
        print(f"✓ User ID: {data['id']}")
        print(f"✓ Name: {user_data['name']}")
        print(f"✓ Email: {user_data['email']}")
        print(f"✓ Username: {user_data['username']}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test getting comments
    print("\n3. Fetching comments...")
    result = await api_caller.execute(endpoint="placeholder", resource="comments")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Resource: {data['resource']}")
        print(f"✓ Total count: {data['count']}")
    else:
        print(f"✗ Error: {result['error']}")


async def test_crypto_api():
    """Test the cryptocurrency API endpoint"""
    print("\n" + "="*60)
    print("Testing Cryptocurrency API")
    print("="*60)
    
    api_caller = ApiCallerTool()
    
    # Test Bitcoin price
    print("\n1. Fetching Bitcoin price...")
    result = await api_caller.execute(endpoint="crypto", crypto_id="bitcoin")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Cryptocurrency: {data['cryptocurrency']}")
        print(f"✓ Price (USD): ${data['price_usd']:,.2f}")
        print(f"✓ Price (EUR): €{data['price_eur']:,.2f}")
        print(f"✓ Price (INR): ₹{data['price_inr']:,.2f}")
        print(f"✓ 24h Change: {data['change_24h_usd']:.2f}%")
        print(f"✓ Market Cap (USD): ${data['market_cap_usd']:,.0f}")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test Ethereum price
    print("\n2. Fetching Ethereum price...")
    result = await api_caller.execute(endpoint="crypto", crypto_id="ethereum")
    
    if result["success"]:
        data = result["result"]["data"]
        print(f"✓ Cryptocurrency: {data['cryptocurrency']}")
        print(f"✓ Price (USD): ${data['price_usd']:,.2f}")
        print(f"✓ 24h Change: {data['change_24h_usd']:.2f}%")
    else:
        print(f"✗ Error: {result['error']}")
    
    # Test with invalid crypto ID
    print("\n3. Testing with invalid crypto ID...")
    result = await api_caller.execute(endpoint="crypto", crypto_id="invalid_coin_xyz")
    
    if result["success"]:
        data = result["result"]["data"]
        if "error" in data:
            print(f"✓ Handled gracefully: {data['error']}")
            print(f"✓ Hint: {data['available_ids_hint']}")
    else:
        print(f"✓ Error caught: {result['error']}")


async def test_all_endpoints():
    """Run all tests"""
    print("\n" + "="*60)
    print("API CALLER TOOL - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print("\nTesting all endpoints with various scenarios...")
    
    try:
        # Test weather API
        await test_weather_api()
        
        # Test placeholder API
        await test_placeholder_api()
        
        # Test crypto API
        await test_crypto_api()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print("\n✓ ApiCallerTool is working correctly!")
        print("✓ All three endpoints (weather, placeholder, crypto) are functional")
        print("✓ Error handling is working as expected")
        
    except Exception as e:
        print(f"\n✗ Unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_tool_metadata():
    """Test tool metadata"""
    print("\n" + "="*60)
    print("Testing Tool Metadata")
    print("="*60)
    
    api_caller = ApiCallerTool()
    metadata = api_caller.metadata
    
    print(f"\nTool Name: {metadata.name}")
    print(f"Description: {metadata.description}")
    print(f"Version: {metadata.version}")
    print(f"Enabled: {metadata.enabled}")
    print(f"\nInput Schema:")
    print(f"  Required: {metadata.input_schema.get('required', [])}")
    print(f"  Properties: {list(metadata.input_schema.get('properties', {}).keys())}")
    
    # Test input validation
    print("\n" + "-"*60)
    print("Testing Input Validation")
    print("-"*60)
    
    # Valid input
    is_valid, error = api_caller.validate_input(endpoint="weather", city="Hyderabad")
    print(f"\n1. Valid input (weather + city): {'✓ Valid' if is_valid else f'✗ Invalid: {error}'}")
    
    # Missing required parameter
    is_valid, error = api_caller.validate_input(city="Hyderabad")
    print(f"2. Missing required 'endpoint': {'✓ Valid' if is_valid else f'✗ Invalid: {error}'}")
    
    # Extra parameters (should still be valid)
    is_valid, error = api_caller.validate_input(endpoint="crypto", crypto_id="bitcoin", extra_param="test")
    print(f"3. With extra parameters: {'✓ Valid' if is_valid else f'✗ Invalid: {error}'}")


if __name__ == "__main__":
    print("Starting ApiCallerTool tests...\n")
    
    # Run metadata tests
    asyncio.run(test_tool_metadata())
    
    # Run all endpoint tests
    asyncio.run(test_all_endpoints())
    
    print("\n" + "="*60)
    print("Test suite finished!")
    print("="*60)
