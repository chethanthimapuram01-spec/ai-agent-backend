# Workflow Execution Engine

## Overview

The WorkflowExecutor is a comprehensive engine for orchestrating multi-step tasks that require sequential execution, data passing between steps, and intelligent planning.

## Architecture

### Core Components

#### 1. WorkflowState
Tracks the complete state of a workflow execution:
- **workflow_id**: Unique identifier
- **query**: Original user query
- **status**: Current workflow status (CREATED, PLANNING, EXECUTING, COMPLETED, FAILED)
- **steps**: List of WorkflowStep objects
- **intermediate_data**: Key-value store for data passing between steps
- **final_result**: Synthesized final answer
- **timestamps**: Created, started, and completed times

#### 2. WorkflowStep
Represents a single step in the workflow:
- **step_id**: Step number
- **description**: What this step does
- **tool_name**: Tool to execute (optional)
- **tool_params**: Parameters for the tool
- **status**: PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED
- **result**: Execution result
- **depends_on**: List of step IDs this step depends on
- **timestamps**: Started and completed times

#### 3. WorkflowExecutor
Main orchestration engine with these phases:

```python
1. Analyze Task → Understand requirements
2. Create Plan → Generate step-by-step execution plan
3. Execute Steps → Run each step sequentially
4. Store Intermediate Data → Pass data between steps
5. Generate Final Answer → Synthesize results
```

## Execution Flow

```
User Query
    ↓
WorkflowExecutor.execute_workflow()
    ↓
_analyze_task()
    ├─ Identify requirements
    ├─ Determine needed tools
    └─ Store analysis in intermediate_data
    ↓
_create_plan()
    ├─ Generate step-by-step plan using LLM
    ├─ Parse plan into WorkflowStep objects
    ├─ Identify dependencies
    └─ Store execution plan
    ↓
_execute_steps()
    ├─ For each step:
    │   ├─ Check dependencies
    │   ├─ Execute tool (if specified)
    │   ├─ Store result in intermediate_data
    │   └─ Update step status
    └─ Handle errors gracefully
    ↓
_generate_final_answer()
    ├─ Collect all step results
    ├─ Synthesize using LLM
    └─ Generate comprehensive answer
    ↓
Return complete workflow state
```

## Usage

### Via Agent Endpoint (Automatic)

The agent automatically detects multi-step queries and delegates to WorkflowExecutor:

```bash
curl -X POST "http://localhost:8000/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find details from documents, call weather API, and generate recommendation",
    "session_id": "user123"
  }'
```

### Via Workflow Endpoint (Direct)

For explicit workflow execution:

```bash
curl -X POST "http://localhost:8000/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get Bitcoin price, analyze trend, and summarize findings",
    "session_id": "user123"
  }'
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "workflow_user123_1_1746000000.0",
  "response": "Based on the analysis of current Bitcoin price...",
  "workflow_state": {
    "workflow_id": "workflow_user123_1_1746000000.0",
    "query": "Get Bitcoin price, analyze trend, and summarize findings",
    "status": "completed",
    "steps": [
      {
        "step_id": 1,
        "description": "Retrieve Bitcoin price",
        "tool_name": "api_caller",
        "tool_params": {"endpoint": "crypto", "crypto_id": "bitcoin"},
        "status": "completed",
        "result": {...}
      },
      {
        "step_id": 2,
        "description": "Analyze price trend",
        "tool_name": "text_analyzer",
        "status": "completed",
        "result": {...}
      }
    ],
    "intermediate_data": {
      "task_analysis": "...",
      "execution_plan": "...",
      "step_1_result": {...},
      "step_2_result": {...}
    },
    "final_result": "Based on the analysis..."
  }
}
```

## Example Workflows

### Example 1: Document + API + Recommendation

**Query:** "Find details from uploaded contract, call weather API, and generate recommendation"

**Execution Plan:**
1. **Step 1**: Query document for contract details
   - Tool: `document_query`
   - Params: `{"query": "contract details"}`
   - Result stored in `step_1_result`

2. **Step 2**: Get weather data
   - Tool: `api_caller`
   - Params: `{"endpoint": "weather", "city": "London"}`
   - Result stored in `step_2_result`

3. **Step 3**: Generate recommendation
   - Synthesize using LLM
   - Input: Results from steps 1 and 2
   - Output: Comprehensive recommendation

**Final Answer:** "Based on the contract terms and current weather conditions, I recommend..."

### Example 2: Multi-API Data Collection

**Query:** "Get weather for New York, Bitcoin price, and create a summary report"

**Execution Plan:**
1. **Step 1**: Get New York weather
   - Tool: `api_caller`
   - Params: `{"endpoint": "weather", "city": "New York"}`

2. **Step 2**: Get Bitcoin price
   - Tool: `api_caller`
   - Params: `{"endpoint": "crypto", "crypto_id": "bitcoin"}`

3. **Step 3**: Synthesize summary
   - Combine weather and crypto data
   - Generate formatted report

### Example 3: Document Analysis Chain

**Query:** "Read contract, identify key terms, and generate compliance summary"

**Execution Plan:**
1. **Step 1**: Extract contract content
   - Tool: `document_query`
   - Params: `{"query": "contract content"}`

