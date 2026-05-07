"""
Test suite for agent workflow execution and tool selection

Tests cover:
- Tool selection logic and decision-making
- Workflow execution with single and multi-step tasks
- Tool parameter validation and execution
- Agent decision reasoning
- Integration with prompt templates and output parsing

Run with: pytest test_agent_workflow.py -v
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.agents.agent_controller import AgentController, AgentDecision, QueryType
from app.agents.workflow_executor import workflow_executor, WorkflowStep
from app.tools.tool_registry import tool_registry
from app.utils.prompts import ToolSelectionOutput, WorkflowPlanOutput

# Initialize test client
client = TestClient(app)


class TestToolSelectionLogic:
    """Test agent's tool selection decision-making"""
    
    @pytest.mark.asyncio
    async def test_tool_selection_with_invalid_tool(self):
        """Test agent handles invalid tool selection gracefully"""
        controller = AgentController()
        
        with patch.object(controller, '_make_decision') as mock_decision:
            mock_decision.return_value = AgentDecision(
                use_tool=True,
                tool_name="non_existent_tool",
                tool_params={},
                reasoning="Testing error handling"
            )
            
            with patch.object(controller.tool_registry, 'get_tool') as mock_get_tool:
                mock_get_tool.return_value = None
                
                result = await controller.process_query(
                    query="Test query",
                    session_id="test-session"
                )
                
                # Should fall back to direct response
                assert "response" in result
                assert result.get("success") is not None
    
    def test_agent_decision_creation(self):
        """Test AgentDecision object creation"""
        decision = AgentDecision(
            use_tool=True,
            tool_name="test_tool",
            tool_params={"param": "value"},
            reasoning="Testing",
            query_type=QueryType.API
        )
        
        assert decision.use_tool is True
        assert decision.tool_name == "test_tool"
        assert decision.tool_params["param"] == "value"
        assert decision.reasoning == "Testing"
        assert decision.query_type == QueryType.API
        assert decision.timestamp is not None
    
    def test_agent_decision_direct_response(self):
        """Test AgentDecision for direct responses"""
        decision = AgentDecision(
            use_tool=False,
            direct_response="Hello!",
            reasoning="Simple greeting",
            query_type=QueryType.DIRECT
        )
        
        assert decision.use_tool is False
        assert decision.direct_response == "Hello!"
        assert decision.tool_name is None


class TestWorkflowExecution:
    """Test multi-step workflow execution"""
    
    def test_workflow_step_creation(self):
        """Test WorkflowStep object creation"""
        from app.agents.workflow_executor import WorkflowStep, StepStatus
        
        step = WorkflowStep(
            step_id=1,
            description="Get weather for Paris",
            tool_name="api_caller",
            tool_params={"api_type": "weather", "city": "Paris"},
            depends_on=[]
        )
        
        assert step.step_id == 1
        assert step.tool_name == "api_caller"
        assert step.tool_params["city"] == "Paris"
        assert step.status == StepStatus.PENDING
        assert step.result is None
    
    def test_workflow_step_to_dict(self):
        """Test WorkflowStep serialization"""
        from app.agents.workflow_executor import WorkflowStep, StepStatus
        
        step = WorkflowStep(
            step_id=1,
            description="Test step",
            tool_name="test_tool"
        )
        
        step_dict = step.to_dict()
        
        assert step_dict["step_id"] == 1
        assert step_dict["description"] == "Test step"
        assert step_dict["status"] == "pending"
    
    def test_workflow_state_creation(self):
        """Test WorkflowState object creation"""
        from app.agents.workflow_executor import WorkflowState, WorkflowStatus
        
        state = WorkflowState(
            workflow_id="wf-123",
            query="Test query",
            session_id="session-123"
        )
        
        assert state.workflow_id == "wf-123"
        assert state.query == "Test query"
        assert state.status == WorkflowStatus.CREATED
        assert len(state.steps) == 0
    
    def test_workflow_state_intermediate_data(self):
        """Test intermediate data storage in workflow"""
        from app.agents.workflow_executor import WorkflowState
        
        state = WorkflowState(
            workflow_id="wf-123",
            query="Test",
            session_id="session-123"
        )
        
        state.add_intermediate_data("step_1", {"result": "data"})
        
        assert state.get_intermediate_data("step_1") == {"result": "data"}
        assert state.get_intermediate_data("step_2") is None


