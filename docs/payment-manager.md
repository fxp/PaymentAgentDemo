# Payment Manager Service

## Overview

The Payment Manager service handles payment token creation, budget management, and voice-based authentication for research workflows. It acts as an intermediary between the Agent Orchestrator and external payment systems.

## Service Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Agent       │───▶│ Token        │───▶│ Budget      │
│ Orchestrator│    │ Manager      │    │ Control     │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Voice        │
                   │ Verification │
                   └──────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Token        │
                   │ Storage      │
                   └──────────────┘
```

## API Reference

### POST /token

Creates a new payment token with specified budget and voice authentication.

#### Request

**URL:** `POST /token`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "budget": 100,          // Required: Available budget amount (integer)
  "voice_id": "string"    // Required: Voice authentication identifier
}
```

#### Response

**Success (200):**
```json
{
  "token_id": "550e8400-e29b-41d4-a716-446655440000",
  "expire_in": 3600       // Token expiration in seconds
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "budget"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

#### Examples

**Basic Request:**
```bash
curl -X POST http://localhost:8001/token \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 50,
    "voice_id": "voice_researcher_001"
  }'
```

**Response:**
```json
{
  "token_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "expire_in": 3600
}
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8001")

response = client.post("/token", json={
    "budget": 75,
    "voice_id": "medical_researcher_voice"
})

token_data = response.json()
print(f"Token ID: {token_data['token_id']}")
print(f"Expires in: {token_data['expire_in']} seconds")
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8001/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    budget: 100,
    voice_id: 'fintech_analyst_voice'
  })
});

const tokenData = await response.json();
console.log('Token created:', tokenData.token_id);
```

### GET /balance/{token_id}

Retrieves the remaining balance for a specific payment token.

#### Request

**URL:** `GET /balance/{token_id}`

**Path Parameters:**
- `token_id` (string, required): The payment token identifier

#### Response

**Success (200):**
```json
{
  "balance": 45   // Remaining balance amount
}
```

**Token Not Found (404):**
```json
{
  "detail": "Token not found"
}
```

#### Examples

**Basic Request:**
```bash
curl http://localhost:8001/balance/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response:**
```json
{
  "balance": 25
}
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8001")
token_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

response = client.get(f"/balance/{token_id}")
balance_data = response.json()
print(f"Remaining balance: {balance_data['balance']}")
```

**JavaScript Example:**
```javascript
const tokenId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
const response = await fetch(`http://localhost:8001/balance/${tokenId}`);
const balanceData = await response.json();
console.log('Remaining balance:', balanceData.balance);
```

## Core Components

### Data Models

#### TokenRequest

```python
from pydantic import BaseModel, validator

class TokenRequest(BaseModel):
    budget: int
    voice_id: str
    
    @validator('budget')
    def budget_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Budget must be positive')
        return v
    
    @validator('voice_id')
    def voice_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Voice ID cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "budget": 100,
                "voice_id": "researcher_voice_123"
            }
        }
```

#### TokenResponse

```python
class TokenResponse(BaseModel):
    token_id: str
    expire_in: int
    
    class Config:
        schema_extra = {
            "example": {
                "token_id": "550e8400-e29b-41d4-a716-446655440000",
                "expire_in": 3600
            }
        }
```

#### BalanceResponse

```python
class BalanceResponse(BaseModel):
    balance: int
    
    @validator('balance')
    def balance_not_negative(cls, v):
        if v < 0:
            return 0  # Never return negative balance
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "balance": 45
            }
        }
```

### Token Storage

Current implementation uses in-memory storage for development:

```python
# Development: Simple dictionary storage
TOKENS = {}

def store_token(token_id: str, budget: int):
    """Store token with initial budget."""
    TOKENS[token_id] = budget

def get_balance(token_id: str) -> int:
    """Get remaining balance for token."""
    return TOKENS.get(token_id, 0)

def deduct_balance(token_id: str, amount: int) -> bool:
    """Deduct amount from token balance."""
    if token_id in TOKENS and TOKENS[token_id] >= amount:
        TOKENS[token_id] -= amount
        return True
    return False
```

### Production Token Storage

For production deployment, implement secure token storage:

```python
import hashicorp_vault
import redis
from datetime import datetime, timedelta

