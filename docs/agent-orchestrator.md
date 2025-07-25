# Agent Orchestrator Service

## Overview

The Agent Orchestrator is the central coordination service that manages research workflows. It receives user requests, orchestrates the research process, manages payment flows, and generates final reports.

## Service Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ User Request│───▶│ Task Manager │───▶│ Workflow    │
└─────────────┘    └──────────────┘    │ Engine      │
                                       └─────────────┘
                                              │
                    ┌─────────────┐           │
                    │ LLM Core    │◀──────────┘
                    └─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Payment     │  │ Marketplace │  │ Report      │
│ Manager     │  │ API         │  │ Builder     │
└─────────────┘  └─────────────┘  └─────────────┘
```

## API Reference

### POST /tasks

Creates and executes a research task with automated payment handling.

#### Request

**URL:** `POST /tasks`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "theme": "string",      // Required: Research topic or question
  "budget": 100,          // Required: Maximum spending limit (integer)
  "voice_id": "string"    // Required: Voice authentication identifier
}
```

#### Response

**Success (200):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "theme"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### Examples

**Basic Request:**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "Tesla Inc financial performance 2023",
    "budget": 50,
    "voice_id": "user_voice_123"
  }'
```

**Response:**
```json
{
  "task_id": "abc-123-def-456"
}
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

response = client.post("/tasks", json={
    "theme": "AI market trends in healthcare",
    "budget": 75,
    "voice_id": "voice_medical_researcher"
})

task_id = response.json()["task_id"]
print(f"Task created: {task_id}")
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/tasks', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    theme: 'Blockchain adoption in finance',
    budget: 100,
    voice_id: 'voice_fintech_analyst'
  })
});

const data = await response.json();
console.log('Task ID:', data.task_id);
```

## Workflow Engine

### Research Process

The Agent Orchestrator follows this automated workflow:

1. **Task Validation**
   - Validates input parameters
   - Generates unique task ID
   - Stores task in memory

2. **Background Processing**
   - Initiates async background task
   - Calls workflow engine with task parameters

3. **Data Discovery**
   - Queries marketplace for basic company information
   - Identifies relevant data sources

4. **Payment Flow**
   - Detects HTTP 402 (Payment Required) responses
   - Requests payment token from Payment Manager
   - Processes payment via Marketplace API
   - Retries data request with valid token

5. **Report Generation**
   - Aggregates collected data
   - Generates Markdown-formatted report
   - Stores final report in task storage

### Workflow Configuration

```python
# Environment Variables
MARKETPLACE_URL = "http://localhost:8002"  # Marketplace API endpoint
PAYMENT_MANAGER_URL = "http://localhost:8001"  # Payment service endpoint

# Timeouts
HTTP_TIMEOUT = 30  # seconds
WORKFLOW_TIMEOUT = 300  # seconds

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
```

## Core Components

### TaskRequest Model

```python
from pydantic import BaseModel, validator

class TaskRequest(BaseModel):
    theme: str
    budget: int
    voice_id: str
    
    @validator('budget')
    def budget_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Budget must be positive')
        return v
    
    @validator('theme')
    def theme_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Theme cannot be empty')
        return v.strip()
```

### TaskResponse Model

```python
class TaskResponse(BaseModel):
    task_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
```

### Workflow Runner

```python
def run_workflow(task_id: str, 
                marketplace_client: httpx.Client = None,
                payment_client: httpx.Client = None):
    """
    Execute the complete research workflow for a given task.
    
    Args:
        task_id: Unique identifier for the task
        marketplace_client: Optional HTTP client for marketplace
        payment_client: Optional HTTP client for payment manager
        
    Returns:
        None (updates task storage with results)
        
    Raises:
        WorkflowError: If workflow execution fails
        PaymentError: If payment processing fails
        DataError: If data retrieval fails
    """
```

## Error Handling

### Error Types

```python
class WorkflowError(Exception):
    """Base exception for workflow errors"""
    pass

class PaymentError(WorkflowError):
    """Payment processing failed"""
    pass

class DataError(WorkflowError):
    """Data retrieval failed"""
    pass

class AuthenticationError(WorkflowError):
    """Voice authentication failed"""
    pass
```

### Error Response Format

```json
{
  "error": "WorkflowError",
  "message": "Failed to process payment",
  "task_id": "abc-123-def",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration Points

### Payment Manager Integration

```python
# Request payment token
token_response = payment_client.post("/token", json={
    "budget": task["budget"],
    "voice_id": task["voice_id"]
})
token_id = token_response.json()["token_id"]
```

### Marketplace Integration

```python
# Attempt data access
response = marketplace_client.get("/company/detail?id=1")

if response.status_code == 402:
    # Payment required
    price = response.json()["price"]
    
    # Process payment
    payment_response = marketplace_client.post("/pay", json={
        "tokenId": token_id,
        "amount": price
    })
    
    # Retry with token
    response = marketplace_client.get(
        "/company/detail?id=1",
        headers={"x-payment-token": token_id}
    )
```

## Performance Considerations

### Async Processing

All workflows run asynchronously to prevent blocking the API:

```python
@app.post("/tasks")
async def create_task(req: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = req.dict()
    
    # Non-blocking background execution
    background_tasks.add_task(run_workflow, task_id)
    
    return TaskResponse(task_id=task_id)
```

### Memory Management

Current implementation uses in-memory storage for development:

```python
# Development: In-memory storage
TASKS = {}

# Production recommendation: Redis or database
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

### Scaling Considerations

For production deployment:

1. **Horizontal Scaling**: Deploy multiple instances behind load balancer
2. **Task Queue**: Use Celery or RQ for distributed task processing
3. **State Management**: Replace in-memory storage with Redis/PostgreSQL
4. **Circuit Breakers**: Implement failure isolation for external services

## Monitoring

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics

Key metrics to monitor:

- Task creation rate
- Workflow completion rate
- Average workflow duration
- Payment success rate
- Error rates by type

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log structured data
logger.info("Task created", extra={
    "task_id": task_id,
    "theme": req.theme,
    "budget": req.budget
})
```

## Testing

### Unit Tests

```python
def test_create_task():
    response = client.post("/tasks", json={
        "theme": "Test research",
        "budget": 50,
        "voice_id": "test_voice"
    })
    assert response.status_code == 200
    assert "task_id" in response.json()
```

### Integration Tests

```python
def test_full_workflow():
    # Create task
    response = client.post("/tasks", json={
        "theme": "Integration test",
        "budget": 100,
        "voice_id": "test_voice"
    })
    task_id = response.json()["task_id"]
    
    # Execute workflow synchronously for testing
    run_workflow(task_id, marketplace_client, payment_client)
    
    # Verify results
    assert TASKS[task_id]["report"] is not None
```

## Security

### Current Limitations

- No authentication required
- In-memory token storage
- Plain HTTP communication
- No rate limiting

### Production Security Requirements

1. **Authentication**: JWT tokens for API access
2. **Authorization**: Role-based access control
3. **Encryption**: HTTPS for all communication
4. **Voice Verification**: Integration with KYC systems
5. **Audit Logging**: Complete audit trail for all operations

### Secure Configuration Example

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Verify JWT token
    if not validate_jwt(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return decode_jwt(token)

@app.post("/tasks")
async def create_task(req: TaskRequest, user=Depends(verify_token)):
    # Authenticated endpoint
    pass
```