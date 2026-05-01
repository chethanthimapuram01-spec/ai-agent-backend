# Workflow Trace Logging System

## Overview

The Workflow Trace Logger provides comprehensive execution tracking for workflow tasks with persistent SQLite storage. It records every step of workflow execution including inputs, outputs, execution times, and errors.

## Architecture

### Core Components

#### 1. WorkflowTrace (Data Model)

Represents a single trace entry with complete execution details:

```python
@dataclass
class WorkflowTrace:
    task_id: str              # Unique workflow identifier
    session_id: str           # User session identifier
    step_number: int          # Sequential step number
    selected_tool: str        # Tool used (if any)
    input_data: Dict          # Input parameters
    output_data: Dict         # Execution result
    status: TraceStatus       # PENDING, IN_PROGRESS, COMPLETED, FAILED
    execution_time_ms: float  # Execution time in milliseconds
    error_message: str        # Error details (if failed)
    timestamp: str            # ISO timestamp
    metadata: Dict            # Additional metadata
```

#### 2. TraceLogger

SQLite-based storage and retrieval system:

**Features:**
- Persistent database storage (`traces.db`)
- Automatic table creation and indexing
- Step-by-step execution tracking
- Performance monitoring
- Error tracking and debugging
- Query by task_id, session_id, or timestamp

#### 3. Database Schema

```sql
CREATE TABLE workflow_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    selected_tool TEXT,
    input_data TEXT NOT NULL,       -- JSON
    output_data TEXT,                -- JSON
    status TEXT NOT NULL,
    execution_time_ms REAL,
    error_message TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT,                   -- JSON
    UNIQUE(task_id, step_number)
);

-- Indexes for fast queries
CREATE INDEX idx_task_id ON workflow_traces(task_id);
CREATE INDEX idx_session_id ON workflow_traces(session_id);
CREATE INDEX idx_timestamp ON workflow_traces(timestamp);
```

## Integration

### Automatic Tracing in Workflow Executor

Traces are automatically logged during workflow execution:

```python
# Before step execution
trace_logger.log_trace(WorkflowTrace(
    task_id=workflow_id,
    session_id=session_id,
    step_number=step_id,
    selected_tool=tool_name,
    input_data={"description": "...", "params": {...}},
    output_data=None,
    status=TraceStatus.IN_PROGRESS
))

# After step execution
trace_logger.log_trace(WorkflowTrace(
    task_id=workflow_id,
    session_id=session_id,
    step_number=step_id,
    selected_tool=tool_name,
    input_data=input_data,
    output_data=result,
    status=TraceStatus.COMPLETED,
    execution_time_ms=125.43
))
```

## API Endpoints

### GET /workflow-trace/{task_id}

Get complete trace history for a workflow task.

**Response:**
```json
{
  "task_id": "workflow_user123_1_1746000000.0",
  "trace_count": 3,
  "traces": [
    {
      "task_id": "workflow_user123_1_1746000000.0",
      "session_id": "user123",
      "step_number": 1,
      "selected_tool": "document_query",
      "input_data": {
        "description": "Retrieve document content",
        "tool_params": {"query": "contract details"}
      },
      "output_data": {
        "success": true,
        "result": {"answer": "..."}
      },
      "status": "completed",
      "execution_time_ms": 245.67,
      "error_message": null,
      "timestamp": "2026-05-02T10:00:00Z",
      "metadata": {}
    },
    {
      "step_number": 2,
      "selected_tool": "api_caller",
      "status": "completed",
      "execution_time_ms": 523.12,
      ...
    },
    {
      "step_number": 3,
      "selected_tool": null,
      "status": "completed",
      "execution_time_ms": 89.45,
      ...
    }
  ]
}
```

### GET /workflow-trace/{task_id}/summary

Get execution summary with statistics.

**Response:**
```json
{
  "task_id": "workflow_user123_1_1746000000.0",
  "session_id": "user123",
  "total_steps": 3,
  "completed_steps": 3,
  "failed_steps": 0,
  "pending_steps": 0,
  "total_execution_time_ms": 858.24,
  "tools_used": ["document_query", "api_caller"],
  "status": "completed",
  "started_at": "2026-05-02T10:00:00Z",
  "last_update": "2026-05-02T10:00:01Z"
}
```

### GET /workflow-traces/session/{session_id}

Get all workflow traces for a session.

**Query Parameters:**
- `limit` (optional): Maximum traces to return (default: 100, max: 1000)

**Response:**
```json
{
  "session_id": "user123",
  "trace_count": 15,
  "traces": [...]
}
```

### GET /workflow-traces/recent

Get recent traces across all workflows.

**Query Parameters:**
- `limit` (optional): Maximum traces to return (default: 100, max: 1000)

**Response:**
```json
{
  "trace_count": 50,
  "traces": [...]
}
```

### DELETE /workflow-trace/{task_id}

Delete all traces for a specific task.

**Response:**
```json
{
  "message": "Traces for task 'workflow_user123_1_...' deleted successfully"
}
```