class SecureTokenStorage:
    def __init__(self, vault_client, redis_client):
        self.vault = vault_client
        self.redis = redis_client
    
    def store_token(self, token_id: str, budget: int, voice_id: str):
        """Store token securely with expiration."""
        token_data = {
            "budget": budget,
            "voice_id": voice_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        # Store in Vault for security
        self.vault.secrets.kv.v2.create_or_update_secret(
            path=f"tokens/{token_id}",
            secret=token_data
        )
        
        # Cache in Redis for performance
        self.redis.setex(
            f"token:{token_id}",
            3600,  # 1 hour TTL
            budget
        )
    
    def get_balance(self, token_id: str) -> int:
        """Get balance from cache or vault."""
        # Try Redis first
        cached_balance = self.redis.get(f"token:{token_id}")
        if cached_balance is not None:
            return int(cached_balance)
        
        # Fallback to Vault
        try:
            secret = self.vault.secrets.kv.v2.read_secret_version(
                path=f"tokens/{token_id}"
            )
            return secret['data']['data']['budget']
        except Exception:
            return 0
```

## Voice Authentication

### Voice ID Verification

```python
class VoiceVerificationService:
    """Integration with voice biometric systems."""
    
    def __init__(self, kaldi_endpoint: str):
        self.kaldi_endpoint = kaldi_endpoint
    
    async def verify_voice_id(self, voice_id: str) -> bool:
        """
        Verify voice ID against KYC database.
        
        Args:
            voice_id: Voice authentication identifier
            
        Returns:
            bool: True if voice ID is verified
        """
        # Integration with voice biometric service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.kaldi_endpoint}/verify",
                json={"voice_id": voice_id}
            )
            return response.json().get("verified", False)
    
    async def get_user_limits(self, voice_id: str) -> dict:
        """Get spending limits for verified user."""
        # Integration with KYC system
        return {
            "daily_limit": 1000,
            "transaction_limit": 500,
            "monthly_limit": 10000
        }
```

### Enhanced Token Creation with Voice Verification

```python
@app.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    """Create token with voice verification."""
    
    # Verify voice ID
    voice_service = VoiceVerificationService(
        os.getenv("VOICE_SERVICE_URL")
    )
    
    if not await voice_service.verify_voice_id(req.voice_id):
        raise HTTPException(
            status_code=401,
            detail="Voice authentication failed"
        )
    
    # Check user limits
    limits = await voice_service.get_user_limits(req.voice_id)
    if req.budget > limits["transaction_limit"]:
        raise HTTPException(
            status_code=400,
            detail=f"Budget exceeds transaction limit of {limits['transaction_limit']}"
        )
    
    # Create token
    token_id = str(uuid.uuid4())
    TOKENS[token_id] = req.budget
    
    return TokenResponse(token_id=token_id, expire_in=3600)
