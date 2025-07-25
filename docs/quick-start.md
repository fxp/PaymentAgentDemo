# Quick Start Guide

## Overview

This guide will help you get the AI Research Agent Payment System up and running in minutes. Follow these steps to set up the complete system, run your first research task, and understand the payment workflow.

## Prerequisites

- **Docker & Docker Compose**: For running services
- **Python 3.8+**: For client examples
- **Node.js 16+**: For JavaScript examples
- **Git**: For cloning the repository

## System Components

The system consists of 5 microservices:
- **Agent Orchestrator** (Port 8000): Main workflow coordination
- **Payment Manager** (Port 8001): Token management and budget control
- **Marketplace API** (Port 8002): Data provider with tiered access
- **Token Issuer Mock** (Port 8003): UnionPay token simulation
- **Marketplace Mock**: Alternative marketplace implementation

Plus supporting services:
- **PostgreSQL** (Port 5432): Database
- **Redis** (Port 6379): Caching

## Step 1: Environment Setup

### Clone the Repository

```bash
git clone <repository-url>
cd ai-research-agent-payment-system
```

### Start All Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                     IMAGE                          STATUS
agent-orchestrator       research-agent-orchestrator    Up
payment-manager          research-payment-manager       Up
marketplace-api          research-marketplace-mock      Up
token-issuer-mock        research-token-issuer-mock     Up
postgres                 postgres:15-alpine             Up
redis                    redis:7-alpine                 Up
```

### Verify Service Health

```bash
# Check all services are responding
curl http://localhost:8000/docs  # Agent Orchestrator OpenAPI
curl http://localhost:8001/docs  # Payment Manager OpenAPI
curl http://localhost:8002/company/basic  # Marketplace API
curl http://localhost:8003/docs  # Token Issuer OpenAPI
```

## Step 2: Your First Research Task

### Using cURL (Quick Test)

Create a research task that will automatically handle the payment workflow:

```bash
# Create a research task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "Tesla Inc financial analysis 2023",
    "budget": 100,
    "voice_id": "analyst_voice_001"
  }'

# Response: {"task_id": "abc-123-def-456"}
```

This single request triggers the complete workflow:
1. Task validation and creation
2. Background research initiation
3. Marketplace data access attempt
4. Automatic payment token creation
5. Payment processing
6. Premium data retrieval
7. Report generation

### Manual Step-by-Step Workflow

For better understanding, let's walk through each step manually:

#### 1. Search for Companies (Free Tier)

```bash
curl "http://localhost:8002/company/basic?keyword=Tesla"
```

Response:
```json
{
  "data": [
    {"id": "1", "name": "ACME Corp"}
  ]
}
```

#### 2. Try to Access Premium Data

```bash
curl "http://localhost:8002/company/detail?id=1"
```

Response (HTTP 402):
```json
{
  "price": 10,
  "message": "Payment required for detailed company information",
  "currency": "USD"
}
```

#### 3. Create Payment Token

```bash
curl -X POST http://localhost:8001/token \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 50,
    "voice_id": "researcher_voice"
  }'
```

Response:
```json
{
  "token_id": "def-456-ghi-789",
  "expire_in": 3600
}
```

#### 4. Process Payment

```bash
curl -X POST http://localhost:8002/pay \
  -H "Content-Type: application/json" \
  -d '{
    "tokenId": "def-456-ghi-789",
    "amount": 10
  }'
```

Response:
```json
{
  "success": true
}
```

#### 5. Access Premium Data

```bash
curl -H "x-payment-token: def-456-ghi-789" \
  "http://localhost:8002/company/detail?id=1"
```

Response:
```json
{
  "id": "1",
  "name": "ACME Corp",
  "description": "A technology company",
  "financial_data": {
    "annual_revenue": 75000000,
    "growth_rate": 15.5,
    "profit_margin": 12.3
  }
}
```

## Step 3: Using Client Libraries

### Python Client Example

Create a file `research_example.py`:

```python
import httpx
from typing import Optional, Dict, Any

class ResearchClient:
    def __init__(self):
        self.agent_url = "http://localhost:8000"
        self.payment_url = "http://localhost:8001"
        self.marketplace_url = "http://localhost:8002"
        
    def create_research_task(self, theme: str, budget: int, voice_id: str) -> str:
        with httpx.Client(base_url=self.agent_url) as client:
            response = client.post("/tasks", json={
                "theme": theme,
                "budget": budget,
                "voice_id": voice_id
            })
            response.raise_for_status()
            return response.json()["task_id"]
    
    def search_companies(self, keyword: str = ""):
        with httpx.Client(base_url=self.marketplace_url) as client:
            response = client.get("/company/basic", params={"keyword": keyword})
            response.raise_for_status()
            return response.json()["data"]

