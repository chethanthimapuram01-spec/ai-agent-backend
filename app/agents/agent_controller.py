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
        direct_response: Optional[str] = None,
        query_type: Optional[str] = None,
        is_multi_step: bool = False
    ):
        self.use_tool = use_tool
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.reasoning = reasoning
        self.direct_response = direct_response
        self.query_type = query_type  # direct, document, api, multi-step
        self.is_multi_step = is_multi_step
        self.timestamp = datetime.utcnow().isoformat()


class QueryType:
    """Constants for query type classification"""
    DIRECT = "direct"
    DOCUMENT = "document"
    API = "api"
    MULTI_STEP = "multi-step"


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
            
            # Step 2: Check if this is a multi-step task
            if decision.is_multi_step and decision.use_tool:
                logger.info("Multi-step task detected - executing orchestrated workflow")
                result = await self._execute_multi_step(query, decision, session_id)
            # Step 3: Execute based on decision
            elif decision.use_tool:
                result = await self._execute_with_tool(query, decision, session_id)
            else:
                result = await self._execute_direct_response(query, decision, session_id)
            
            # Step 4: Record execution
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
        """Build prompt for LLM to make intelligent routing decision"""
        return f"""You are an intelligent routing agent. Analyze the user query and determine the best action.

User Query: "{query}"

Available Tools:
{tool_descriptions}

Query Classification Guidelines:
1. DIRECT RESPONSE - Simple questions that don't require external data or documents
   Examples: "What is AI?", "Explain machine learning", "Hello", "How are you?"
   
2. DOCUMENT QUESTION - Questions about uploaded documents or content
   Examples: "Summarize the contract", "What does the document say about pricing?", "Find information about deadlines in the uploaded files"
   Tool: document_query
   
3. API REQUEST - Questions requiring external API data
   Examples: "Get weather for London", "What's the Bitcoin price?", "Fetch user data"
   Tool: api_caller
   
4. MULTI-STEP TASK - Complex queries requiring multiple operations
   Examples: "Get weather and summarize it in a document", "Compare contract terms with weather impact", "Fetch data and analyze it"
   Note: For multi-step tasks, identify the FIRST tool to use

Response Format:
- Direct response: DIRECT: [your helpful response]
- Tool usage: TOOL: [tool_name] | PARAMS: {{"param1": "value1", "param2": "value2"}} | REASON: [brief explanation]

Important:
- Match tool parameters exactly to the tool's input schema
- For document queries, use tool "document_query" with parameter "query"
- For API calls, use tool "api_caller" with parameters "endpoint" and specific endpoint params
- Be precise with parameter names and values

Decision:"""
    
    def _parse_decision_response(
        self,
        response: str,
        available_tools: Dict[str, Any]
    ) -> AgentDecision:
        """Parse LLM decision response and classify query type"""
        response = response.strip()
        
        if response.startswith("DIRECT:"):
            # Direct response
            direct_response = response.replace("DIRECT:", "").strip()
            return AgentDecision(
                use_tool=False,
                direct_response=direct_response,
                reasoning="Query can be answered directly",
                query_type=QueryType.DIRECT
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
                        reasoning=f"Requested tool '{tool_name}' not available",
                        query_type=QueryType.DIRECT
                    )
                
                # Classify query type based on tool selection
                query_type = self._classify_query_type(tool_name, reasoning)
                
                # Check if multi-step based on reasoning keywords
                is_multi_step = self._is_multi_step_query(reasoning)
                
                return AgentDecision(
                    use_tool=True,
                    tool_name=tool_name,
                    tool_params=params,
                    reasoning=reasoning,
                    query_type=query_type,
                    is_multi_step=is_multi_step
                )
                
            except Exception as e:
                logger.warning(f"Error parsing tool decision: {str(e)}")
                return AgentDecision(
                    use_tool=False,
                    reasoning=f"Could not parse tool decision: {str(e)}",
                    query_type=QueryType.DIRECT
                )
        
        # Default to direct response
        return AgentDecision(
            use_tool=False,
            direct_response=response,
            reasoning="Default to direct response",
            query_type=QueryType.DIRECT
        )
    
    def _classify_query_type(self, tool_name: str, reasoning: str) -> str:
        """Classify query type based on tool selection"""
        if tool_name == "document_query":
            return QueryType.DOCUMENT
        elif tool_name == "api_caller":
            return QueryType.API
        else:
            return QueryType.DIRECT
    
    def _is_multi_step_query(self, reasoning: str) -> bool:
        """Determine if query requires multiple steps"""
        multi_step_keywords = [
            "multi-step", "multiple", "then", "after", "combine",
            "compare", "both", "and then", "followed by"
        ]
        reasoning_lower = reasoning.lower()
        return any(keyword in reasoning_lower for keyword in multi_step_keywords)
    
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
    
    async def _execute_multi_step(
        self,
        query: str,
        decision: AgentDecision,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute multi-step workflow
        
        This orchestrates complex queries that require multiple tool calls
        or a combination of tools and processing.
        """
        logger.info(f"Executing multi-step workflow for query: {query[:50]}...")
        
        steps_executed = []
        accumulated_context = {}
        
        try:
            # Step 1: Execute the first tool (already decided)
            logger.info(f"Step 1: Executing {decision.tool_name}")
            first_result = await self._execute_with_tool(query, decision, session_id)
            steps_executed.append({
                "step": 1,
                "tool": decision.tool_name,
                "success": first_result["success"],
                "result": first_result.get("tool_results")
            })
            
            if first_result.get("tool_results", {}).get("result"):
                accumulated_context["step1_result"] = first_result["tool_results"]["result"]
            
            # Step 2: Determine if additional steps are needed
            # For now, we'll synthesize the result with LLM using accumulated context
            synthesis_prompt = self._build_synthesis_prompt(
                query, 
                steps_executed, 
                accumulated_context
            )
            
            synthesis_response = await chat_service.process_message(
                message=synthesis_prompt,
                session_id=session_id
            )
            
            final_response = synthesis_response.get("reply", first_result["response"])
            
            return {
                "response": final_response,
                "decision": decision,
                "tool_results": {
                    "multi_step": True,
                    "steps": steps_executed,
                    "accumulated_context": accumulated_context
                },
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in multi-step execution: {str(e)}", exc_info=True)
            return {
                "response": f"Multi-step execution failed: {str(e)}",
                "decision": decision,
                "tool_results": {"steps": steps_executed, "error": str(e)},
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": False
            }
    
    def _build_synthesis_prompt(
        self,
        original_query: str,
        steps_executed: List[Dict[str, Any]],
        accumulated_context: Dict[str, Any]
    ) -> str:
        """Build prompt for synthesizing multi-step results"""
        context_str = json.dumps(accumulated_context, indent=2)
        
        return f"""You are helping to answer a complex multi-step query.

Original Query: "{original_query}"

Steps Executed and Results:
{json.dumps(steps_executed, indent=2)}

Accumulated Context:
{context_str}

Instructions:
- Synthesize the results from all steps into a coherent answer
- Address the original query completely
- Be clear and concise
- Cite specific data from the results

Final Answer:"""
    
    def _format_tool_response(
        self,
        query: str,
        decision: AgentDecision,
        tool_result: Dict[str, Any]
    ) -> str:
        """Format tool execution result into user-friendly response"""
        result_data = tool_result.get("result", {})
        
        # Format based on query type
        if decision.query_type == QueryType.DOCUMENT:
            return self._format_document_response(result_data)
        elif decision.query_type == QueryType.API:
            return self._format_api_response(result_data, decision.tool_name)
        else:
            # Generic formatting
            return (
                f"I used the '{decision.tool_name}' tool to help with your request.\n\n"
                f"Result: {json.dumps(result_data, indent=2)}"
            )
    
    def _format_document_response(self, result_data: Dict[str, Any]) -> str:
        """Format document query response"""
        answer = result_data.get("answer", "No answer generated")
        sources = result_data.get("sources", [])
        
        response = f"{answer}\n\n"
        
        if sources:
            response += "Sources:\n"
            for idx, source in enumerate(sources[:3], 1):  # Limit to top 3 sources
                filename = source.get("filename", "Unknown")
                preview = source.get("text_preview", "")
                response += f"{idx}. {filename}\n   \"{preview[:100]}...\"\n\n"
        
        return response.strip()
    
    def _format_api_response(self, result_data: Dict[str, Any], tool_name: str) -> str:
        """Format API response"""
        # Format API responses in a more readable way
        if isinstance(result_data, dict):
            formatted = json.dumps(result_data, indent=2)
            return f"API Response:\n```json\n{formatted}\n```"
        else:
            return f"API Response: {result_data}"
    
    def _log_decision(self, session_id: str, query: str, decision: AgentDecision):
        """Log agent decision with query type"""
        log_entry = {
            "timestamp": decision.timestamp,
            "session_id": session_id,
            "query": query[:100],
            "use_tool": decision.use_tool,
            "tool_name": decision.tool_name,
            "query_type": decision.query_type,
            "is_multi_step": decision.is_multi_step,
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
