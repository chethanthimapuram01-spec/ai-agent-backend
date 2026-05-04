"""
Reusable prompt templates for AI agent tasks with structured output validation

This module provides:
- Pydantic models for validating LLM outputs
- System prompts for each task type
- JSON schema generation for structured outputs
- Output parsing and validation utilities
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
import json


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUTS
# ============================================================================

class ToolSelectionOutput(BaseModel):
    """Structured output for tool selection decisions"""
    query_type: Literal["DIRECT", "DOCUMENT", "API", "MULTI_STEP"] = Field(
        description="Type of query: DIRECT (simple answer), DOCUMENT (needs RAG), API (needs external call), MULTI_STEP (complex workflow)"
    )
    is_multi_step: bool = Field(
        description="Whether the query requires multiple steps to complete"
    )
    selected_tool: Optional[str] = Field(
        default=None,
        description="Name of the tool to use for single-step queries (null for multi-step)"
    )
    tool_parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters to pass to the selected tool"
    )
    reasoning: str = Field(
        description="Brief explanation of why this approach was chosen"
    )
    requires_context: bool = Field(
        default=False,
        description="Whether the query needs conversation history context"
    )
    
    @validator("selected_tool")
    def validate_tool_selection(cls, v, values):
        """Validate tool selection is consistent with query type"""
        if values.get("is_multi_step") and v is not None:
            raise ValueError("Multi-step queries should not have a selected_tool")
        if not values.get("is_multi_step") and values.get("query_type") != "DIRECT" and v is None:
            raise ValueError("Single-step non-DIRECT queries must have a selected_tool")
        return v


class WorkflowPlanOutput(BaseModel):
    """Structured output for workflow planning"""
    task_analysis: str = Field(
        description="Analysis of what the task requires"
    )
    required_capabilities: List[str] = Field(
        description="List of capabilities needed (e.g., 'document_retrieval', 'api_call', 'calculation')"
    )
    steps: List[Dict[str, Any]] = Field(
        description="Ordered list of steps with tool assignments and parameters"
    )
    expected_challenges: Optional[List[str]] = Field(
        default=None,
        description="Potential challenges or edge cases to handle"
    )
    success_criteria: str = Field(
        description="What defines successful completion of this workflow"
    )
    
    @validator("steps")
    def validate_steps(cls, v):
        """Validate steps have required fields"""
        for i, step in enumerate(v, 1):
            if "step_id" not in step:
                step["step_id"] = i
            if "description" not in step:
                raise ValueError(f"Step {i} missing 'description' field")
            if "tool_name" not in step and "action" not in step:
                raise ValueError(f"Step {i} must have 'tool_name' or 'action'")
        return v


class SummarizationOutput(BaseModel):
    """Structured output for summarization tasks"""
    summary: str = Field(
        description="Concise summary of the content"
    )
    key_points: List[str] = Field(
        description="Main points extracted from the content"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the summary quality"
    )
    missing_information: Optional[List[str]] = Field(
        default=None,
        description="Information that would improve the summary if available"
    )


class FinalAnswerOutput(BaseModel):
    """Structured output for final answer generation"""
    answer: str = Field(
        description="The main answer to the user's query"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="Sources used to generate the answer (document IDs, API endpoints, etc.)"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the answer"
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context or caveats about the answer"
    )
    follow_up_suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggested follow-up questions the user might ask"
    )


class TaskAnalysisOutput(BaseModel):
    """Structured output for task analysis"""
    task_type: str = Field(
        description="Category of the task (e.g., 'information_retrieval', 'data_analysis', 'content_generation')"
    )
    complexity: Literal["simple", "moderate", "complex"] = Field(
        description="Estimated complexity level"
    )
    required_tools: List[str] = Field(
        description="Tools that will be needed"
    )
    estimated_steps: int = Field(
        description="Estimated number of steps required",
        ge=1
    )
    can_parallelize: bool = Field(
        default=False,
        description="Whether some steps can be executed in parallel"
    )


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

class PromptTemplates:
    """Container for all prompt templates"""
    
    @staticmethod
    def get_tool_selection_prompt(query: str, available_tools: List[str], context: Optional[str] = None) -> str:
        """
        Generate prompt for tool selection and query classification
        
        Args:
            query: User's query
            available_tools: List of available tool names
            context: Optional conversation context
            
        Returns:
            Formatted prompt string
        """
        tools_list = "\n".join([f"- {tool}" for tool in available_tools])
        
        context_section = ""
        if context:
            context_section = f"""
