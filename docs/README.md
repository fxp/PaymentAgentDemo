# AI Research Agent Payment System - API Documentation

## Overview

This system enables AI agents to conduct deep research by autonomously acquiring payment tokens and purchasing premium data from marketplace APIs. The architecture follows an event-driven microservices pattern with REST APIs and payment integration.

## Architecture

The system consists of 5 core microservices:

1. **Agent Orchestrator** - Main workflow coordination
2. **Payment Manager** - Token management and budget control
3. **Marketplace API** - Data provider with tiered access
4. **Token Issuer Mock** - UnionPay token simulation
5. **Marketplace Mock** - Test marketplace implementation

## System Flow

```
User App → Agent Orchestrator → Payment Manager → Token Issuer
                ↓                      ↓
         Marketplace API ← Payment Token ←
```

---

## Agent Orchestrator Service

### Base URL
`http://localhost:8000`

### Endpoints

#### POST /tasks
Creates a new research task and initiates the automated workflow.

**Request Body:**
```json
{
  "theme": "string",      // Research topic/theme
  "budget": 100,          // Maximum budget in currency units
  "voice_id": "string"    // Voice authentication ID
}
```

**Response:**
```json
{
  "task_id": "uuid4-string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "ACME Corporation financial analysis",
    "budget": 100,
    "voice_id": "voice_123"
  }'
```

**Workflow:**
1. Validates request and generates unique task ID
2. Initiates background research workflow
3. Attempts to access marketplace data
4. On HTTP 402 response, acquires payment token
5. Completes purchase and retrieves premium data
6. Generates final research report

---

## Payment Manager Service

### Base URL
`http://localhost:8001`

### Endpoints

#### POST /token
Creates a payment token with specified budget and voice authentication.

**Request Body:**
```json
{
  "budget": 100,          // Available budget for token
  "voice_id": "string"    // Voice authentication identifier
}
```

**Response:**
```json
{
  "token_id": "uuid4-string",
  "expire_in": 3600       // Token expiration in seconds
}
```

**Example:**
```bash
curl -X POST http://localhost:8001/token \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 50,
    "voice_id": "voice_123"
  }'
```

#### GET /balance/{token_id}
Retrieves remaining balance for a payment token.

**Parameters:**
- `token_id` (path): The payment token identifier

**Response:**
```json
{
  "balance": 45   // Remaining balance
}
```

**Example:**
```bash
curl http://localhost:8001/balance/abc-123-def
```

---

## Marketplace API Service

### Base URL
`http://localhost:8002`

### Endpoints

#### GET /company/basic
Search for companies using basic (free) tier access.

**Query Parameters:**
- `keyword` (optional): Search term for company names

**Response:**
```json
{
  "data": [
    {
      "id": "1",
      "name": "ACME Corp"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8002/company/basic?keyword=ACME"
```

#### GET /company/detail
Retrieve detailed company information (premium tier).

**Query Parameters:**
- `id` (required): Company identifier

**Headers:**
- `x-payment-token` (optional): Payment token for premium access

**Responses:**

*Without payment token (HTTP 402):*
```json
{
  "price": 10   // Required payment amount
}
```

*With valid payment token (HTTP 200):*
```json
{
  "id": "1",
  "name": "ACME Corp",
  "description": "A technology company"
}
```

**Examples:**
```bash
# Free attempt (receives 402)
curl http://localhost:8002/company/detail?id=1

# Paid access
curl -H "x-payment-token: abc-123-def" \
  http://localhost:8002/company/detail?id=1
```

#### POST /pay
Process payment for premium data access.

**Request Body:**
```json
{
  "tokenId": "string",    // Payment token ID
  "amount": 10            // Payment amount
}
```

**Response:**
```json
{
  "success": true
}
```

**Example:**
```bash
curl -X POST http://localhost:8002/pay \
  -H "Content-Type: application/json" \
  -d '{
    "tokenId": "abc-123-def",
    "amount": 10
  }'
```

---

## Token Issuer Mock Service

### Base URL
`http://localhost:8003`

### Endpoints

#### GET /token
Issues payment tokens (simulates UnionPay API).

**Query Parameters:**
- `app_id` (required): Application identifier
- `app_secret` (required): Application secret key