# Usage
if __name__ == "__main__":
    client = ResearchClient()
    
    # Create research task
    task_id = client.create_research_task(
        theme="AI market analysis",
        budget=75,
        voice_id="researcher_001"
    )
    print(f"Research task created: {task_id}")
    
    # Search companies
    companies = client.search_companies("ACME")
    print(f"Found {len(companies)} companies: {companies}")
```

Run the example:
```bash
python research_example.py
```

### JavaScript/Node.js Example

Create a file `research_example.js`:

```javascript
const axios = require('axios');

class ResearchClient {
  constructor() {
    this.agentUrl = 'http://localhost:8000';
    this.paymentUrl = 'http://localhost:8001';
    this.marketplaceUrl = 'http://localhost:8002';
  }
  
  async createResearchTask(theme, budget, voiceId) {
    const response = await axios.post(`${this.agentUrl}/tasks`, {
      theme,
      budget,
      voice_id: voiceId
    });
    return response.data.task_id;
  }
  
  async searchCompanies(keyword = '') {
    const response = await axios.get(`${this.marketplaceUrl}/company/basic`, {
      params: { keyword }
    });
    return response.data.data;
  }
}

// Usage
async function main() {
  const client = new ResearchClient();
  
  try {
    // Create research task
    const taskId = await client.createResearchTask(
      'Blockchain market trends',
      100,
      'crypto_analyst'
    );
    console.log(`Research task created: ${taskId}`);
    
    // Search companies
    const companies = await client.searchCompanies('ACME');
    console.log(`Found ${companies.length} companies:`, companies);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

Install dependencies and run:
```bash
npm install axios
node research_example.js
```

## Step 4: Understanding the Payment Flow

The system implements a sophisticated payment flow that handles:

### 1. Voice Authentication
- Each request requires a `voice_id` for authentication
- In production, this would integrate with voice biometric systems
- Currently accepts any string for development

### 2. Budget Management
- Payment tokens have allocated budgets
- Expenses are deducted from the token balance
- Remaining balance can be checked at any time

### 3. Automatic Payment Processing
- When premium data is requested without payment, the API returns HTTP 402
- The Agent Orchestrator automatically handles this by:
  - Creating a payment token
  - Processing the payment
  - Retrying the data request
  - Continuing with the research workflow

### 4. Cost Transparency
- All pricing is transparent and communicated upfront
- HTTP 402 responses include the exact price required
- Payment confirmations include transaction details

## Step 5: Monitoring and Debugging

### Check Service Logs

```bash
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs agent-orchestrator
docker-compose logs payment-manager
docker-compose logs marketplace-api
```

### Health Checks

Each service provides health check endpoints:

```bash
# Agent Orchestrator health
curl http://localhost:8000/health

# Payment Manager health  
curl http://localhost:8001/health

# Marketplace API health
curl http://localhost:8002/health
```

### OpenAPI Documentation

Access interactive API documentation:

- Agent Orchestrator: http://localhost:8000/docs
- Payment Manager: http://localhost:8001/docs
- Token Issuer: http://localhost:8003/docs

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# Connect to Redis
docker-compose exec redis redis-cli
```

## Step 6: Advanced Usage

### Async Research Tasks

The Agent Orchestrator runs research tasks asynchronously. To check task status:

```python
# In a production system, you would poll for task completion
import time

def wait_for_task_completion(client, task_id, timeout=300):
    """Poll for task completion (conceptual - not implemented in current system)"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # In production, this would be a real API endpoint
        # status = client.get_task_status(task_id)
        # if status['completed']:
        #     return status['result']
        
        print(f"Task {task_id} still processing...")
        time.sleep(10)
    
    raise TimeoutError("Task did not complete within timeout")
```

### Batch Processing

Process multiple companies at once:

```python
def batch_company_research():
    client = ResearchClient()
    companies = client.search_companies("")  # Get all companies
    
    results = []
    for company in companies:
        try:
            details = client.get_company_detail(company["id"])
            results.append(details)
        except PaymentRequiredError as e:
            print(f"Skipping {company['name']} - payment required: ${e.price}")
    
    return results
```

### Custom Payment Strategies

Implement different payment strategies:

```python
class SmartPaymentClient(ResearchClient):
    def __init__(self, max_price_threshold=50):
        super().__init__()
        self.max_price_threshold = max_price_threshold
    
    def get_company_detail_smart(self, company_id, voice_id):
        try:
            return self.get_company_detail(company_id)
        except PaymentRequiredError as e:
            if e.price <= self.max_price_threshold:
                print(f"Auto-paying ${e.price} for company {company_id}")
                
                # Create token and pay
                token_info = self.create_payment_token(e.price + 10, voice_id)
                self.process_payment(token_info["token_id"], e.price)
                
                # Retry with token
                return self.get_company_detail(company_id, token_info["token_id"])
            else:
                print(f"Price ${e.price} exceeds threshold ${self.max_price_threshold}")
                raise
```

## Step 7: Production Considerations

### Environment Variables

For production deployment, set these environment variables:

```bash
# Service URLs (use HTTPS in production)
AGENT_URL=https://agent.company.com
PAYMENT_URL=https://payment.company.com
MARKETPLACE_URL=https://marketplace.company.com

# Database
DATABASE_URL=postgresql://user:pass@db.company.com:5432/research
REDIS_URL=redis://cache.company.com:6379

# Security
JWT_SECRET=your-super-secret-key
ENCRYPTION_KEY=your-fernet-encryption-key
VAULT_URL=https://vault.company.com
VAULT_TOKEN=your-vault-token

# Voice Authentication
VOICE_SERVICE_URL=https://voice.company.com
KYC_SERVICE_URL=https://kyc.company.com

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
LOG_LEVEL=INFO
```

### SSL/TLS Configuration

Enable HTTPS for all services:

```yaml
# docker-compose.prod.yml
version: '3.9'
services:
  agent-orchestrator:
    environment:
      - SSL_CERT_PATH=/certs/cert.pem
      - SSL_KEY_PATH=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

### Scaling Considerations

1. **Horizontal Scaling**: Run multiple instances behind a load balancer
2. **Database**: Use managed PostgreSQL with read replicas
3. **Caching**: Implement Redis clustering
4. **Message Queues**: Add RabbitMQ or Apache Kafka for large-scale processing

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check Docker daemon is running
docker info

# Check port conflicts
netstat -tulpn | grep :8000

# Restart services
docker-compose down
docker-compose up -d
```

#### Connection Refused Errors

```bash
# Verify service URLs in requests
curl -v http://localhost:8000/health

# Check Docker network
docker network ls
docker-compose exec agent-orchestrator ping marketplace-api
```

#### Payment Failures

```bash
# Check token balance
curl http://localhost:8001/balance/your-token-id

# Verify token exists
docker-compose logs payment-manager | grep "token created"

# Check marketplace logs
docker-compose logs marketplace-api | grep "payment"
```

#### Database Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Verify database connection
docker-compose exec postgres psql -U postgres -c "\l"

# Reset database (development only)
docker-compose down -v
docker-compose up -d
```

### Performance Tuning

#### Enable Caching

```python
# Use Redis for caching expensive operations
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def cached_company_search(keyword):
    cache_key = f"search:{keyword}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    result = client.search_companies(keyword)
    cache.setex(cache_key, 300, json.dumps(result))  # Cache for 5 minutes
    return result
```

#### Connection Pooling

```python
# Use connection pooling for better performance
import httpx

# Global clients with connection pooling
AGENT_CLIENT = httpx.Client(
    base_url="http://localhost:8000",
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

PAYMENT_CLIENT = httpx.Client(
    base_url="http://localhost:8001",
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)
```

## Next Steps

1. **Explore the API Documentation**: Visit http://localhost:8000/docs for detailed API reference
2. **Read Service Documentation**: Check `docs/agent-orchestrator.md`, `docs/payment-manager.md`, etc.
3. **SDK Examples**: See `docs/sdk-examples.md` for advanced client implementations
4. **Production Deployment**: Review security and scaling considerations in the main README
5. **Custom Integrations**: Build your own clients using the API specifications in `/proto/*.yaml`

## Support

- **Documentation**: This repository's `docs/` directory
- **API Specs**: OpenAPI specifications at `/docs` endpoints
- **Issues**: GitHub Issues for bug reports and feature requests
- **Examples**: Complete code examples in `docs/sdk-examples.md`

## Quick Commands Reference

```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart agent-orchestrator

# Clean restart (removes data)
docker-compose down -v && docker-compose up -d

# Check service health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Create research task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"theme": "Your research topic", "budget": 100, "voice_id": "your_voice"}'

# Search companies
curl "http://localhost:8002/company/basic?keyword=search_term"

# Get company details (will require payment)
curl "http://localhost:8002/company/detail?id=1"
```

You're now ready to explore the AI Research Agent Payment System! Start with the basic examples and gradually move to more advanced use cases as you become familiar with the system.