## Conversation Context
{context}
"""
        
        return f"""You are an AI agent router that decides how to handle user queries.

Your task is to analyze the query and determine:
1. The type of query (DIRECT, DOCUMENT, API, or MULTI_STEP)
2. Whether it requires multiple steps
3. Which tool(s) to use
4. What parameters to pass

## Query Types
- DIRECT: Simple questions you can answer directly without tools
- DOCUMENT: Questions that need information from uploaded documents (use document_query tool)
- API: Questions that need external data (use api_caller tool)
- MULTI_STEP: Complex tasks requiring multiple tools or steps in sequence

## Available Tools
{tools_list}

## Tool Descriptions
- document_query: Search and retrieve information from uploaded documents using RAG
- api_caller: Make HTTP requests to external APIs (supports GET, POST, PUT, DELETE)
- calculator: Perform mathematical calculations
- text_analyzer: Analyze text for sentiment, keywords, entities, etc.
{context_section}
## User Query
{query}

## Instructions
Analyze the query and respond with a JSON object following this exact schema:
{{
  "query_type": "DIRECT" | "DOCUMENT" | "API" | "MULTI_STEP",
  "is_multi_step": boolean,
  "selected_tool": string | null,
  "tool_parameters": object | null,
  "reasoning": "Brief explanation of your decision",
  "requires_context": boolean
}}

## Examples

Query: "What is 2 + 2?"
{{
  "query_type": "DIRECT",
  "is_multi_step": false,
  "selected_tool": null,
  "tool_parameters": null,
  "reasoning": "Simple arithmetic question that can be answered directly",
  "requires_context": false
}}

Query: "What does the contract say about payment terms?"
{{
  "query_type": "DOCUMENT",
  "is_multi_step": false,
  "selected_tool": "document_query",
  "tool_parameters": {{"query": "payment terms"}},
  "reasoning": "Needs to retrieve information from uploaded documents",
  "requires_context": false
}}

Query: "Get the current Bitcoin price and calculate 10% of it"
{{
  "query_type": "MULTI_STEP",
  "is_multi_step": true,
  "selected_tool": null,
  "tool_parameters": null,
  "reasoning": "Requires API call for price data, then calculation - two distinct steps",
  "requires_context": false
}}

Respond ONLY with the JSON object, no additional text."""


    @staticmethod
    def get_workflow_planning_prompt(query: str, available_tools: List[str], context: Optional[str] = None) -> str:
        """
        Generate prompt for workflow planning
        
        Args:
            query: User's task description
            available_tools: List of available tool names
            context: Optional conversation context
            
        Returns:
            Formatted prompt string
        """
        tools_list = "\n".join([f"- {tool}" for tool in available_tools])
        
        context_section = ""
        if context:
            context_section = f"""
## Conversation Context
{context}
"""
        
        return f"""You are an AI workflow planner that breaks down complex tasks into executable steps.

Your task is to analyze the user's request and create a detailed, step-by-step execution plan.

## Available Tools
{tools_list}

## Tool Capabilities
- document_query: Search documents, extract information, answer questions based on document content
- api_caller: HTTP requests (GET, POST, PUT, DELETE) to external APIs
- calculator: Mathematical operations, formulas, numerical analysis
- text_analyzer: Sentiment analysis, keyword extraction, entity recognition, text classification
{context_section}
## User Task
{query}

## Instructions
Create a workflow plan with these components:
1. Task analysis - what needs to be accomplished
2. Required capabilities - what abilities are needed
3. Step-by-step plan - ordered execution steps with tool assignments
4. Expected challenges - potential issues to handle
5. Success criteria - how to know the task is complete

Each step should have:
- step_id: Sequential number
- description: What this step does
- tool_name: Tool to use (or null if no tool needed)
- tool_params: Parameters for the tool
- depends_on: List of step IDs that must complete first (empty if no dependencies)