```

## Budget Management

### Budget Tracking

```python
class BudgetManager:
    """Manages budget allocation and consumption tracking."""
    
    def __init__(self, storage):
        self.storage = storage
    
    def allocate_budget(self, voice_id: str, amount: int) -> str:
        """Allocate budget and return token ID."""
        token_id = str(uuid.uuid4())
        
        budget_data = {
            "total_allocated": amount,
            "remaining": amount,
            "consumed": 0,
            "transactions": [],
            "voice_id": voice_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.storage.store_budget(token_id, budget_data)
        return token_id
    
    def consume_budget(self, token_id: str, amount: int, 
                      description: str = "") -> bool:
        """Consume budget for a transaction."""
        budget_data = self.storage.get_budget(token_id)
        
        if not budget_data or budget_data["remaining"] < amount:
            return False
        
        # Update budget
        budget_data["remaining"] -= amount
        budget_data["consumed"] += amount
        budget_data["transactions"].append({
            "amount": amount,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.storage.update_budget(token_id, budget_data)
        return True
    
    def get_budget_report(self, token_id: str) -> dict:
        """Generate budget consumption report."""
        budget_data = self.storage.get_budget(token_id)
        
        if not budget_data:
            return {"error": "Token not found"}
        
        return {
            "token_id": token_id,
            "total_allocated": budget_data["total_allocated"],
            "remaining": budget_data["remaining"],
            "consumed": budget_data["consumed"],
            "utilization_rate": budget_data["consumed"] / budget_data["total_allocated"],
            "transaction_count": len(budget_data["transactions"]),
            "last_transaction": budget_data["transactions"][-1] if budget_data["transactions"] else None
        }
```

## Error Handling

### Custom Exceptions

```python
class PaymentManagerError(Exception):
    """Base exception for Payment Manager errors."""
    pass

class InsufficientBudgetError(PaymentManagerError):
    """Raised when budget is insufficient for operation."""
    pass

class TokenNotFoundError(PaymentManagerError):
    """Raised when token is not found."""
    pass

class VoiceVerificationError(PaymentManagerError):
    """Raised when voice verification fails."""
    pass

class BudgetLimitExceededError(PaymentManagerError):
    """Raised when budget exceeds user limits."""
    pass
```

### Error Handlers

```python
@app.exception_handler(InsufficientBudgetError)
async def insufficient_budget_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": "InsufficientBudget",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(TokenNotFoundError)
async def token_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "TokenNotFound",
            "message": "Payment token not found",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Security Features

### Token Security

```python
import jwt
from cryptography.fernet import Fernet

class SecureTokenManager:
    """Secure token management with encryption and signing."""
    
    def __init__(self, encryption_key: bytes, jwt_secret: str):
        self.fernet = Fernet(encryption_key)
        self.jwt_secret = jwt_secret
    
    def create_secure_token(self, budget: int, voice_id: str) -> str:
        """Create encrypted and signed token."""
        
        # Create token payload
        payload = {
            "budget": budget,
            "voice_id": voice_id,
            "created_at": datetime.utcnow().timestamp(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).timestamp()
        }
        
        # Encrypt payload
        encrypted_payload = self.fernet.encrypt(
            json.dumps(payload).encode()
        )
        
        # Sign with JWT
        jwt_token = jwt.encode(
            {"encrypted_data": encrypted_payload.decode()},
            self.jwt_secret,
            algorithm="HS256"
        )
        
        return jwt_token
    
    def decrypt_token(self, token: str) -> dict:
        """Decrypt and verify token."""
        try:
            # Verify JWT signature
            decoded_jwt = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )
            
            # Decrypt payload
            encrypted_data = decoded_jwt["encrypted_data"].encode()
            decrypted_payload = self.fernet.decrypt(encrypted_data)
            
            payload = json.loads(decrypted_payload.decode())
            
            # Check expiration
            if datetime.fromtimestamp(payload["expires_at"]) < datetime.utcnow():
                raise TokenExpiredError("Token has expired")
            
            return payload
            
        except Exception as e:
            raise TokenValidationError(f"Token validation failed: {str(e)}")
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/token")
@limiter.limit("10/minute")  # Limit token creation to 10 per minute per IP
async def create_token(request: Request, req: TokenRequest):
    # Token creation logic
    pass
```

## Monitoring & Analytics

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
token_creation_counter = Counter(
    'payment_tokens_created_total',
    'Total number of payment tokens created',
    ['voice_id_hash']
)

budget_consumption_histogram = Histogram(
    'budget_consumption_amount',
    'Budget consumption amounts',
    buckets=[1, 5, 10, 25, 50, 100, 250, 500]
)

active_tokens_gauge = Gauge(
    'active_payment_tokens',
    'Number of active payment tokens'
)

@app.post("/token")
async def create_token(req: TokenRequest):
    # Create token logic
    token_id = str(uuid.uuid4())
    TOKENS[token_id] = req.budget
    
    # Record metrics
    voice_id_hash = hashlib.sha256(req.voice_id.encode()).hexdigest()[:8]
    token_creation_counter.labels(voice_id_hash=voice_id_hash).inc()
    active_tokens_gauge.inc()
    
    return TokenResponse(token_id=token_id, expire_in=3600)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "active_tokens": len(TOKENS),
        "total_budget": sum(TOKENS.values()),
        "dependencies": {
            "vault": await check_vault_connection(),
            "redis": await check_redis_connection(),
            "voice_service": await check_voice_service()
        }
    }

async def check_vault_connection() -> bool:
    """Check if Vault is accessible."""
    try:
        # Attempt to read a test secret
        vault_client.sys.read_health_status()
        return True
    except Exception:
        return False
```

## Testing

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_token_success():
    """Test successful token creation."""
    response = client.post("/token", json={
        "budget": 100,
        "voice_id": "test_voice"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "token_id" in data
    assert data["expire_in"] == 3600

def test_create_token_invalid_budget():
    """Test token creation with invalid budget."""
    response = client.post("/token", json={
        "budget": -10,
        "voice_id": "test_voice"
    })
    
    assert response.status_code == 422

def test_get_balance_existing_token():
    """Test balance retrieval for existing token."""
    # Create token first
    response = client.post("/token", json={
        "budget": 50,
        "voice_id": "test_voice"
    })
    token_id = response.json()["token_id"]
    
    # Get balance
    response = client.get(f"/balance/{token_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == 50

def test_get_balance_nonexistent_token():
    """Test balance retrieval for non-existent token."""
    response = client.get("/balance/nonexistent-token")
    assert response.status_code == 200
    assert response.json()["balance"] == 0
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_token_workflow_integration():
    """Test complete token workflow."""
    
    # Create token
    response = client.post("/token", json={
        "budget": 100,
        "voice_id": "integration_test_voice"
    })
    token_data = response.json()
    token_id = token_data["token_id"]
    
    # Verify initial balance
    response = client.get(f"/balance/{token_id}")
    assert response.json()["balance"] == 100
    
    # Simulate budget consumption
    budget_manager = BudgetManager(storage)
    success = budget_manager.consume_budget(token_id, 25, "Test purchase")
    assert success
    
    # Verify updated balance
    response = client.get(f"/balance/{token_id}")
    assert response.json()["balance"] == 75
```

## Deployment

### Environment Configuration

```bash
# Payment Manager Configuration
PAYMENT_MANAGER_PORT=8001
VAULT_URL=https://vault.company.com
VAULT_TOKEN=<vault-token>
REDIS_URL=redis://localhost:6379
VOICE_SERVICE_URL=https://voice.company.com
JWT_SECRET=<jwt-secret-key>
ENCRYPTION_KEY=<fernet-encryption-key>

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001 9090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Production Considerations

1. **High Availability**: Deploy multiple instances with load balancing
2. **Database**: Use PostgreSQL for persistent token storage
3. **Caching**: Implement Redis for performance
4. **Security**: Enable HTTPS and implement proper authentication
5. **Monitoring**: Set up comprehensive metrics and alerting