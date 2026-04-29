"""
Test script for WorkflowExecutor

Demonstrates multi-step workflow execution with intermediate data passing
"""
import asyncio
import json
from app.agents.workflow_executor import workflow_executor


async def test_workflow_examples():
    """Test various workflow scenarios"""
    
    test_workflows = [
        {
            "name": "Document + API + Recommendation",
            "query": "Find details from the uploaded document, call weather API for London, and generate a recommendation",
            "description": "Complex workflow combining document retrieval, API call, and synthesis"
        },
        {
            "name": "API Analysis",
            "query": "Get Bitcoin price, analyze the trend, and summarize findings",
            "description": "API call followed by analysis"
        },
        {
            "name": "Multi-Document Analysis",
            "query": "Read the contract terms and generate a compliance summary",
            "description": "Document-heavy workflow with analysis"
        },
        {
            "name": "Data Collection and Synthesis",
            "query": "Get weather for New York, get cryptocurrency prices, and create a data summary report",
            "description": "Multiple API calls with data synthesis"
        }
    ]
    
    print("=" * 80)
    print("WORKFLOW EXECUTOR TEST SUITE")
    print("=" * 80)
    print()
    
    for idx, test_case in enumerate(test_workflows, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {idx}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"Description: {test_case['description']}")
        print(f"Query: \"{test_case['query']}\"")
        print("-" * 80)
        
        try:
            # Execute workflow
            result = await workflow_executor.execute_workflow(
                query=test_case['query'],
                session_id=f"test_{idx}"
            )
            
            if result['success']:
                print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
                print(f"\nWorkflow ID: {result['workflow_id']}")
                
                # Display workflow state
                state = result['workflow_state']
                print(f"\nStatus: {state['status']}")
                print(f"\nExecution Plan ({len(state['steps'])} steps):")
                for step in state['steps']:
                    status_icon = "✅" if step['status'] == 'completed' else "❌" if step['status'] == 'failed' else "⏳"
                    print(f"  {status_icon} Step {step['step_id']}: {step['description']}")
                    if step['tool_name']:
                        print(f"      Tool: {step['tool_name']}")
                    if step['status'] == 'completed' and step.get('result'):
                        print(f"      Result: {str(step['result'])[:100]}...")
                    elif step['status'] == 'failed':
                        print(f"      Error: {step.get('error', 'Unknown')}")
                
                print(f"\nIntermediate Data Keys: {list(state['intermediate_data'].keys())}")
                
                print(f"\nFinal Answer:")
                print("-" * 80)
                print(result['response'])
                print("-" * 80)
                
            else:
                print("❌ WORKFLOW FAILED")
                print(f"Error: {result.get('error', 'Unknown error')}")
                
                # Still show what was executed
                if result.get('workflow_state'):
                    state = result['workflow_state']
                    print(f"\nSteps attempted:")
                    for step in state.get('steps', []):
                        status = step['status']
                        print(f"  Step {step['step_id']}: {step['description']} - {status}")
            
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
        
        print("=" * 80)
        print()
    
    # Show all workflows
    print("\n" + "=" * 80)
    print("ALL WORKFLOWS SUMMARY")
    print("=" * 80)
    
    all_workflows = workflow_executor.list_workflows()
    print(f"\nTotal Workflows: {len(all_workflows)}")
    
    for wf in all_workflows:
        print(f"\n- {wf['workflow_id']}")
        print(f"  Query: {wf['query'][:60]}...")
        print(f"  Status: {wf['status']}")
        print(f"  Steps: {len(wf['steps'])}")
        print(f"  Created: {wf['created_at']}")


async def test_specific_workflow():
    """Test a specific workflow with detailed output"""
    
    query = "Find information in the uploaded documents about pricing, get the current weather for London, and recommend the best action"
    
    print("=" * 80)
    print("DETAILED WORKFLOW TEST")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print("-" * 80)
    
    result = await workflow_executor.execute_workflow(
        query=query,
        session_id="detailed_test"
    )
    
    print("\n" + "=" * 80)
    print("COMPLETE WORKFLOW STATE")
    print("=" * 80)
    print(json.dumps(result, indent=2, default=str))


async def test_workflow_state_retrieval():
    """Test retrieving workflow state by ID"""
    
    # First execute a workflow
    result = await workflow_executor.execute_workflow(
        query="Get weather and analyze it",
        session_id="state_test"
    )
    
    workflow_id = result['workflow_id']
    
    print("=" * 80)
    print("WORKFLOW STATE RETRIEVAL TEST")
    print("=" * 80)
    print(f"\nWorkflow ID: {workflow_id}")
    
    # Retrieve the state
    state = workflow_executor.get_workflow_state(workflow_id)
    
    if state:
        print("\n✅ Workflow state retrieved successfully")
        print(f"\nStatus: {state.status.value}")
        print(f"Steps: {len(state.steps)}")
        print(f"Intermediate Data: {list(state.intermediate_data.keys())}")
        print(f"Final Result: {state.final_result[:100] if state.final_result else 'N/A'}...")
    else:
        print("❌ Workflow state not found")


if __name__ == "__main__":
    print("\n🔧 Workflow Executor Test Suite\n")
    
    # Run comprehensive tests
    print("Running workflow examples...\n")
    asyncio.run(test_workflow_examples())
    
    # Uncomment to run specific tests:
    # asyncio.run(test_specific_workflow())
    # asyncio.run(test_workflow_state_retrieval())
