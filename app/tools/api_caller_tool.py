"""API Caller Tool - Fetch data from external APIs"""
import httpx
from typing import Dict, Any, Optional
from app.tools.base_tool import BaseTool, ToolMetadata
import logging

logger = logging.getLogger(__name__)


class ApiCallerTool(BaseTool):
    """
    Tool for calling external REST APIs
    
    Supports multiple endpoints:
    - weather: Get weather data for a city
    - placeholder: Fetch data from JSONPlaceholder API
    - crypto: Get cryptocurrency prices
    """
    
    # API Endpoint configurations
    API_CONFIGS = {
        "weather": {
            "base_url": "https://wttr.in/{city}",
            "params": {"format": "j1"},
            "method": "GET",
            "description": "Get weather information for a city"
        },
        "placeholder": {
            "base_url": "https://jsonplaceholder.typicode.com/{resource}/{id}",
            "method": "GET",
            "description": "Fetch sample data from JSONPlaceholder API"
        },
        "crypto": {
            "base_url": "https://api.coingecko.com/api/v3/simple/price",
            "params": {"vs_currencies": "usd,eur"},
            "method": "GET",
            "description": "Get cryptocurrency prices"
        }
    }
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="api_caller",
            description="Calls external REST APIs to fetch data from various sources (weather, placeholder data, crypto prices)",
            input_schema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The API endpoint to call",
                        "enum": ["weather", "placeholder", "crypto"]
                    },
                    "city": {
                        "type": "string",
                        "description": "City name for weather endpoint (required for weather)"
                    },
                    "resource": {
                        "type": "string",
                        "description": "Resource type for placeholder endpoint (e.g., 'posts', 'users', 'comments')",
                        "enum": ["posts", "users", "comments", "albums", "todos"]
                    },
                    "id": {
                        "type": "string",
                        "description": "Resource ID for placeholder endpoint (optional)"
                    },
                    "crypto_id": {
                        "type": "string",
                        "description": "Cryptocurrency ID for crypto endpoint (e.g., 'bitcoin', 'ethereum')"
                    }
                },
                "required": ["endpoint"]
            },
            version="1.0.0",
            enabled=True
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute API call to external service
        
        Args:
            endpoint: API endpoint to call (weather, placeholder, crypto)
            city: City name (for weather endpoint)
            resource: Resource type (for placeholder endpoint)
            id: Resource ID (for placeholder endpoint)
            crypto_id: Cryptocurrency ID (for crypto endpoint)
            
        Returns:
            Normalized response with status and data
        """
        endpoint = kwargs.get("endpoint")
        
        try:
            # Validate endpoint-specific parameters
            validation_result = self._validate_endpoint_params(endpoint, kwargs)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "result": None,
                    "error": validation_result["error"]
                }
            
            # Call the appropriate API
            if endpoint == "weather":
                response_data = await self._call_weather_api(kwargs.get("city"))
            elif endpoint == "placeholder":
                response_data = await self._call_placeholder_api(
                    kwargs.get("resource", "posts"),
                    kwargs.get("id")
                )
            elif endpoint == "crypto":
                response_data = await self._call_crypto_api(kwargs.get("crypto_id", "bitcoin"))
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"Unknown endpoint: {endpoint}"
                }
            
            # Normalize output format
            return {
                "success": True,
                "result": {
                    "tool_name": "api_caller",
                    "status": "success",
                    "data": response_data
                },
                "error": None
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            return {
                "success": False,
                "result": {
                    "tool_name": "api_caller",
                    "status": "error",
                    "data": None
                },
                "error": f"HTTP request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "result": {
                    "tool_name": "api_caller",
                    "status": "error",
                    "data": None
                },
                "error": f"API call failed: {str(e)}"
            }
    
    def _validate_endpoint_params(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate endpoint-specific required parameters"""
        if endpoint == "weather":
            if not params.get("city"):
                return {"valid": False, "error": "Parameter 'city' is required for weather endpoint"}
        elif endpoint == "placeholder":
            if not params.get("resource"):
                return {"valid": False, "error": "Parameter 'resource' is required for placeholder endpoint"}
        elif endpoint == "crypto":
            if not params.get("crypto_id"):
                return {"valid": False, "error": "Parameter 'crypto_id' is required for crypto endpoint"}
        
        return {"valid": True, "error": None}
    
    async def _call_weather_api(self, city: str) -> Dict[str, Any]:
        """
        Call weather API (wttr.in)
        
        Args:
            city: Name of the city
            
        Returns:
            Weather data for the city
        """
        url = f"https://wttr.in/{city}"
        params = {"format": "j1"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract and normalize relevant weather data
            current = data.get("current_condition", [{}])[0]
            
            return {
                "location": city,
                "temperature_c": current.get("temp_C"),
                "temperature_f": current.get("temp_F"),
                "weather_description": current.get("weatherDesc", [{}])[0].get("value"),
                "humidity": current.get("humidity"),
                "feels_like_c": current.get("FeelsLikeC"),
                "feels_like_f": current.get("FeelsLikeF"),
                "wind_speed_kmph": current.get("windspeedKmph"),
                "pressure": current.get("pressure"),
                "visibility": current.get("visibility"),
                "uv_index": current.get("uvIndex")
            }
    
    async def _call_placeholder_api(self, resource: str, resource_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Call JSONPlaceholder API
        
        Args:
            resource: Type of resource (posts, users, comments, etc.)
            resource_id: Optional specific resource ID
            
        Returns:
            Data from JSONPlaceholder API
        """
        base_url = "https://jsonplaceholder.typicode.com"
        
        if resource_id:
            url = f"{base_url}/{resource}/{resource_id}"
        else:
            url = f"{base_url}/{resource}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Normalize response
            if isinstance(data, list):
                return {
                    "resource": resource,
                    "count": len(data),
                    "items": data[:5] if len(data) > 5 else data  # Limit to first 5 items
                }
            else:
                return {
                    "resource": resource,
                    "id": resource_id,
                    "data": data
                }
    
    async def _call_crypto_api(self, crypto_id: str) -> Dict[str, Any]:
        """
        Call CoinGecko API for cryptocurrency prices
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Cryptocurrency price data
        """
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": crypto_id,
            "vs_currencies": "usd,eur,inr",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if crypto_id not in data:
                return {
                    "cryptocurrency": crypto_id,
                    "error": "Cryptocurrency not found",
                    "available_ids_hint": "Try: bitcoin, ethereum, cardano, solana, dogecoin"
                }
            
            crypto_data = data[crypto_id]
            
            return {
                "cryptocurrency": crypto_id,
                "price_usd": crypto_data.get("usd"),
                "price_eur": crypto_data.get("eur"),
                "price_inr": crypto_data.get("inr"),
                "change_24h_usd": crypto_data.get("usd_24h_change"),
                "market_cap_usd": crypto_data.get("usd_market_cap")
            }