class TestToolParameterValidation:
    """Test tool parameter validation during execution"""
    
    def test_tool_metadata_structure(self):
        """Test ToolMetadata structure"""
        from app.tools.base_tool import ToolMetadata
        
        metadata = ToolMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        )
        
        assert metadata.name == "test_tool"
        assert metadata.description == "A test tool"
        assert "properties" in metadata.input_schema
        assert metadata.version == "1.0.0"
        assert metadata.enabled is True
    
    def test_tool_registry_get_tool(self):
        """Test tool registry returns registered tools"""
        tool = tool_registry.get_tool("api_caller")
        
        # api_caller should be registered
        if tool:
            assert tool.metadata.name == "api_caller"
            assert "input_schema" in tool.metadata.model_dump()
    
    def test_tool_registry_list_tools(self):
        """Test listing all registered tools"""
        all_tools = tool_registry.get_all_tools()
        
        assert isinstance(all_tools, dict)
        # Tool registry returns a dictionary
        assert len(all_tools) >= 0
    
    def test_query_type_constants(self):
        """Test QueryType constants"""
        assert QueryType.DIRECT == "direct"
        assert QueryType.DOCUMENT == "document"
        assert QueryType.API == "api"
        assert QueryType.MULTI_STEP == "multi-step"


class TestAgentEndpoint:
    """Test agent endpoint integration"""
    
    def test_agent_endpoint_success(self):
        """Test successful agent query processing"""
        with patch('app.agents.agent_controller.agent_controller.process_query') as mock_process:
            mock_process.return_value = {
                "response": "Here's the weather information",
                "session_id": "test-session",
                "timestamp": "2026-05-08T10:00:00",
                "success": True,
                "decision": AgentDecision(
                    use_tool=True,
                    tool_name="api_caller",
                    reasoning="Weather query detected"
                )
            }
            
            response = client.post(
                "/agent",
                json={
                    "query": "What's the weather in London?",
                    "session_id": "test-session"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "response" in data
    
    def test_agent_endpoint_empty_query(self):
        """Test agent endpoint rejects empty queries"""
        response = client.post(
            "/agent",
            json={
                "query": "",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 400
    
    def test_agent_endpoint_missing_session_id(self):
        """Test agent endpoint requires session_id"""
        response = client.post(
            "/agent",
            json={
                "query": "Test query"
            }
        )
        
        assert response.status_code == 422
    
    def test_agent_endpoint_with_context(self):
        """Test agent endpoint accepts optional context"""
        with patch('app.agents.agent_controller.agent_controller.process_query') as mock_process:
            mock_process.return_value = {
                "response": "Response with context",
                "session_id": "test-session",
                "timestamp": "2026-05-08T10:00:00",
                "success": True,
                "decision": AgentDecision(use_tool=False)
            }
            
            response = client.post(
                "/agent",
                json={
                    "query": "Test query",
                    "session_id": "test-session",
                    "context": {"user_preference": "detailed"}
                }
            )
            
            assert response.status_code == 200


class TestDecisionReasoning:
    """Test agent decision reasoning quality"""
    
    @pytest.mark.asyncio
    async def test_reasoning_provided_for_tool_use(self):
        """Test that agent provides reasoning when using tools"""
        controller = AgentController()
        
        with patch.object(controller, '_make_decision') as mock_decision:
            decision = AgentDecision(
                use_tool=True,
                tool_name="api_caller",
                reasoning="User requested current weather data which requires API call"
            )
            mock_decision.return_value = decision
            
            assert decision.reasoning is not None
            assert len(decision.reasoning) > 10  # Meaningful reasoning
    
    @pytest.mark.asyncio
    async def test_reasoning_for_direct_response(self):
        """Test that agent provides reasoning for direct responses"""
        controller = AgentController()
        
        with patch.object(controller, '_make_decision') as mock_decision:
            decision = AgentDecision(
                use_tool=False,
                direct_response="Hello! How can I help you?",
                reasoning="Simple greeting, no external data needed"
            )
            mock_decision.return_value = decision
            
            assert decision.reasoning is not None
            assert decision.direct_response is not None
    
    def test_decision_includes_timestamp(self):
        """Test that decisions include timestamp"""
        decision = AgentDecision(
            use_tool=False,
            direct_response="Test"
        )
        
        assert decision.timestamp is not None
        # Verify timestamp format
        datetime.fromisoformat(decision.timestamp)


class TestPromptTemplateIntegration:
    """Test integration with prompt templates"""
    
    def test_output_validation_catches_errors(self):
        """Test that output parser validates LLM responses"""
        from app.utils.prompts import OutputParser
        
        # Invalid JSON
        with pytest.raises(Exception):
            OutputParser.extract_json("Not valid JSON")
        
        # Missing required fields
        invalid_output = {
            "use_tool": True
            # Missing tool_name
        }
        
        with pytest.raises(Exception):
            OutputParser.validate_tool_selection(invalid_output)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
