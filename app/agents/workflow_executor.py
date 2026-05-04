"""Workflow execution engine for multi-step tasks"""
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from pydantic import ValidationError
from app.tools.tool_registry import tool_registry
from app.services.chat_service import chat_service
from app.services.trace_logger import trace_logger, WorkflowTrace, TraceStatus
from app.utils.prompts import (
    PromptTemplates,
    OutputParser,
    WorkflowPlanOutput,
    FinalAnswerOutput
)

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Overall workflow status"""
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: int
    description: str
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    depends_on: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        return data


@dataclass
class WorkflowState:
    """Tracks the state of a workflow execution"""
    workflow_id: str
    query: str
    session_id: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    steps: List[WorkflowStep] = field(default_factory=list)
    intermediate_data: Dict[str, Any] = field(default_factory=dict)
    final_result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "query": self.query,
            "session_id": self.session_id,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "intermediate_data": self.intermediate_data,
            "final_result": self.final_result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
    
    def get_step(self, step_id: int) -> Optional[WorkflowStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def add_intermediate_data(self, key: str, value: Any):
        """Store intermediate data from a step"""
        self.intermediate_data[key] = value
        logger.info(f"Stored intermediate data: {key}")
    
    def get_intermediate_data(self, key: str) -> Optional[Any]:
        """Retrieve intermediate data"""
        return self.intermediate_data.get(key)


class WorkflowExecutor:
    """
    Workflow execution engine for orchestrating multi-step tasks
    
    Handles:
    1. Task analysis
    2. Workflow planning
    3. Sequential step execution
    4. Intermediate data storage and passing
    5. Final result synthesis
    6. Comprehensive logging
    """
    
    def __init__(self):
        """Initialize the workflow executor"""
        self.tool_registry = tool_registry
        self.chat_service = chat_service
        self.workflows: Dict[str, WorkflowState] = {}
        self._workflow_counter = 0
    
    async def execute_workflow(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a multi-step workflow
        
        Args:
            query: User's complex query
            session_id: Session identifier
            context: Optional context information
            
        Returns:
            Dictionary with workflow results and state
        """
        # Create workflow ID
        self._workflow_counter += 1
        workflow_id = f"workflow_{session_id}_{self._workflow_counter}_{datetime.utcnow().timestamp()}"
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        logger.info(f"Query: {query}")
        
        # Initialize workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            query=query,
            session_id=session_id
        )
        self.workflows[workflow_id] = workflow_state
        
        try:
            # Step 1: Analyze task
            workflow_state.status = WorkflowStatus.PLANNING
            await self._analyze_task(workflow_state, context)
            
            # Step 2: Create execution plan
            await self._create_plan(workflow_state)
            
            # Step 3: Execute workflow steps
            workflow_state.status = WorkflowStatus.EXECUTING
            workflow_state.started_at = datetime.utcnow().isoformat()
            await self._execute_steps(workflow_state)
            
            # Step 4: Generate final answer
            await self._generate_final_answer(workflow_state)
            
            # Mark as completed
            workflow_state.status = WorkflowStatus.COMPLETED
            workflow_state.completed_at = datetime.utcnow().isoformat()
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "response": workflow_state.final_result,
                "workflow_state": workflow_state.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}", exc_info=True)
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error = str(e)
            workflow_state.completed_at = datetime.utcnow().isoformat()
            
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_state": workflow_state.to_dict()
            }
    
    async def _analyze_task(
        self,
        workflow_state: WorkflowState,
        context: Optional[Dict[str, Any]]
    ):
        """Analyze the task to understand requirements"""
        logger.info(f"Analyzing task for workflow {workflow_state.workflow_id}")
        
        # Get available tools
        available_tools = self.tool_registry.get_enabled_tools()
        tool_descriptions = self._build_tool_descriptions(available_tools)
        
        # Analyze the query
        analysis_prompt = f"""Analyze this complex query and identify what needs to be done.

Query: "{workflow_state.query}"

Available Tools:
{tool_descriptions}

Provide a brief analysis of:
1. What is the user asking for?
2. What data or information is needed?
3. What tools or operations are required?
4. Are there dependencies between steps?

Analysis:"""
        
        analysis_response = await chat_service.process_message(
            message=analysis_prompt,
            session_id=f"{workflow_state.session_id}_analysis"
        )
        
        # Store analysis
        workflow_state.add_intermediate_data("task_analysis", analysis_response.get("reply", ""))
        logger.info(f"Task analysis completed: {analysis_response.get('reply', '')[:100]}...")
    
    async def _create_plan(self, workflow_state: WorkflowState):
        """Create a step-by-step execution plan using structured prompts"""
        logger.info(f"Creating execution plan for workflow {workflow_state.workflow_id}")
        
        available_tools = self.tool_registry.get_enabled_tools()
        tool_names = list(available_tools.keys())
        task_analysis = workflow_state.get_intermediate_data("task_analysis")
        
        # Use structured prompt template
        planning_prompt = PromptTemplates.get_workflow_planning_prompt(
            query=workflow_state.query,
            available_tools=tool_names,
            context=task_analysis
        )
        
        plan_response = await chat_service.process_message(
            message=planning_prompt,
            session_id=f"{workflow_state.session_id}_planning"
        )
        
        # Parse and validate the plan using Pydantic
        try:
            validated_plan = OutputParser.validate_workflow_plan(plan_response.get("reply", ""))
            
            # Store plan metadata
            workflow_state.add_intermediate_data("execution_plan", {
                "task_analysis": validated_plan.task_analysis,
                "required_capabilities": validated_plan.required_capabilities,
                "expected_challenges": validated_plan.expected_challenges,
                "success_criteria": validated_plan.success_criteria
            })
            
            # Convert validated steps to WorkflowStep objects
            steps = self._convert_to_workflow_steps(validated_plan.steps)
            workflow_state.steps = steps
            
            logger.info(f"Created plan with {len(steps)} steps")
            for step in steps:
                logger.info(f"  Step {step.step_id}: {step.description} (Tool: {step.tool_name})")
                
        except (ValidationError, ValueError) as e:
            logger.warning(f"Plan validation failed: {e}. Using fallback parser.")
            # Fallback to legacy parsing
            plan_text = plan_response.get("reply", "")
            workflow_state.add_intermediate_data("execution_plan", plan_text)
            steps = self._parse_plan(plan_text)
            workflow_state.steps = steps
            logger.info(f"Created plan with {len(steps)} steps (using fallback parser)")
    
    def _convert_to_workflow_steps(self, steps_data: List[Dict[str, Any]]) -> List[WorkflowStep]:
        """
        Convert validated plan steps to WorkflowStep objects
        
        Args:
            steps_data: List of step dictionaries from validated plan
            
        Returns:
            List of WorkflowStep objects
        """
        workflow_steps = []
        
        for step_data in steps_data:
            workflow_step = WorkflowStep(
                step_id=step_data.get("step_id", len(workflow_steps) + 1),
                description=step_data.get("description", "Unnamed step"),
                tool_name=step_data.get("tool_name"),
                tool_params=step_data.get("tool_params", {}),
                depends_on=step_data.get("depends_on", [])
            )
            workflow_steps.append(workflow_step)
        
        return workflow_steps
    
    def _parse_plan(self, plan_text: str) -> List[WorkflowStep]:
        """Parse plan text into WorkflowStep objects"""
        steps = []
        
        try:
            # Try to extract JSON from the response
            # Look for JSON block
            if "```json" in plan_text:
                json_start = plan_text.find("```json") + 7
                json_end = plan_text.find("```", json_start)
                json_text = plan_text[json_start:json_end].strip()
            elif "{" in plan_text and "}" in plan_text:
                json_start = plan_text.find("{")
                json_end = plan_text.rfind("}") + 1
                json_text = plan_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in plan")
            
            plan_data = json.loads(json_text)
            
            for step_data in plan_data.get("steps", []):
                step = WorkflowStep(
                    step_id=step_data.get("step_id", len(steps) + 1),
                    description=step_data.get("description", ""),
                    tool_name=step_data.get("tool_name"),
                    tool_params=step_data.get("tool_params", {}),
                    depends_on=step_data.get("depends_on", [])
                )
                steps.append(step)
                
        except Exception as e:
            logger.warning(f"Could not parse structured plan: {str(e)}. Creating default plan.")
            # Create a simple default plan
            steps = [
                WorkflowStep(
                    step_id=1,
                    description="Execute task",
                    tool_name=None,
                    tool_params={}
                )
            ]
        
        return steps
    
    async def _execute_steps(self, workflow_state: WorkflowState):
        """Execute workflow steps in order"""
        logger.info(f"Executing {len(workflow_state.steps)} steps for workflow {workflow_state.workflow_id}")
        
        for step in workflow_state.steps:
            logger.info(f"Executing step {step.step_id}: {step.description}")
            
            # Update step status
            step.status = StepStatus.IN_PROGRESS
            step.started_at = datetime.utcnow().isoformat()
            
            # Record start time for execution tracking
            start_time = time.time()
            
            # Log trace - step started
            trace_logger.log_trace(WorkflowTrace(
                task_id=workflow_state.workflow_id,
                session_id=workflow_state.session_id,
                step_number=step.step_id,
                selected_tool=step.tool_name,
                input_data={
                    "description": step.description,
                    "tool_params": step.tool_params
                },
                output_data=None,
                status=TraceStatus.IN_PROGRESS
            ))
            
            try:
                # Check dependencies
                if step.depends_on:
                    for dep_id in step.depends_on:
                        dep_step = workflow_state.get_step(dep_id)
                        if dep_step and dep_step.status != StepStatus.COMPLETED:
                            raise Exception(f"Step {step.step_id} depends on incomplete step {dep_id}")
                
                # Execute the step
                result = await self._execute_single_step(step, workflow_state)
                
                # Calculate execution time
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Store result
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow().isoformat()
                
                # Store intermediate data for next steps
                workflow_state.add_intermediate_data(f"step_{step.step_id}_result", result)
                
                # Log trace - step completed
                trace_logger.log_trace(WorkflowTrace(
                    task_id=workflow_state.workflow_id,
                    session_id=workflow_state.session_id,
                    step_number=step.step_id,
                    selected_tool=step.tool_name,
                    input_data={
                        "description": step.description,
                        "tool_params": step.tool_params
                    },
                    output_data=result,
                    status=TraceStatus.COMPLETED,
                    execution_time_ms=execution_time_ms
                ))
                
                logger.info(f"Step {step.step_id} completed successfully in {execution_time_ms:.2f}ms")
                
            except Exception as e:
                # Calculate execution time even for failed steps
                execution_time_ms = (time.time() - start_time) * 1000
                
                logger.error(f"Step {step.step_id} failed: {str(e)}", exc_info=True)
                step.status = StepStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.utcnow().isoformat()
                
                # Log trace - step failed
                trace_logger.log_trace(WorkflowTrace(
                    task_id=workflow_state.workflow_id,
                    session_id=workflow_state.session_id,
                    step_number=step.step_id,
                    selected_tool=step.tool_name,
                    input_data={
                        "description": step.description,
                        "tool_params": step.tool_params
                    },
                    output_data=None,
                    status=TraceStatus.FAILED,
                    execution_time_ms=execution_time_ms,
                    error_message=str(e)
                ))
                
                # Continue with other steps or fail workflow
                # For now, we'll continue but log the error
                workflow_state.add_intermediate_data(f"step_{step.step_id}_error", str(e))
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        workflow_state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        if not step.tool_name:
            # No tool specified - just acknowledge the step
            return {
                "success": True,
                "message": f"Step {step.step_id} executed without tool"
            }
        
        # Get the tool
        tool = self.tool_registry.get_tool(step.tool_name)
        if not tool:
            raise Exception(f"Tool '{step.tool_name}' not found")
        
        # Resolve parameters with intermediate data
        resolved_params = self._resolve_parameters(step.tool_params, workflow_state)
        
        # Execute tool
        logger.info(f"Executing tool '{step.tool_name}' with params: {resolved_params}")
        result = await tool.safe_execute(**resolved_params)
        
        if not result.get("success"):
            raise Exception(f"Tool execution failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        workflow_state: WorkflowState
    ) -> Dict[str, Any]:
        """Resolve parameters that reference intermediate data"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$step_"):
                # Reference to previous step result
                step_ref = value[1:]  # Remove $
                referenced_data = workflow_state.get_intermediate_data(step_ref)
                if referenced_data:
                    resolved[key] = referenced_data
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    async def _generate_final_answer(self, workflow_state: WorkflowState):
        """Generate final answer by synthesizing all step results using structured prompts"""
        logger.info(f"Generating final answer for workflow {workflow_state.workflow_id}")
        
        # Collect all step results
        step_results = []
        for step in workflow_state.steps:
            step_results.append({
                "step_id": step.step_id,
                "description": step.description,
                "tool_name": step.tool_name,
                "status": step.status.value,
                "result": step.result,
                "error": step.error
            })
        
        # Use structured prompt template
        synthesis_prompt = PromptTemplates.get_final_answer_prompt(
            query=workflow_state.query,
            workflow_results=step_results,
            context=None  # Could add session context here if needed
        )
        
        synthesis_response = await chat_service.process_message(
            message=synthesis_prompt,
            session_id=f"{workflow_state.session_id}_synthesis"
        )
        
        # Parse and validate the final answer
        try:
            validated_answer = OutputParser.validate_final_answer(synthesis_response.get("reply", ""))
            
            # Store the comprehensive answer with metadata
            workflow_state.final_result = validated_answer.answer
            
            # Store additional metadata
            workflow_state.add_intermediate_data("final_answer_metadata", {
                "sources": validated_answer.sources or [],
                "confidence": validated_answer.confidence,
                "additional_context": validated_answer.additional_context,
                "follow_up_suggestions": validated_answer.follow_up_suggestions or []
            })
            
            logger.info(
                f"Final answer generated (confidence: {validated_answer.confidence}): "
                f"{workflow_state.final_result[:100]}..."
            )
            
        except (ValidationError, ValueError) as e:
            logger.warning(f"Final answer validation failed: {e}. Using raw response.")
            # Fallback to raw response
            workflow_state.final_result = synthesis_response.get("reply", "Unable to generate final answer")
            logger.info(f"Final answer generated (fallback): {workflow_state.final_result[:100]}...")
    
    def _build_tool_descriptions(self, tools: Dict[str, Any]) -> str:
        """Build formatted description of available tools"""
        descriptions = []
        for name, tool in tools.items():
            metadata = tool.metadata
            descriptions.append(
                f"- {metadata.name}: {metadata.description}"
            )
        return "\n".join(descriptions)
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all workflows, optionally filtered by session"""
        workflows = []
        for wf_id, wf_state in self.workflows.items():
            if session_id is None or wf_state.session_id == session_id:
                workflows.append(wf_state.to_dict())
        return workflows


# Singleton instance
workflow_executor = WorkflowExecutor()
