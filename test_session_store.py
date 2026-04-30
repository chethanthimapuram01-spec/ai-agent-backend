"""
Test script for Session Store functionality

Demonstrates session management, chat history, and context retrieval
"""
import asyncio
from app.services.session_store import session_store, MessageRole
from app.agents.agent_controller import agent_controller


async def test_session_store():
    """Test session store basic functionality"""
    
    print("=" * 80)
    print("SESSION STORE TEST")
    print("=" * 80)
    
    session_id = "test_session_1"
    
    # Test 1: Create session and add messages
    print("\n1. Creating session and adding messages...")
    print("-" * 80)
    
    session_store.create_session(session_id, metadata={"user": "test_user"})
    
    # Add conversation
    session_store.add_user_message(session_id, "Hello, can you help me?")
    session_store.add_assistant_message(session_id, "Of course! I'd be happy to help you.")
    session_store.add_user_message(session_id, "What's the weather like?")
    session_store.add_assistant_message(session_id, "I'll check the weather for you.")
    
    # Add tool execution
    session_store.add_tool_output(
        session_id=session_id,
        tool_name="api_caller",
        tool_params={"endpoint": "weather", "city": "London"},
        result={"temperature": "15°C", "condition": "Cloudy"},
        success=True
    )
    
    session_store.add_assistant_message(
        session_id,
        "The weather in London is 15°C and cloudy."
    )
    
    print("✓ Added 4 messages and 1 tool execution")
    
    # Test 2: Get conversation history
    print("\n2. Retrieving conversation history...")
    print("-" * 80)
    
    history = session_store.get_conversation_history(session_id)
    print(f"✓ Retrieved {len(history)} messages:\n")
    
    for i, msg in enumerate(history, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:60]
        print(f"  {i}. [{role.upper()}] {content}...")
    
    # Test 3: Get recent context
    print("\n3. Getting recent context for LLM...")
    print("-" * 80)
    
    context = session_store.get_recent_context(session_id, message_limit=3)
    print(f"✓ Retrieved {len(context)} recent messages in OpenAI format:\n")
    
    for msg in context:
        print(f"  {msg}")
    
    # Test 4: Get tool history
    print("\n4. Retrieving tool execution history...")
    print("-" * 80)
    
    tool_history = session_store.get_tool_history(session_id)
    print(f"✓ Retrieved {len(tool_history)} tool executions:\n")
    
    for exec in tool_history:
        print(f"  Tool: {exec['tool_name']}")
        print(f"  Success: {exec['success']}")
        print(f"  Result: {exec['result']}")
    
    # Test 5: Get session summary
    print("\n5. Getting session summary...")
    print("-" * 80)
    
    summary = session_store.get_session_summary(session_id)
    print(f"✓ Session Summary:")
    print(f"  Session ID: {summary['session_id']}")
    print(f"  Messages: {summary['message_count']}")
    print(f"  Tool Executions: {summary['tool_execution_count']}")
    print(f"  Duration: {summary['duration_minutes']} minutes")
    print(f"  Created: {summary['created_at']}")
    print(f"  Last Activity: {summary['last_activity']}")
    
    # Test 6: Multiple sessions
    print("\n6. Testing multiple sessions...")
    print("-" * 80)
    
    session_store.add_user_message("session_2", "Different session message")
    session_store.add_user_message("session_3", "Another session")
    
    all_sessions = session_store.list_sessions()
    print(f"✓ Total sessions: {len(all_sessions)}")
    print(f"  Sessions: {all_sessions}")
    
    print("\n" + "=" * 80)
    print("SESSION STORE TEST COMPLETED")
    print("=" * 80)


async def test_agent_with_context():
    """Test agent controller with conversation context"""
    
    print("\n\n" + "=" * 80)
    print("AGENT WITH CONTEXT TEST")
    print("=" * 80)
    
    session_id = "context_test_session"
    
    # Query 1
    print("\n1. First query (no context)...")
    print("-" * 80)
    
    result1 = await agent_controller.process_query(
        query="My name is Alice",
        session_id=session_id
    )
    print(f"Query: 'My name is Alice'")
    print(f"Response: {result1['response'][:100]}...")
    
    # Query 2 - should have context from first query
    print("\n2. Second query (with context)...")
    print("-" * 80)
    
    result2 = await agent_controller.process_query(
        query="What's my name?",
        session_id=session_id
    )
    print(f"Query: 'What's my name?'")
    print(f"Response: {result2['response'][:100]}...")
    
    # Check session history
    print("\n3. Checking session history...")
    print("-" * 80)
    
    history = session_store.get_conversation_history(session_id)
    print(f"✓ Session has {len(history)} messages")
    
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")[:50]
        print(f"  [{role}]: {content}...")
    
    # Check recent context
    print("\n4. Recent context for next query...")
    print("-" * 80)
    
    context = session_store.get_recent_context(session_id, message_limit=4)
    print(f"✓ Context size: {len(context)} messages")
    
    print("\n" + "=" * 80)
    print("AGENT CONTEXT TEST COMPLETED")
    print("=" * 80)


async def test_tool_tracking():
    """Test tool execution tracking in sessions"""
    
    print("\n\n" + "=" * 80)
    print("TOOL EXECUTION TRACKING TEST")
    print("=" * 80)
    
    session_id = "tool_test_session"
    
    # Execute query that uses tools
    print("\n1. Executing query with tool...")
    print("-" * 80)
    
    result = await agent_controller.process_query(
        query="Get the weather for London",
        session_id=session_id
    )
    
    print(f"Query: 'Get the weather for London'")
    print(f"Response: {result['response'][:100]}...")
    print(f"Used tool: {result.get('decision').tool_name if result.get('decision') else 'None'}")
    
    # Check tool history
    print("\n2. Checking tool execution history...")
    print("-" * 80)
    
    tool_history = session_store.get_tool_history(session_id)
    print(f"✓ Found {len(tool_history)} tool executions")
    
    for exec in tool_history:
        print(f"\n  Tool: {exec['tool_name']}")
        print(f"  Parameters: {exec['tool_params']}")
        print(f"  Success: {exec['success']}")
        print(f"  Timestamp: {exec['timestamp']}")
    
    # Check complete conversation history
    print("\n3. Complete conversation (messages + tools)...")
    print("-" * 80)
    
    history = session_store.get_conversation_history(session_id)
    print(f"✓ Total messages: {len(history)}")
    
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")[:60]
        print(f"  [{role}]: {content}...")
    
    print("\n" + "=" * 80)
    print("TOOL TRACKING TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🧪 Session Store & Context Management Tests\n")
    
    # Run tests
    asyncio.run(test_session_store())
    asyncio.run(test_agent_with_context())
    asyncio.run(test_tool_tracking())
    
    print("\n✅ All tests completed!\n")