2. **Step 2**: Analyze key terms
   - Tool: `text_analyzer`
   - Input: Contract text from step 1
   - Params: `{"text": "$step_1_result", "analysis_type": "key_terms"}`

3. **Step 3**: Generate compliance summary
   - Synthesize analysis into summary

## Intermediate Data Passing

Data flows between steps using the `intermediate_data` dictionary:

```python
# Step 1 stores result
workflow_state.add_intermediate_data("step_1_result", {
    "contract_terms": [...],
    "pricing": {...}
})

# Step 2 can reference it
tool_params = {
    "query": "$step_1_result"  # Reference to previous step
}

# Executor resolves the reference
resolved_params = workflow_executor._resolve_parameters(
    tool_params,
    workflow_state
)
# resolved_params["query"] now contains actual data from step 1
```

## API Endpoints

### POST /workflow/execute
Execute a multi-step workflow.

**Request:**
```json
{
  "query": "Complex multi-step query",
  "session_id": "user123",
  "context": {}  // optional
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "workflow_user123_1_...",
  "response": "Final answer",
  "workflow_state": {...}
}
```

### GET /workflow/{workflow_id}
Retrieve workflow state by ID.

**Response:**
```json
{
  "workflow_id": "...",
  "status": "completed",
  "query": "...",
  "steps": [...],
  "intermediate_data": {...},
  "final_result": "...",
  "created_at": "...",
  "completed_at": "..."
}
```

### GET /workflow?session_id=user123
List all workflows, optionally filtered by session.

**Response:**
```json
{
  "count": 5,
  "workflows": [...]
}
```

## State Management

### Workflow Statuses
- **CREATED**: Workflow initialized
- **PLANNING**: Analyzing task and creating plan
- **EXECUTING**: Running steps
- **COMPLETED**: Successfully finished
- **FAILED**: Encountered error

### Step Statuses
- **PENDING**: Not started yet
- **IN_PROGRESS**: Currently executing
- **COMPLETED**: Successfully finished
- **FAILED**: Encountered error
- **SKIPPED**: Skipped due to conditions

## Logging

Every phase is logged:

```
INFO - Starting workflow execution: workflow_user123_1_...
INFO - Query: Find details from documents, call weather API...
INFO - Analyzing task for workflow workflow_user123_1_...
INFO - Task analysis completed: The user is requesting...
INFO - Creating execution plan for workflow workflow_user123_1_...
INFO - Created plan with 3 steps
INFO -   Step 1: Retrieve document content (Tool: document_query)
INFO -   Step 2: Call weather API (Tool: api_caller)
INFO -   Step 3: Generate recommendation (Tool: None)
INFO - Executing 3 steps for workflow workflow_user123_1_...
INFO - Executing step 1: Retrieve document content
INFO - Executing tool 'document_query' with params: {'query': '...'}
INFO - Stored intermediate data: step_1_result
INFO - Step 1 completed successfully
INFO - Executing step 2: Call weather API
...
INFO - Generating final answer for workflow workflow_user123_1_...
INFO - Final answer generated: Based on the analysis...
INFO - Workflow workflow_user123_1_... completed successfully
```

## Error Handling

Workflows handle errors gracefully:

1. **Step Failure**: 
   - Step marked as FAILED
   - Error stored in step.error
   - Execution continues with remaining steps
   - Final answer notes the failure

2. **Workflow Failure**:
   - Workflow marked as FAILED
   - Error stored in workflow_state.error
   - Partial results still available
   - Completed steps retain their results

3. **Tool Not Found**:
   - Exception raised
   - Workflow fails with descriptive error

## Testing

Run the test suite:

```bash
python test_workflow.py
```

Tests include:
- Document + API + Recommendation workflow
- Multi-API data collection
- Document analysis chains
- State retrieval
- Error handling

## Benefits

✅ **Automatic Planning**: LLM creates execution plans  
✅ **Data Passing**: Seamless data flow between steps  
✅ **State Tracking**: Complete visibility into execution  
✅ **Error Recovery**: Graceful handling of failures  
✅ **Flexible**: Supports any combination of tools  
✅ **Logged**: Comprehensive logging for debugging  
✅ **Queryable**: Retrieve workflow state anytime  

## Integration with Agent

The WorkflowExecutor integrates seamlessly with AgentController:

```python
# In AgentController
if decision.is_multi_step and decision.use_tool:
    # Delegate to WorkflowExecutor
    result = await workflow_executor.execute_workflow(
        query=query,
        session_id=session_id,
        context={"initial_decision": decision}
    )
```

Users don't need to choose - the agent automatically:
1. Detects multi-step queries
2. Delegates to WorkflowExecutor
3. Returns comprehensive results

## Future Enhancements

- [ ] Parallel step execution (for independent steps)
- [ ] Conditional branching (if-else logic)
- [ ] Loop support (iterate over data)
- [ ] Sub-workflows (nested workflows)
- [ ] Workflow templates (reusable patterns)
- [ ] Rollback/retry mechanisms
- [ ] Performance optimization (caching)
- [ ] Workflow visualization (diagrams)