**Response:**
```json
{
  "token_id": "uuid4-string",
  "expire_in": 3600
}
```

**Example:**
```bash
curl "http://localhost:8003/token?app_id=myapp&app_secret=secret123"
```

---

## Core Components

### LLMCore Class

Located in `services/agent_orchestrator/llm_core.py`

```python
class LLMCore:
    """Language model integration for research workflows."""
    
    def run_research(self, theme: str, marketplace_client) -> str:
        """
        Execute research workflow using marketplace data.
        
        Args:
            theme: Research topic or theme
            marketplace_client: HTTP client for marketplace API
            
        Returns:
            Markdown-formatted research report
        """
```

**Usage Example:**
```python
from llm_core import LLMCore
import httpx

llm = LLMCore()
client = httpx.Client(base_url="http://localhost:8002")
report = llm.run_research("AI market analysis", client)
```

---

## Data Models

### TaskRequest
```python
class TaskRequest(BaseModel):
    theme: str       # Research topic
    budget: int      # Maximum spending limit
    voice_id: str    # Voice authentication ID
```

### TaskResponse
```python
class TaskResponse(BaseModel):
    task_id: str     # Unique task identifier
```

### TokenRequest
```python
class TokenRequest(BaseModel):
    budget: int      # Available token budget
    voice_id: str    # Voice authentication ID
```

### TokenResponse
```python
class TokenResponse(BaseModel):
    token_id: str    # Unique token identifier
    expire_in: int   # Expiration time in seconds
```

### PayRequest
```python
class PayRequest(BaseModel):
    tokenId: str     # Payment token ID
    amount: int      # Payment amount
```

---

## Error Handling

### Common HTTP Status Codes

- **200**: Success
- **402**: Payment Required (marketplace premium endpoints)
- **404**: Resource not found
- **422**: Validation error
- **500**: Internal server error

### Error Response Format
```json
{
  "detail": "Error description"
}
```

---

## Security Considerations

### Current Implementation (Development)
- In-memory token storage
- No authentication middleware
- Plain HTTP communication

### Production Requirements (TODO)
- Hashicorp Vault for token storage
- JWT authentication middleware
- mTLS between internal services
- Voice ID verification against KYC databases
- PCI DSS compliance for payment flows

---

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Install Python dependencies
pip install -r requirements.txt

# Start all services
docker-compose up -d

# Verify services
curl http://localhost:8000/docs  # Agent Orchestrator OpenAPI
curl http://localhost:8001/docs  # Payment Manager OpenAPI
curl http://localhost:8002/company/basic  # Marketplace API
curl http://localhost:8003/docs  # Token Issuer OpenAPI
```

### Service Ports
- Agent Orchestrator: `8000`
- Payment Manager: `8001`
- Marketplace API: `8002`
- Token Issuer Mock: `8003`
- PostgreSQL: `5432`
- Redis: `6379`

---

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_workflow.py::test_full_flow
```

### Integration Test Flow
The test suite validates the complete workflow:
1. Creates research task via Agent Orchestrator
2. Simulates marketplace API requiring payment
3. Verifies payment token acquisition
4. Confirms successful data retrieval
5. Validates report generation

---

## Monitoring & Observability

### Recommended Stack
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry
- **Logging**: Structured JSON logs
- **Alerting**: PagerDuty integration

### Key Metrics
- Task completion rate
- Payment success rate
- API response times
- Token utilization
- Budget consumption patterns

---

## Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -n research-agent
```

### Environment Variables
- `MARKETPLACE_URL`: Marketplace API base URL
- `PAYMENT_MANAGER_URL`: Payment Manager base URL
- `TOKEN_ISSUER_URL`: Token Issuer API base URL
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

---

## API Rate Limits

| Service | Endpoint | Rate Limit |
|---------|----------|------------|
| Agent Orchestrator | POST /tasks | 10/minute |
| Payment Manager | POST /token | 100/minute |
| Marketplace | All endpoints | 1000/minute |

---

## Support & Contact

- **Documentation**: This file
- **API Specifications**: `/proto/*.yaml` files
- **Source Code**: `/services/` directory
- **Issues**: GitHub Issues
- **Security**: security@company.com