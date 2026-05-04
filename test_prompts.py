"""
Test suite for prompt templates and structured outputs

Validates:
- Pydantic model validation
- Prompt template generation
- Output parsing and validation
- Error handling
"""

import json
import asyncio
from app.utils.prompts import (
    PromptTemplates,
    OutputParser,
    ToolSelectionOutput,
    WorkflowPlanOutput,
    SummarizationOutput,
    FinalAnswerOutput,
    TaskAnalysisOutput
)
from pydantic import ValidationError


def test_tool_selection_validation():
    """Test ToolSelectionOutput validation"""
    print("=" * 80)
    print("TEST: Tool Selection Validation")
    print("=" * 80)
    
    # Valid DIRECT response
    valid_direct = {
        "query_type": "DIRECT",
        "is_multi_step": False,
        "selected_tool": None,
        "tool_parameters": None,
        "reasoning": "Simple question that can be answered directly",
        "requires_context": False
    }
    
    try:
        output = ToolSelectionOutput(**valid_direct)
        print("✓ Valid DIRECT response parsed successfully")
        print(f"  Query Type: {output.query_type}")
        print(f"  Reasoning: {output.reasoning}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Valid DOCUMENT query
    valid_document = {
        "query_type": "DOCUMENT",
        "is_multi_step": False,
        "selected_tool": "document_query",
        "tool_parameters": {"query": "contract terms"},
        "reasoning": "Needs document retrieval",
        "requires_context": False
    }
    
    try:
        output = ToolSelectionOutput(**valid_document)
        print("✓ Valid DOCUMENT query parsed successfully")
        print(f"  Tool: {output.selected_tool}")
        print(f"  Parameters: {output.tool_parameters}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Valid MULTI_STEP
    valid_multi_step = {
        "query_type": "MULTI_STEP",
        "is_multi_step": True,
        "selected_tool": None,
        "tool_parameters": None,
        "reasoning": "Requires multiple operations",
        "requires_context": False
    }
    
    try:
        output = ToolSelectionOutput(**valid_multi_step)
        print("✓ Valid MULTI_STEP parsed successfully")
        print(f"  Is Multi-Step: {output.is_multi_step}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Invalid: Multi-step with selected_tool (should fail)
    print("\nTesting invalid input (multi-step with selected_tool):")
    invalid_multi_step = {
        "query_type": "MULTI_STEP",
        "is_multi_step": True,
        "selected_tool": "document_query",  # Invalid!
        "tool_parameters": {"query": "test"},
        "reasoning": "Invalid configuration",
        "requires_context": False
    }
    
    try:
        output = ToolSelectionOutput(**invalid_multi_step)
        print("✗ Should have failed validation!")
    except ValidationError as e:
        print(f"✓ Correctly rejected invalid input: {e.errors()[0]['msg']}")
    
    print()


def test_workflow_plan_validation():
    """Test WorkflowPlanOutput validation"""
    print("=" * 80)
    print("TEST: Workflow Plan Validation")
    print("=" * 80)
    
    valid_plan = {
        "task_analysis": "User wants to fetch weather and analyze it",
        "required_capabilities": ["api_call", "data_analysis"],
        "steps": [
            {
                "step_id": 1,
                "description": "Fetch weather data",
                "tool_name": "api_caller",
                "tool_params": {"endpoint": "weather_api"},
                "depends_on": []
            },
            {
                "step_id": 2,
                "description": "Analyze weather data",
                "tool_name": None,
                "tool_params": {},
                "depends_on": [1]
            }
        ],
        "expected_challenges": ["API might be unavailable"],
        "success_criteria": "Weather data retrieved and analyzed"
    }
    
    try:
        output = WorkflowPlanOutput(**valid_plan)
        print("✓ Valid workflow plan parsed successfully")
        print(f"  Task Analysis: {output.task_analysis}")
        print(f"  Steps: {len(output.steps)}")
        for step in output.steps:
            print(f"    Step {step['step_id']}: {step['description']}")
        print(f"  Success Criteria: {output.success_criteria}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Test auto-assignment of step_id
    print("\nTesting step_id auto-assignment:")
    plan_without_ids = {
        "task_analysis": "Test task",
        "required_capabilities": ["test"],
        "steps": [
            {"description": "Step 1", "tool_name": "test_tool"},
            {"description": "Step 2", "action": "analyze"}
        ],
        "success_criteria": "Complete"
    }
    
    try:
        output = WorkflowPlanOutput(**plan_without_ids)
        print("✓ Step IDs auto-assigned successfully")
        for step in output.steps:
            print(f"    Step {step['step_id']}: {step['description']}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    print()


def test_output_parser():
    """Test OutputParser JSON extraction"""
    print("=" * 80)
    print("TEST: Output Parser")
    print("=" * 80)
    
    # Test JSON with markdown code blocks
    json_with_markdown = '''```json
{
  "query_type": "DIRECT",
  "is_multi_step": false,
  "selected_tool": null,
  "tool_parameters": null,
  "reasoning": "Simple answer",
  "requires_context": false
}
```'''
    
    try:
        parsed = OutputParser.extract_json(json_with_markdown)
        print("✓ Successfully extracted JSON from markdown code block")
        print(f"  Query Type: {parsed['query_type']}")
    except ValueError as e:
        print(f"✗ Failed to extract JSON: {e}")
    
    # Test plain JSON
    plain_json = '''{
  "query_type": "API",
  "is_multi_step": false,
  "selected_tool": "api_caller",
  "tool_parameters": {"endpoint": "test"},
  "reasoning": "Need API call",
  "requires_context": false
}'''
    
    try:
        parsed = OutputParser.extract_json(plain_json)
        print("✓ Successfully extracted plain JSON")
        print(f"  Selected Tool: {parsed['selected_tool']}")
    except ValueError as e:
        print(f"✗ Failed to extract JSON: {e}")
    
    # Test full validation
    print("\nTesting full validation pipeline:")
    try:
        validated = OutputParser.validate_tool_selection(json_with_markdown)
        print("✓ Successfully validated tool selection output")
        print(f"  Type: {type(validated).__name__}")
        print(f"  Query Type: {validated.query_type}")
    except (ValueError, ValidationError) as e:
        print(f"✗ Validation failed: {e}")
    
    print()


def test_prompt_generation():
    """Test prompt template generation"""
    print("=" * 80)
    print("TEST: Prompt Template Generation")
    print("=" * 80)
    
    # Tool selection prompt
    print("Tool Selection Prompt:")
    print("-" * 80)
    tools = ["document_query", "api_caller", "calculator"]
    prompt = PromptTemplates.get_tool_selection_prompt(
        query="What's the weather in London?",
        available_tools=tools
    )
    print(prompt[:300] + "...\n")
    print(f"✓ Generated {len(prompt)} characters")
    
    # Workflow planning prompt
    print("\nWorkflow Planning Prompt:")
    print("-" * 80)
    prompt = PromptTemplates.get_workflow_planning_prompt(
        query="Get Bitcoin price and calculate 10% of it",
        available_tools=tools
    )
    print(prompt[:300] + "...\n")
    print(f"✓ Generated {len(prompt)} characters")
    
    # Final answer prompt
    print("\nFinal Answer Prompt:")
    print("-" * 80)
    results = [
        {
            "step_id": 1,
            "description": "Fetch price",
            "tool_name": "api_caller",
            "result": {"price": 50000}
        },
        {
            "step_id": 2,
            "description": "Calculate 10%",
            "tool_name": "calculator",
            "result": {"answer": 5000}
        }
    ]
    prompt = PromptTemplates.get_final_answer_prompt(
        query="Get Bitcoin price and calculate 10%",
        workflow_results=results
    )
    print(prompt[:300] + "...\n")
    print(f"✓ Generated {len(prompt)} characters")
    
    print()


def test_summarization_output():
    """Test SummarizationOutput validation"""
    print("=" * 80)
    print("TEST: Summarization Output Validation")
    print("=" * 80)
    
    valid_summary = {
        "summary": "This is a concise summary of the content.",
        "key_points": [
            "First key point",
            "Second key point",
            "Third key point"
        ],
        "confidence": "high",
        "missing_information": ["Additional context needed"]
    }
    
    try:
        output = SummarizationOutput(**valid_summary)
        print("✓ Valid summary parsed successfully")
        print(f"  Summary: {output.summary}")
        print(f"  Key Points: {len(output.key_points)}")
        print(f"  Confidence: {output.confidence}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    print()


def test_final_answer_output():
    """Test FinalAnswerOutput validation"""
    print("=" * 80)
    print("TEST: Final Answer Output Validation")
    print("=" * 80)
    
    valid_answer = {
        "answer": "The Bitcoin price is $50,000 and 10% of that is $5,000.",
        "sources": ["api_caller: bitcoin_price", "calculator: percentage"],
        "confidence": "high",
        "additional_context": "Price as of current time",
        "follow_up_suggestions": [
            "Would you like historical price data?",
            "Should I calculate other percentages?"
        ]
    }
    
    try:
        output = FinalAnswerOutput(**valid_answer)
        print("✓ Valid final answer parsed successfully")
        print(f"  Answer: {output.answer}")
        print(f"  Sources: {output.sources}")
        print(f"  Confidence: {output.confidence}")
        print(f"  Follow-ups: {len(output.follow_up_suggestions)}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    print()


def test_task_analysis_output():
    """Test TaskAnalysisOutput validation"""
    print("=" * 80)
    print("TEST: Task Analysis Output Validation")
    print("=" * 80)
    
    valid_analysis = {
        "task_type": "api_integration",
        "complexity": "moderate",
        "required_tools": ["api_caller", "calculator"],
        "estimated_steps": 2,
        "can_parallelize": False
    }
    
    try:
        output = TaskAnalysisOutput(**valid_analysis)
        print("✓ Valid task analysis parsed successfully")
        print(f"  Task Type: {output.task_type}")
        print(f"  Complexity: {output.complexity}")
        print(f"  Required Tools: {output.required_tools}")
        print(f"  Estimated Steps: {output.estimated_steps}")
        print(f"  Can Parallelize: {output.can_parallelize}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    print()


def run_all_tests():
    """Run all tests"""
    print("\n🧪 Prompt Templates & Validation Test Suite\n")
    
    test_tool_selection_validation()
    test_workflow_plan_validation()
    test_output_parser()
    test_prompt_generation()
    test_summarization_output()
    test_final_answer_output()
    test_task_analysis_output()
    
    print("=" * 80)
    print("✅ All Tests Completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
