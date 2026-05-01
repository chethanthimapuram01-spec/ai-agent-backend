"""
Test script for Workflow Trace Logger

Demonstrates trace logging functionality and API usage
"""
import asyncio
import json
from app.agents.workflow_executor import workflow_executor
from app.services.trace_logger import trace_logger


async def test_trace_logging():
    """Test trace logging with workflow execution"""
    
    print("=" * 80)
    print("WORKFLOW TRACE LOGGING TEST")
    print("=" * 80)
    print()
    
    # Execute a workflow
    print("1. Executing workflow with trace logging...")
    print("-" * 80)
    
    result = await workflow_executor.execute_workflow(
        query="Get weather for London and analyze the data",
        session_id="trace_test_session"
    )
    
    workflow_id = result.get("workflow_id", "unknown")
    print(f"✓ Workflow executed: {workflow_id}")
    print(f"  Success: {result['success']}")
    
    # Retrieve traces
    print("\n2. Retrieving trace logs...")
    print("-" * 80)
    
    traces = trace_logger.get_task_traces(workflow_id)
    print(f"✓ Retrieved {len(traces)} trace entries\n")
    
    for trace in traces:
        print(f"Step {trace['step_number']}: {trace.get('selected_tool', 'No tool')}")
        print(f"  Status: {trace['status']}")
        print(f"  Execution Time: {trace.get('execution_time_ms', 0):.2f}ms")
        if trace.get('error_message'):
            print(f"  Error: {trace['error_message']}")
        print()
    
    # Get task summary
    print("3. Getting task summary...")
    print("-" * 80)
    
    summary = trace_logger.get_task_summary(workflow_id)
    if summary:
        print(f"✓ Task Summary:")
        print(f"  Total Steps: {summary['total_steps']}")
        print(f"  Completed: {summary['completed_steps']}")
        print(f"  Failed: {summary['failed_steps']}")
        print(f"  Total Time: {summary['total_execution_time_ms']:.2f}ms")
        print(f"  Tools Used: {', '.join(summary['tools_used'])}")
        print(f"  Status: {summary['status']}")
    
    # Get session traces
    print("\n4. Getting all traces for session...")
    print("-" * 80)
    
    session_traces = trace_logger.get_session_traces("trace_test_session", limit=20)
    print(f"✓ Found {len(session_traces)} traces in session")
    
    # Get recent traces
    print("\n5. Getting recent traces across all workflows...")
    print("-" * 80)
    
    recent_traces = trace_logger.get_recent_traces(limit=10)
    print(f"✓ Found {len(recent_traces)} recent traces")
    
    print("\n" + "=" * 80)
    print("TRACE LOGGING TEST COMPLETED")
    print("=" * 80)


async def test_trace_api_format():
    """Test trace data format for API"""
    
    print("\n\n" + "=" * 80)
    print("TRACE API FORMAT TEST")
    print("=" * 80)
    print()
    
    # Execute a simple workflow
    result = await workflow_executor.execute_workflow(
        query="Simple test workflow",
        session_id="api_test"
    )
    
    workflow_id = result.get("workflow_id")
    
    # Get traces in API format
    traces = trace_logger.get_task_traces(workflow_id)
    
    print("Sample Trace Entry (API Format):")
    print("-" * 80)
    if traces:
        print(json.dumps(traces[0], indent=2, default=str))
    
    print("\n\nTask Summary (API Format):")
    print("-" * 80)
    summary = trace_logger.get_task_summary(workflow_id)
    if summary:
        print(json.dumps(summary, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("API FORMAT TEST COMPLETED")
    print("=" * 80)


async def test_trace_performance():
    """Test trace logging performance"""
    
    print("\n\n" + "=" * 80)
    print("TRACE PERFORMANCE TEST")
    print("=" * 80)
    print()
    
    import time
    
    # Execute multiple workflows
    print("Executing 3 workflows to test trace logging performance...")
    print("-" * 80)
    
    start_time = time.time()
    
    workflows = []
    for i in range(3):
        result = await workflow_executor.execute_workflow(
            query=f"Test workflow {i+1}",
            session_id="perf_test"
        )
        workflows.append(result.get("workflow_id"))
    
    total_time = time.time() - start_time
    
    print(f"✓ Executed 3 workflows in {total_time:.2f}s")
    
    # Count total traces
    total_traces = 0
    for wf_id in workflows:
        traces = trace_logger.get_task_traces(wf_id)
        total_traces += len(traces)
    
    print(f"✓ Total traces logged: {total_traces}")
    print(f"✓ Average time per trace: {(total_time / total_traces * 1000):.2f}ms")
    
    # Test retrieval performance
    print("\nTesting trace retrieval performance...")
    print("-" * 80)
    
    start_time = time.time()
    recent = trace_logger.get_recent_traces(limit=100)
    retrieval_time = (time.time() - start_time) * 1000
    
    print(f"✓ Retrieved {len(recent)} traces in {retrieval_time:.2f}ms")
    
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🔍 Workflow Trace Logger Test Suite\n")
    
    # Run tests
    asyncio.run(test_trace_logging())
    asyncio.run(test_trace_api_format())
    asyncio.run(test_trace_performance())
    
    print("\n✅ All trace logging tests completed!\n")
