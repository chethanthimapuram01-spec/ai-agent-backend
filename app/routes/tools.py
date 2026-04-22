"""Tools management endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.tools.tool_registry import tool_registry

router = APIRouter()


class ToolInfo(BaseModel):
    """Tool information schema"""
    name: str
    description: str
    version: str
    enabled: bool
    input_schema: Dict[str, Any]


@router.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """
    List all registered tools
    
    Returns:
        List of tool information
    """
    metadata_list = tool_registry.get_all_metadata()
    
    return [
        {
            "name": meta.name,
            "description": meta.description,
            "version": meta.version,
            "enabled": meta.enabled,
            "input_schema": meta.input_schema
        }
        for meta in metadata_list
    ]


@router.get("/tools/enabled", response_model=List[str])
async def list_enabled_tools():
    """
    List names of enabled tools
    
    Returns:
        List of enabled tool names
    """
    return tool_registry.list_enabled_tool_names()


@router.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool_info(tool_name: str):
    """
    Get information about a specific tool
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool information
    """
    metadata = tool_registry.get_tool_metadata(tool_name)
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return {
        "name": metadata.name,
        "description": metadata.description,
        "version": metadata.version,
        "enabled": metadata.enabled,
        "input_schema": metadata.input_schema
    }


@router.post("/tools/{tool_name}/enable")
async def enable_tool(tool_name: str):
    """
    Enable a tool
    
    Args:
        tool_name: Name of the tool to enable
        
    Returns:
        Success message
    """
    success = tool_registry.enable_tool(tool_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return {"message": f"Tool '{tool_name}' enabled successfully"}


@router.post("/tools/{tool_name}/disable")
async def disable_tool(tool_name: str):
    """
    Disable a tool
    
    Args:
        tool_name: Name of the tool to disable
        
    Returns:
        Success message
    """
    success = tool_registry.disable_tool(tool_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return {"message": f"Tool '{tool_name}' disabled successfully"}
