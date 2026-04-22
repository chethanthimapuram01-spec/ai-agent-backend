"""Central registry for managing tools"""
from typing import Dict, Optional, List
from app.tools.base_tool import BaseTool, ToolMetadata
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Singleton registry for managing all available tools
    
    Provides centralized registration, retrieval, and management of tools
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools: Dict[str, BaseTool] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the registry"""
        if not self._initialized:
            self._initialized = True
            logger.info("ToolRegistry initialized")
    
    def register(self, tool: BaseTool) -> bool:
        """
        Register a new tool
        
        Args:
            tool: BaseTool instance to register
            
        Returns:
            True if registration successful, False if tool already exists
        """
        tool_name = tool.metadata.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered. Skipping.")
            return False
        
        self._tools[tool_name] = tool
        logger.info(f"Tool '{tool_name}' registered successfully")
        return True
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool by name
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if unregistered, False if tool not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Tool '{tool_name}' unregistered")
            return True
        
        logger.warning(f"Tool '{tool_name}' not found in registry")
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            BaseTool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools
        
        Returns:
            Dictionary of tool_name -> BaseTool
        """
        return self._tools.copy()
    
    def get_enabled_tools(self) -> Dict[str, BaseTool]:
        """
        Get all enabled tools
        
        Returns:
            Dictionary of enabled tools
        """
        return {
            name: tool 
            for name, tool in self._tools.items() 
            if tool.metadata.enabled
        }
    
    def list_tool_names(self) -> List[str]:
        """
        Get list of all registered tool names
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def list_enabled_tool_names(self) -> List[str]:
        """
        Get list of enabled tool names
        
        Returns:
            List of enabled tool names
        """
        return [
            name 
            for name, tool in self._tools.items() 
            if tool.metadata.enabled
        ]
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolMetadata or None if not found
        """
        tool = self._tools.get(tool_name)
        return tool.metadata if tool else None
    
    def get_all_metadata(self) -> List[ToolMetadata]:
        """
        Get metadata for all registered tools
        
        Returns:
            List of ToolMetadata objects
        """
        return [tool.metadata for tool in self._tools.values()]
    
    def enable_tool(self, tool_name: str) -> bool:
        """
        Enable a tool
        
        Args:
            tool_name: Name of the tool to enable
            
        Returns:
            True if enabled, False if not found
        """
        tool = self._tools.get(tool_name)
        if tool:
            tool.metadata.enabled = True
            logger.info(f"Tool '{tool_name}' enabled")
            return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """
        Disable a tool
        
        Args:
            tool_name: Name of the tool to disable
            
        Returns:
            True if disabled, False if not found
        """
        tool = self._tools.get(tool_name)
        if tool:
            tool.metadata.enabled = False
            logger.info(f"Tool '{tool_name}' disabled")
            return True
        return False
    
    def clear(self):
        """Clear all registered tools (useful for testing)"""
        self._tools.clear()
        logger.info("All tools cleared from registry")
    
    def tool_exists(self, tool_name: str) -> bool:
        """
        Check if a tool is registered
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tools


# Singleton instance
tool_registry = ToolRegistry()