Respond with a JSON object following this schema:
{{
  "task_analysis": "Analysis of what the task requires",
  "required_capabilities": ["capability1", "capability2"],
  "steps": [
    {{
      "step_id": 1,
      "description": "Description of step",
      "tool_name": "tool_name" | null,
      "tool_params": {{}},
      "depends_on": []
    }}
  ],
  "expected_challenges": ["challenge1", "challenge2"],
  "success_criteria": "What defines success"
}}

## Example

Task: "Get weather for London and analyze if it's good for outdoor activities"

{{
  "task_analysis": "Need to fetch current weather data for London, then analyze the conditions to determine suitability for outdoor activities",
  "required_capabilities": ["api_call", "data_analysis"],
  "steps": [
    {{
      "step_id": 1,
      "description": "Fetch current weather data for London",
      "tool_name": "api_caller",
      "tool_params": {{
        "method": "GET",
        "endpoint": "https://api.weatherapi.com/v1/current.json?q=London"
      }},
      "depends_on": []
    }},
    {{
      "step_id": 2,
      "description": "Analyze weather conditions for outdoor activity suitability",
      "tool_name": null,
      "tool_params": {{}},
      "depends_on": [1]
    }}
  ],
  "expected_challenges": [
    "Weather API might be unavailable",
    "Need to define 'good weather' criteria"
  ],
  "success_criteria": "Successfully retrieved weather data and provided clear recommendation for outdoor activities"
}}

Respond ONLY with the JSON object, no additional text."""


    @staticmethod
    def get_summarization_prompt(content: str, focus: Optional[str] = None, max_length: Optional[int] = None) -> str:
        """
        Generate prompt for content summarization
        
        Args:
            content: Content to summarize
            focus: Optional focus area for the summary
            max_length: Optional maximum summary length
            
        Returns:
            Formatted prompt string
        """
        focus_section = ""
        if focus:
            focus_section = f"\n## Focus Area\n{focus}\n"
        
        length_section = ""
        if max_length:
            length_section = f"\n## Length Constraint\nKeep the summary under {max_length} characters.\n"
        
        return f"""You are an expert summarization assistant that creates concise, accurate summaries.

Your task is to analyze the content and extract the most important information.
{focus_section}{length_section}
## Content to Summarize
{content}

## Instructions
Create a structured summary that includes:
1. A concise summary of the main content
2. Key points (3-7 bullet points)
3. Your confidence level in the summary quality
4. Any missing information that would improve the summary

Respond with a JSON object following this schema:
{{
  "summary": "Concise summary of the content",
  "key_points": [
    "Main point 1",
    "Main point 2",
    "Main point 3"
  ],
  "confidence": "high" | "medium" | "low",
  "missing_information": ["What would help improve this summary"]
}}

## Quality Criteria
- Accuracy: Summary must accurately represent the content
- Conciseness: Remove redundancy while preserving meaning
- Completeness: Cover all major points
- Clarity: Easy to understand

Respond ONLY with the JSON object, no additional text."""


    @staticmethod
    def get_final_answer_prompt(
        query: str,
        workflow_results: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> str:
        """
        Generate prompt for final answer synthesis
        
        Args:
            query: Original user query
            workflow_results: Results from workflow steps
            context: Optional conversation context
            
        Returns:
            Formatted prompt string
        """
        # Format workflow results
        results_text = ""
        for i, result in enumerate(workflow_results, 1):
            results_text += f"\n### Step {i}: {result.get('description', 'N/A')}\n"
            results_text += f"Tool: {result.get('tool_name', 'None')}\n"
            results_text += f"Result: {json.dumps(result.get('result', {}), indent=2)}\n"
        
        context_section = ""
        if context:
            context_section = f"""
## Conversation Context
{context}
"""
        
        return f"""You are an AI assistant that synthesizes workflow results into clear, helpful answers.

Your task is to combine information from multiple steps and generate a comprehensive final answer.

## Original Query
{query}
{context_section}
## Workflow Results
{results_text}

## Instructions
Synthesize the workflow results into a final answer that:
1. Directly addresses the user's query
2. Integrates information from all relevant steps
3. Is clear, concise, and well-structured
4. Includes source attribution when applicable
5. Acknowledges any limitations or uncertainties

