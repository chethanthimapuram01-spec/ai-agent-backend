"""Agent controller for managing agent execution flow"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.tools.tool_registry import tool_registry
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)


class AgentDecision:
    """Represents an agent's decision"""
    
    def __init__(
        self,
        use_tool: bool,
        tool_name: Optional[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        direct_response: Optional[str] = None
    ):
        self.use_tool = use_tool
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.reasoning = reasoning
        self.direct_response = direct_response
        self.timestamp = datetime.utcnow().isoformat()


class AgentController:
    """
    Controller for managing agent execution flow
    
    Orchestrates the decision-making process:
    1. Receive user query
    2. Analyze whether to use tools or respond directly
    3. Execute tools if needed
    4. Generate final response
    5. Log all decisions and actions
    """
    
    def __init__(self):
        """Initialize the agent controller"""
        self.tool_registry = tool_registry
        self.chat_service = chat_service
        self.execution_history: List[Dict[str, Any]] = []
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent workflow
        
        Args:
            query: User's input query
            session_id: Session identifier
            context: Optional context information
            
        Returns:
            Dictionary containing:
                - response: Final response to user
                - decision: AgentDecision object
                - tool_results: Results from tool execution (if any)
                - session_id: Session identifier
                - timestamp: Execution timestamp
        """
        logger.info(f"Processing query for session {session_id}: {query[:50]}...")
        
        try:
            # Step 1: Analyze query and decide on action
            decision = await self._make_decision(query, context)
            
            # Log the decision
            self._log_decision(session_id, query, decision)
            
            # Step 2: Execute based on decision
            if decision.use_tool:
                result = await self._execute_with_tool(query, decision, session_id)
            else:
                result = await self._execute_direct_response(query, decision, session_id)
            
            # Step 3: Record execution
            execution_record = {
                "session_id": session_id,
                "query": query,
                "decision": {
                    "use_tool": decision.use_tool,
                    "tool_name": decision.tool_name,
                    "reasoning": decision.reasoning
                },
                "response": result["response"],
                "timestamp": decision.timestamp,
                "success": result["success"]
            }
            self.execution_history.append(execution_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "response": f"An error occurred while processing your request: {str(e)}",
                "decision": None,
                "tool_results": None,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    async def _make_decision(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentDecision:
        """
        Analyze query and decide whether to use tools or respond directly
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            AgentDecision object
        """
        # Get available tools
        available_tools = self.tool_registry.get_enabled_tools()
        
        if not available_tools:
            # No tools available, respond directly
            logger.info("No tools available - will respond directly")
            return AgentDecision(
                use_tool=False,
                reasoning="No tools are currently available"
            )
        
        # Build decision prompt with tool information
        tool_descriptions = self._build_tool_descriptions(available_tools)
        decision_prompt = self._build_decision_prompt(query, tool_descriptions)
        
        # Use LLM to make decision
        try:
            llm_response = await chat_service.process_message(
                message=decision_prompt,
                session_id="agent_decision"
            )
            
            # Parse LLM response to extract decision
            decision = self._parse_decision_response(llm_response["reply"], available_tools)
            
            logger.info(
                f"Decision made - Use tool: {decision.use_tool}, "
                f"Tool: {decision.tool_name if decision.use_tool else 'N/A'}"
            )
            
            return decision
            
        except Exception as e:
            logger.warning(f"Error in decision making: {str(e)}. Defaulting to direct response.")
            return AgentDecision(
                use_tool=False,
                reasoning=f"Error in decision process: {str(e)}"
            )
    
    def _build_tool_descriptions(self, tools: Dict[str, Any]) -> str:
        """Build formatted description of available tools"""
        descriptions = []
        for name, tool in tools.items():
            metadata = tool.metadata
            descriptions.append(
                f"- {metadata.name}: {metadata.description}\n"
                f"  Input: {json.dumps(metadata.input_schema.get('properties', {}), indent=2)}"
            )
        return "\n".join(descriptions)
    
    def _build_decision_prompt(self, query: str, tool_descriptions: str) -> str:
        """Build prompt for LLM to make decision"""
        return f"""Analyze the following user query and decide whether to use a tool or respond directly.

User Query: {query}

Available Tools:
{tool_descriptions}

Instructions:
1. If the query can be answered directly without tools, respond with: DIRECT: [your response]
2. If a tool should be used, respond with: TOOL: [tool_name] | PARAMS: {{"param": "value"}} | REASON: [why this tool]

Decision:"""
    
    def _parse_decision_response(
        self,
        response: str,
        available_tools: Dict[str, Any]
    ) -> AgentDecision:
        """Parse LLM decision response"""
        response = response.strip()
        
        if response.startswith("DIRECT:"):
            # Direct response
            direct_response = response.replace("DIRECT:", "").strip()
            return AgentDecision(
                use_tool=False,
                direct_response=direct_response,
                reasoning="Query can be answered directly"
            )
        
        elif response.startswith("TOOL:"):
            # Tool usage
            try:
                parts = response.replace("TOOL:", "").split("|")
                tool_name = parts[0].strip()
                
                # Extract parameters
                params = {}
                if len(parts) > 1 and "PARAMS:" in parts[1]:
                    params_str = parts[1].split("PARAMS:")[1].strip()
                    params = json.loads(params_str)
                
                # Extract reasoning
                reasoning = "Tool selected by agent"
                if len(parts) > 2 and "REASON:" in parts[2]:
                    reasoning = parts[2].split("REASON:")[1].strip()
                
                # Validate tool exists
                if tool_name not in available_tools:
                    logger.warning(f"Tool '{tool_name}' not found. Using direct response.")
                    return AgentDecision(
                        use_tool=False,
                        reasoning=f"Requested tool '{tool_name}' not available"
                    )
                
                return AgentDecision(
                    use_tool=True,
                    tool_name=tool_name,
                    tool_params=params,
                    reasoning=reasoning
                )
                
            except Exception as e:
                logger.warning(f"Error parsing tool decision: {str(e)}")
                return AgentDecision(
                    use_tool=False,
                    reasoning=f"Could not parse tool decision: {str(e)}"
                )
        
        # Default to direct response
        return AgentDecision(
            use_tool=False,
            direct_response=response,
            reasoning="Default to direct response"
        )
    
    async def _execute_with_tool(
        self,
        query: str,
        decision: AgentDecision,
        session_id: str
    ) -> Dict[str, Any]:
        """Execute query using a tool"""
        logger.info(f"Executing with tool: {decision.tool_name}")
        
        tool = self.tool_registry.get_tool(decision.tool_name)
        if not tool:
            return {
                "response": f"Tool '{decision.tool_name}' is not available.",
                "decision": decision,
                "tool_results": None,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False
            }
        
        # Execute tool
        tool_result = await tool.safe_execute(**decision.tool_params)
        
        # Generate response based on tool result
        if tool_result["success"]:
            response = self._format_tool_response(query, decision, tool_result)
        else:
            response = f"Tool execution failed: {tool_result.get('error', 'Unknown error')}"
        
        return {
            "response": response,
            "decision": decision,
            "tool_results": tool_result,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": tool_result["success"]
        }
    
    async def _execute_direct_response(
        self,
        query: str,
        decision: AgentDecision,
        session_id: str
    ) -> Dict[str, Any]:
        """Execute query with direct LLM response"""
        logger.info("Executing with direct response")
        
        # Use pre-determined response or get fresh one from LLM
        if decision.direct_response:
            response = decision.direct_response
        else:
            llm_result = await chat_service.process_message(query, session_id)
            response = llm_result["reply"]
        
        return {
            "response": response,
            "decision": decision,
            "tool_results": None,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }
    
    def _format_tool_response(
        self,
        query: str,
        decision: AgentDecision,
        tool_result: Dict[str, Any]
    ) -> str:
        """Format tool execution result into user-friendly response"""
        result_data = tool_result.get("result", {})
        
        # Basic formatting - can be enhanced with LLM
        return (
            f"I used the '{decision.tool_name}' tool to help with your request.\n\n"
            f"Result: {json.dumps(result_data, indent=2)}"
        )
    
    def _log_decision(self, session_id: str, query: str, decision: AgentDecision):
        """Log agent decision"""
        log_entry = {
            "timestamp": decision.timestamp,
            "session_id": session_id,
            "query": query[:100],
            "use_tool": decision.use_tool,
            "tool_name": decision.tool_name,
            "reasoning": decision.reasoning
        }
        logger.info(f"Agent Decision: {json.dumps(log_entry, indent=2)}")
    
    def get_execution_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            session_id: Optional filter by session
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        history = self.execution_history
        
        if session_id:
            history = [h for h in history if h["session_id"] == session_id]
        
        return history[-limit:]


# Singleton instance
agent_controller = AgentController()
