"""
Test script for intelligent routing system

This script demonstrates how the AgentController routes different types of queries
to appropriate tools or direct responses.
"""
import asyncio
import json
from app.agents.agent_controller import agent_controller, QueryType


async def test_routing():
    """Test various query types through the intelligent routing system"""
    
    test_queries = [
        # Direct response queries
        {
            "query": "What is artificial intelligence?",
            "expected_type": QueryType.DIRECT,
            "description": "Simple educational question"
        },
        {
            "query": "Hello, how are you?",
            "expected_type": QueryType.DIRECT,
            "description": "Greeting"
        },
        
        # Document queries
        {
            "query": "Summarize the uploaded contract",
            "expected_type": QueryType.DOCUMENT,
            "description": "Document summarization"
        },
        {
            "query": "What does the document say about pricing?",
            "expected_type": QueryType.DOCUMENT,
            "description": "Specific document question"
        },
        
        # API requests
        {
            "query": "Get weather for London",
            "expected_type": QueryType.API,
            "description": "Weather API request"
        },
        {
            "query": "What's the Bitcoin price?",
            "expected_type": QueryType.API,
            "description": "Crypto price request"
        },
        
        # Multi-step tasks
        {
            "query": "Get weather for London and summarize it",
            "expected_type": QueryType.MULTI_STEP,
            "description": "API call + summarization"
        },
        {
            "query": "Read the contract and compare with weather impact",
            "expected_type": QueryType.MULTI_STEP,
            "description": "Document query + API call + analysis"
        }
    ]
    
    print("=" * 80)
    print("INTELLIGENT ROUTING SYSTEM TEST")
    print("=" * 80)
    print()
    
    for idx, test_case in enumerate(test_queries, 1):
        print(f"\nTest Case {idx}: {test_case['description']}")
        print(f"Query: \"{test_case['query']}\"")
        print(f"Expected Type: {test_case['expected_type']}")
        print("-" * 80)
        
        try:
            # Process the query
            result = await agent_controller.process_query(
                query=test_case['query'],
                session_id=f"test_{idx}"
            )
            
            # Extract decision info
            decision = result.get('decision')
            if decision:
                print(f"✓ Query Type: {decision.query_type}")
                print(f"✓ Use Tool: {decision.use_tool}")
                if decision.use_tool:
                    print(f"✓ Tool Selected: {decision.tool_name}")
                    print(f"✓ Tool Params: {json.dumps(decision.tool_params, indent=2)}")
                print(f"✓ Reasoning: {decision.reasoning}")
                print(f"✓ Multi-Step: {decision.is_multi_step}")
                
                # Check if routing matches expectation
                if decision.query_type == test_case['expected_type']:
                    print(f"✅ PASS - Correct routing!")
                else:
                    print(f"❌ FAIL - Expected {test_case['expected_type']}, got {decision.query_type}")
            else:
                print("❌ No decision information available")
            
            print(f"\nResponse Preview: {result.get('response', 'N/A')[:200]}...")
            print(f"Success: {result.get('success', False)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("=" * 80)
    
    # Print execution history
    print("\n\nEXECUTION HISTORY:")
    print("=" * 80)
    history = agent_controller.get_execution_history(limit=20)
    for record in history:
        print(f"\nSession: {record['session_id']}")
        print(f"Query: {record['query'][:50]}...")
        print(f"Decision: {json.dumps(record['decision'], indent=2)}")
        print(f"Success: {record['success']}")
        print("-" * 80)


async def test_specific_routing(query: str):
    """Test a specific query and show detailed routing information"""
    print("=" * 80)
    print(f"TESTING QUERY: \"{query}\"")
    print("=" * 80)
    
    result = await agent_controller.process_query(
        query=query,
        session_id="specific_test"
    )
    
    print("\nFull Result:")
    print(json.dumps({
        "response": result.get("response"),
        "decision": {
            "use_tool": result.get("decision").use_tool if result.get("decision") else None,
            "tool_name": result.get("decision").tool_name if result.get("decision") else None,
            "query_type": result.get("decision").query_type if result.get("decision") else None,
            "is_multi_step": result.get("decision").is_multi_step if result.get("decision") else None,
            "reasoning": result.get("decision").reasoning if result.get("decision") else None,
        },
        "success": result.get("success"),
        "timestamp": result.get("timestamp")
    }, indent=2))


if __name__ == "__main__":
    print("\n🤖 Agent Routing System Test\n")
    
    # Run comprehensive test
    print("Running comprehensive routing tests...\n")
    asyncio.run(test_routing())
    
    # Example: Test a specific query
    # asyncio.run(test_specific_routing("Summarize the uploaded contract"))