Respond with a JSON object following this schema:
{{
  "answer": "The comprehensive answer to the user's query",
  "sources": ["source1", "source2"],
  "confidence": "high" | "medium" | "low",
  "additional_context": "Any caveats or additional information",
  "follow_up_suggestions": [
    "Suggested follow-up question 1",
    "Suggested follow-up question 2"
  ]
}}

## Quality Criteria
- Completeness: Address all aspects of the query
- Accuracy: Ensure information is correct and properly sourced
- Clarity: Use clear, accessible language
- Usefulness: Provide actionable information

Respond ONLY with the JSON object, no additional text."""


    @staticmethod
    def get_task_analysis_prompt(query: str) -> str:
        """
        Generate prompt for task analysis
        
        Args:
            query: User's query to analyze
            
        Returns:
            Formatted prompt string
        """
        return f"""You are an AI task analyzer that evaluates query complexity and requirements.

Your task is to analyze the user's query and provide a structured assessment.

## Query
{query}

## Instructions
Analyze the query and determine:
1. Task type/category
2. Complexity level
3. Required tools
4. Estimated number of steps
5. Whether steps can be parallelized

Respond with a JSON object following this schema:
{{
  "task_type": "information_retrieval | data_analysis | content_generation | calculation | api_integration | document_processing",
  "complexity": "simple" | "moderate" | "complex",
  "required_tools": ["tool1", "tool2"],
  "estimated_steps": 1-10,
  "can_parallelize": boolean
}}

## Complexity Guidelines
- Simple: Single tool, single step, straightforward
- Moderate: 2-3 tools or steps, some dependencies
- Complex: Multiple tools, complex dependencies, multi-phase execution

Respond ONLY with the JSON object, no additional text."""


# ============================================================================
# OUTPUT PARSING AND VALIDATION
# ============================================================================

class OutputParser:
    """Utilities for parsing and validating LLM outputs"""
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response, handling markdown code blocks
        
        Args:
            text: Raw LLM response
            
        Returns:
            Parsed JSON object
            
        Raises:
            ValueError: If no valid JSON found
        """
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        # Strip whitespace
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {e}\nText: {text}")
    
    @staticmethod
    def validate_tool_selection(response: str) -> ToolSelectionOutput:
        """Parse and validate tool selection output"""
        data = OutputParser.extract_json(response)
        return ToolSelectionOutput(**data)
    
    @staticmethod
    def validate_workflow_plan(response: str) -> WorkflowPlanOutput:
        """Parse and validate workflow plan output"""
        data = OutputParser.extract_json(response)
        return WorkflowPlanOutput(**data)
    
    @staticmethod
    def validate_summarization(response: str) -> SummarizationOutput:
        """Parse and validate summarization output"""
        data = OutputParser.extract_json(response)
        return SummarizationOutput(**data)
    
    @staticmethod
    def validate_final_answer(response: str) -> FinalAnswerOutput:
        """Parse and validate final answer output"""
        data = OutputParser.extract_json(response)
        return FinalAnswerOutput(**data)
    
    @staticmethod
    def validate_task_analysis(response: str) -> TaskAnalysisOutput:
        """Parse and validate task analysis output"""
        data = OutputParser.extract_json(response)
        return TaskAnalysisOutput(**data)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_json_schema(model_class: type[BaseModel]) -> Dict[str, Any]:
    """
    Get JSON schema for a Pydantic model
    
    Args:
        model_class: Pydantic model class
        
    Returns:
        JSON schema dictionary
    """
    return model_class.model_json_schema()


def validate_and_parse(response: str, output_type: str) -> BaseModel:
    """
    Validate and parse LLM response based on output type
    
    Args:
        response: Raw LLM response
        output_type: Type of output ("tool_selection", "workflow_plan", etc.)
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If output_type is unknown or validation fails
    """
    parsers = {
        "tool_selection": OutputParser.validate_tool_selection,
        "workflow_plan": OutputParser.validate_workflow_plan,
        "summarization": OutputParser.validate_summarization,
        "final_answer": OutputParser.validate_final_answer,
        "task_analysis": OutputParser.validate_task_analysis,
    }
    
    parser = parsers.get(output_type)
    if not parser:
        raise ValueError(f"Unknown output type: {output_type}")
    
    return parser(response)