### POST /workflow-traces/clear

Clear all workflow traces (use with caution!).

**Response:**
```json
{
  "message": "All workflow traces cleared successfully"
}
```

## Usage Examples

### Example 1: Workflow Execution with Tracing

```python
# Execute workflow (tracing is automatic)
result = await workflow_executor.execute_workflow(
    query="Get weather and analyze it",
    session_id="user123"
)

workflow_id = result["workflow_id"]

# Retrieve traces
traces = trace_logger.get_task_traces(workflow_id)

for trace in traces:
    print(f"Step {trace['step_number']}: {trace['selected_tool']}")
    print(f"  Time: {trace['execution_time_ms']}ms")
    print(f"  Status: {trace['status']}")
```

### Example 2: Via API

```bash
# Execute workflow
curl -X POST "http://localhost:8000/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get Bitcoin price and analyze trend",
    "session_id": "user123"
  }'

# Get workflow_id from response, then retrieve traces
curl -X GET "http://localhost:8000/workflow-trace/workflow_user123_1_1746000000.0"
```

### Example 3: Debugging Failed Workflow

```bash
# Get trace for failed workflow
curl -X GET "http://localhost:8000/workflow-trace/workflow_user456_2_1746000100.0"

# Response shows which step failed:
{
  "traces": [
    {
      "step_number": 1,
      "status": "completed",
      "execution_time_ms": 123.45
    },
    {
      "step_number": 2,
      "status": "failed",
      "execution_time_ms": 45.67,
      "error_message": "Tool 'api_caller' execution failed: Connection timeout",
      "selected_tool": "api_caller",
      "input_data": {"endpoint": "weather", "city": "London"}
    }
  ]
}
```

## Trace Information

Each trace entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique workflow identifier |
| `session_id` | string | User session ID |
| `step_number` | integer | Sequential step number (1, 2, 3...) |
| `selected_tool` | string | Tool used for this step (null if no tool) |
| `input_data` | object | Step description and parameters |
| `output_data` | object | Tool execution result (null if pending/failed) |
| `status` | string | pending, in_progress, completed, failed, skipped |
| `execution_time_ms` | float | Execution time in milliseconds |
| `error_message` | string | Error details if step failed |
| `timestamp` | string | ISO 8601 timestamp |
| `metadata` | object | Additional metadata |

## Performance Monitoring

### Execution Time Tracking

Traces include precise execution times:

```python
summary = trace_logger.get_task_summary(workflow_id)

print(f"Total execution time: {summary['total_execution_time_ms']}ms")
print(f"Average per step: {summary['total_execution_time_ms'] / summary['total_steps']}ms")
```

### Identifying Bottlenecks

```python
traces = trace_logger.get_task_traces(workflow_id)

# Find slowest step
slowest = max(traces, key=lambda t: t['execution_time_ms'] or 0)
print(f"Slowest step: {slowest['step_number']} - {slowest['execution_time_ms']}ms")
print(f"Tool: {slowest['selected_tool']}")
```

## Debugging Use Cases

### 1. Failed Workflow Investigation

```bash
GET /workflow-trace/workflow_xyz_123
# Shows exactly which step failed and why
```

### 2. Performance Analysis

```bash
GET /workflow-trace/workflow_xyz_123/summary
# Shows total time and per-step breakdown
```

### 3. Tool Usage Audit

```bash
GET /workflow-traces/session/user123
# Shows all tools used in session
```

### 4. Recent Activity Monitoring

```bash
GET /workflow-traces/recent?limit=50
# Shows last 50 workflow steps across all users
```

## Benefits

✅ **Complete Audit Trail** - Every step recorded with full details  
✅ **Performance Monitoring** - Execution times tracked precisely  
✅ **Error Debugging** - Failed steps with error messages  
✅ **SQLite Storage** - Persistent, queryable database  
✅ **API Access** - RESTful endpoints for retrieval  
✅ **Automatic Logging** - No manual intervention needed  
✅ **Indexed Queries** - Fast retrieval by task, session, or time  

## Storage and Maintenance

### Database Location

Default: `./traces.db` in the application root directory.

### Database Size Management

```python
# Clear old traces
trace_logger.delete_task_traces("old_workflow_id")

# Clear all traces (use sparingly)
trace_logger.clear_all_traces()
```

### Backup

```bash
# Backup trace database
cp traces.db traces_backup_$(date +%Y%m%d).db
```

## Testing

Run the test suite:

```bash
python test_trace_logger.py
```

Tests demonstrate:
- Automatic trace logging during workflow execution
- Trace retrieval by task_id and session_id
- Task summary generation
- API response formats
- Performance characteristics

## Future Enhancements

- [ ] Trace aggregation and analytics
- [ ] Visualization dashboard
- [ ] Export to JSON/CSV
- [ ] Trace retention policies
- [ ] Real-time trace streaming
- [ ] Performance alerts and notifications
- [ ] Trace comparison between workflows
