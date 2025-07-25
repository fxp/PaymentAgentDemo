# Marketplace API Service

## Overview

The Marketplace API provides tiered access to company data and business intelligence. It implements a freemium model where basic information is freely accessible, while detailed data requires payment tokens. The service integrates with payment systems to enable seamless data monetization.

## Service Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Client      │───▶│ Rate Limiter │───▶│ Auth        │
│ Request     │    │ & Validator  │    │ Middleware  │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
                   ┌──────────────┐    ┌─────────────┐
                   │ Payment      │◀───│ API         │
                   │ Gateway      │    │ Controller  │
                   └──────────────┘    └─────────────┘
                           │                  │
                           ▼                  ▼
                   ┌──────────────┐    ┌─────────────┐
                   │ UnionPay     │    │ Data        │
                   │ Integration  │    │ Repository  │
                   └──────────────┘    └─────────────┘
```

## Data Tiers

### Free Tier
- Basic company information
- Company names and IDs
- Simple search functionality
- No authentication required

### Premium Tier
- Detailed company profiles
- Financial data
- Historical information
- Requires valid payment token

## API Reference

### GET /company/basic

Search for companies using the free tier with basic information.

#### Request

**URL:** `GET /company/basic`

**Query Parameters:**
- `keyword` (string, optional): Search term for filtering companies by name

#### Response

**Success (200):**
```json
{
  "data": [
    {
      "id": "1",
      "name": "ACME Corp"
    },
    {
      "id": "2", 
      "name": "Tech Innovations Ltd"
    }
  ]
}
```

#### Examples

**Basic Search:**
```bash
curl "http://localhost:8002/company/basic"
```

**Keyword Search:**
```bash
curl "http://localhost:8002/company/basic?keyword=ACME"
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8002")

# Search all companies
response = client.get("/company/basic")
companies = response.json()["data"]

# Search with keyword
response = client.get("/company/basic", params={"keyword": "Tech"})
filtered_companies = response.json()["data"]

print(f"Found {len(companies)} companies")
```

**JavaScript Example:**
```javascript
// Basic search
const response = await fetch('http://localhost:8002/company/basic');
const data = await response.json();
console.log('Companies:', data.data);

// Keyword search
const searchResponse = await fetch(
  'http://localhost:8002/company/basic?keyword=ACME'
);
const searchData = await searchResponse.json();
console.log('Filtered companies:', searchData.data);
```

### GET /company/detail

Retrieve detailed company information (premium tier).

#### Request

**URL:** `GET /company/detail`

**Query Parameters:**
- `id` (string, required): Company identifier

**Headers:**
- `x-payment-token` (string, optional): Payment token for premium access

#### Response

**Without Payment Token (HTTP 402):**
```json
{
  "price": 10,
  "message": "Payment required for detailed company information",
  "currency": "USD"
}
```

**With Valid Payment Token (HTTP 200):**
```json
{
  "id": "1",
  "name": "ACME Corp",
  "description": "A leading technology company specializing in AI solutions",
  "industry": "Technology",
  "founded": "2010",
  "employees": "500-1000",
  "revenue": "$50M-$100M",
  "headquarters": "San Francisco, CA",
  "website": "https://acme-corp.com",
  "financial_data": {
    "annual_revenue": 75000000,
    "growth_rate": 15.5,
    "profit_margin": 12.3
  }
}
```

**Invalid/Expired Token (HTTP 401):**
```json
{
  "detail": "Invalid or expired payment token"
}
```

#### Examples

**Free Attempt (receives 402):**
```bash
curl "http://localhost:8002/company/detail?id=1"
```

**Premium Access:**
```bash
curl -H "x-payment-token: abc-123-def-456" \
  "http://localhost:8002/company/detail?id=1"
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8002")

# Attempt without token (will get 402)
response = client.get("/company/detail", params={"id": "1"})
if response.status_code == 402:
    price_info = response.json()
    print(f"Payment required: ${price_info['price']}")

# Access with payment token
headers = {"x-payment-token": "your-token-here"}
response = client.get("/company/detail", 
                     params={"id": "1"}, 
                     headers=headers)

if response.status_code == 200:
    company_data = response.json()
    print(f"Company: {company_data['name']}")
    print(f"Revenue: ${company_data['financial_data']['annual_revenue']:,}")
```

**JavaScript Example:**
```javascript
// Check price without token
let response = await fetch('http://localhost:8002/company/detail?id=1');
if (response.status === 402) {
  const priceInfo = await response.json();
  console.log(`Payment required: $${priceInfo.price}`);
}

// Access with payment token
response = await fetch('http://localhost:8002/company/detail?id=1', {
  headers: {
    'x-payment-token': 'your-token-here'
  }
});

if (response.ok) {
  const companyData = await response.json();
  console.log('Company details:', companyData);
}
```

### POST /pay

Process payment for premium data access.

#### Request

**URL:** `POST /pay`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "tokenId": "string",    // Payment token identifier
  "amount": 10            // Payment amount in USD
}
```

#### Response

**Success (200):**
```json
{
  "success": true,
  "transaction_id": "txn_abc123",
  "amount_charged": 10,
  "remaining_balance": 40,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Insufficient Balance (400):**
```json
{
  "success": false,
  "error": "InsufficientBalance",
  "message": "Token balance insufficient for this transaction",
  "required": 10,
  "available": 5
}
```

**Invalid Token (401):**
```json
{
  "success": false,
  "error": "InvalidToken",
  "message": "Payment token not found or expired"
}
```

#### Examples

**Basic Payment:**
```bash
curl -X POST http://localhost:8002/pay \
  -H "Content-Type: application/json" \
  -d '{
    "tokenId": "abc-123-def-456",
    "amount": 10
  }'
```

**Python Example:**
```python
import httpx

client = httpx.Client(base_url="http://localhost:8002")

payment_request = {
    "tokenId": "abc-123-def-456",
    "amount": 10
}

response = client.post("/pay", json=payment_request)
payment_result = response.json()

if payment_result["success"]:
    print(f"Payment successful! Transaction ID: {payment_result['transaction_id']}")
    print(f"Remaining balance: ${payment_result['remaining_balance']}")
else:
    print(f"Payment failed: {payment_result['message']}")
```

**JavaScript Example:**
```javascript
const paymentData = {
  tokenId: 'abc-123-def-456',
  amount: 10
};

const response = await fetch('http://localhost:8002/pay', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(paymentData)
});

const result = await response.json();
if (result.success) {
  console.log('Payment successful:', result.transaction_id);
} else {
  console.log('Payment failed:', result.message);
}
```

## Core Components

### Data Models

#### CompanyBasic

```javascript
// Node.js/Express model
const CompanyBasic = {
  id: String,        // Unique company identifier
  name: String       // Company display name
};
```

#### CompanyDetail

```javascript
const CompanyDetail = {
  id: String,
  name: String,
  description: String,
  industry: String,
  founded: String,
  employees: String,
  revenue: String,
  headquarters: String,
  website: String,
  financial_data: {
    annual_revenue: Number,
    growth_rate: Number,
    profit_margin: Number
  }
};
```

#### PaymentRequest

```javascript
const PaymentRequest = {
  tokenId: String,   // Payment token identifier
  amount: Number     // Payment amount (integer)
};
```

#### PaymentResponse

```javascript
const PaymentResponse = {
  success: Boolean,
  transaction_id: String,
  amount_charged: Number,
  remaining_balance: Number,
  timestamp: String
};
```

### Data Repository

```javascript
// In-memory data store for development
const COMPANIES = {
  '1': {
    id: '1',
    name: 'ACME Corp',
    description: 'A leading technology company specializing in AI solutions',
    industry: 'Technology',
    founded: '2010',
    employees: '500-1000',
    revenue: '$50M-$100M',
    headquarters: 'San Francisco, CA',
    website: 'https://acme-corp.com',
    financial_data: {
      annual_revenue: 75000000,
      growth_rate: 15.5,
      profit_margin: 12.3
    }
  },
  '2': {
    id: '2',
    name: 'Tech Innovations Ltd',
    description: 'Innovative solutions for modern businesses',
    industry: 'Technology',
    founded: '2015',
    employees: '100-250',
    revenue: '$10M-$25M',
    headquarters: 'Austin, TX',
    website: 'https://tech-innovations.com',
    financial_data: {
      annual_revenue: 18000000,
      growth_rate: 22.1,
      profit_margin: 8.7
    }
  }
};
```

### Production Data Integration

```javascript
class CompanyDataService {
  constructor(config) {
    this.database = config.database;
    this.cache = config.redisClient;
    this.externalAPIs = config.externalAPIs;
  }

  async searchCompanies(keyword = '') {
    // Check cache first
    const cacheKey = `search:${keyword}`;
    const cached = await this.cache.get(cacheKey);
    
    if (cached) {
      return JSON.parse(cached);
    }

    // Query database
    const query = `
      SELECT id, name 
      FROM companies 
      WHERE name ILIKE $1 
      ORDER BY name
    `;
    
    const results = await this.database.query(query, [`%${keyword}%`]);
    
    // Cache results for 5 minutes
    await this.cache.setex(cacheKey, 300, JSON.stringify(results.rows));
    
    return results.rows;
  }

  async getCompanyDetail(id) {
    // Check cache
    const cacheKey = `company:${id}`;
    const cached = await this.cache.get(cacheKey);
    
    if (cached) {
      return JSON.parse(cached);
    }

    // Aggregate data from multiple sources
    const [dbData, financialData, marketData] = await Promise.all([
      this.getCompanyFromDB(id),
      this.getFinancialData(id),
      this.getMarketData(id)
    ]);

    const companyDetail = {
      ...dbData,
      financial_data: financialData,
      market_data: marketData
    };

    // Cache for 1 hour
    await this.cache.setex(cacheKey, 3600, JSON.stringify(companyDetail));
    
    return companyDetail;
  }

  async getCompanyFromDB(id) {
    const query = `
      SELECT id, name, description, industry, founded, 
             employees, revenue, headquarters, website
      FROM companies 
      WHERE id = $1
    `;
    
    const result = await this.database.query(query, [id]);
    return result.rows[0];
  }

  async getFinancialData(id) {
    // Integration with financial data providers
    const response = await this.externalAPIs.financial.get(`/company/${id}`);
    return response.data;
  }

  async getMarketData(id) {
    // Integration with market data providers
    const response = await this.externalAPIs.market.get(`/company/${id}`);
    return response.data;
  }
}
```

## Payment Integration

### Token Validation

```javascript
class PaymentValidator {
  constructor(paymentManagerURL) {
    this.paymentManagerURL = paymentManagerURL;
  }

  async validateToken(tokenId) {
    try {
      const response = await fetch(
        `${this.paymentManagerURL}/balance/${tokenId}`
      );
      
      if (response.ok) {
        const data = await response.json();
        return {
          valid: true,
          balance: data.balance
        };
      }
      
      return { valid: false, balance: 0 };
    } catch (error) {
      console.error('Token validation error:', error);
      return { valid: false, balance: 0 };
    }
  }

  async processPayment(tokenId, amount) {
    try {
      const response = await fetch(
        `${this.paymentManagerURL}/pay`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tokenId, amount })
        }
      );

      if (response.ok) {
        return await response.json();
      }

      throw new Error(`Payment failed: ${response.statusText}`);
    } catch (error) {
      console.error('Payment processing error:', error);
      throw error;
    }
  }
}
```

### Enhanced Payment Middleware

```javascript
const createPaymentMiddleware = (validator) => {
  return async (req, res, next) => {
    const token = req.headers['x-payment-token'];
    
    if (!token) {
      return res.status(402).json({
        price: 10,
        message: 'Payment required for detailed company information',
        currency: 'USD'
      });
    }

    try {
      const validation = await validator.validateToken(token);
      
      if (!validation.valid) {
        return res.status(401).json({
          detail: 'Invalid or expired payment token'
        });
      }

      if (validation.balance < 10) {
        return res.status(400).json({
          success: false,
          error: 'InsufficientBalance',
          message: 'Token balance insufficient for this transaction',
          required: 10,
          available: validation.balance
        });
      }

      req.paymentToken = {
        id: token,
        balance: validation.balance
      };
      
      next();
    } catch (error) {
      console.error('Payment middleware error:', error);
      res.status(500).json({
        detail: 'Payment validation failed'
      });
    }
  };
};
```

## Error Handling

### Error Types

```javascript
class MarketplaceError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.statusCode = statusCode;
    this.name = 'MarketplaceError';
  }
}

class PaymentRequiredError extends MarketplaceError {
  constructor(price) {
    super('Payment required', 402);
    this.price = price;
    this.name = 'PaymentRequiredError';
  }
}

class InsufficientBalanceError extends MarketplaceError {
  constructor(required, available) {
    super('Insufficient balance', 400);
    this.required = required;
    this.available = available;
    this.name = 'InsufficientBalanceError';
  }
}

class InvalidTokenError extends MarketplaceError {
  constructor() {
    super('Invalid or expired payment token', 401);
    this.name = 'InvalidTokenError';
  }
}
```

### Error Handler Middleware

```javascript
const errorHandler = (err, req, res, next) => {
  console.error('API Error:', err);

  if (err instanceof PaymentRequiredError) {
    return res.status(402).json({
      price: err.price,
      message: err.message,
      currency: 'USD'
    });
  }

  if (err instanceof InsufficientBalanceError) {
    return res.status(400).json({
      success: false,
      error: 'InsufficientBalance',
      message: err.message,
      required: err.required,
      available: err.available
    });
  }

  if (err instanceof InvalidTokenError) {
    return res.status(401).json({
      detail: err.message
    });
  }

  // Default error response
  res.status(err.statusCode || 500).json({
    detail: err.message || 'Internal server error',
    timestamp: new Date().toISOString()
  });
};
```

## Rate Limiting

### Implementation

```javascript
const rateLimit = require('express-rate-limit');

// General rate limiting
const generalLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  message: {
    error: 'TooManyRequests',
    message: 'Rate limit exceeded. Please try again later.',
    retryAfter: 60
  }
});

// Stricter limits for premium endpoints
const premiumLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 50, // 50 requests per minute for premium endpoints
  message: {
    error: 'TooManyRequests',
    message: 'Premium endpoint rate limit exceeded.',
    retryAfter: 60
  }
});

// Payment endpoint limits
const paymentLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 20, // 20 payment requests per minute
  message: {
    error: 'TooManyRequests',
    message: 'Payment rate limit exceeded.',
    retryAfter: 60
  }
});

// Apply to routes
app.use('/company/basic', generalLimiter);
app.use('/company/detail', premiumLimiter);
app.use('/pay', paymentLimiter);
```

## Caching Strategy

### Multi-Level Caching

```javascript
class CacheManager {
  constructor(redisClient, memoryCache) {
    this.redis = redisClient;
    this.memory = memoryCache;
  }

  async get(key) {
    // Check memory cache first (fastest)
    let value = this.memory.get(key);
    if (value) {
      return value;
    }

    // Check Redis cache (fast)
    value = await this.redis.get(key);
    if (value) {
      const parsed = JSON.parse(value);
      // Store in memory for next time
      this.memory.set(key, parsed, { ttl: 60 }); // 1 minute memory cache
      return parsed;
    }

    return null;
  }

  async set(key, value, ttl = 3600) {
    // Store in both caches
    this.memory.set(key, value, { ttl: Math.min(ttl, 300) }); // Max 5 minutes in memory
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  async invalidate(pattern) {
    // Clear memory cache
    this.memory.flushAll();
    
    // Clear matching Redis keys
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}

// Usage in API routes
app.get('/company/detail', async (req, res) => {
  const { id } = req.query;
  const cacheKey = `company:detail:${id}`;
  
  // Try cache first
  let company = await cacheManager.get(cacheKey);
  
  if (!company) {
    // Fetch from data source
    company = await dataService.getCompanyDetail(id);
    
    if (company) {
      // Cache for 1 hour
      await cacheManager.set(cacheKey, company, 3600);
    }
  }
  
  res.json(company);
});
```

## Security Features

### API Key Authentication (Production)

```javascript
const apiKeyAuth = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return res.status(401).json({
      detail: 'API key required'
    });
  }

  // Validate API key against database
  if (!isValidApiKey(apiKey)) {
    return res.status(401).json({
      detail: 'Invalid API key'
    });
  }

  req.client = getClientInfo(apiKey);
  next();
};

async function isValidApiKey(apiKey) {
  const client = await db.query(
    'SELECT id FROM api_clients WHERE api_key = $1 AND active = true',
    [apiKey]
  );
  return client.rows.length > 0;
}
```

### Input Validation

```javascript
const { body, query, validationResult } = require('express-validator');

// Validation rules
const paymentValidation = [
  body('tokenId').isUUID().withMessage('Invalid token ID format'),
  body('amount').isInt({ min: 1, max: 1000 }).withMessage('Amount must be between 1 and 1000'),
];

const companyDetailValidation = [
  query('id').isAlphanumeric().withMessage('Invalid company ID format'),
];

// Validation middleware
const validateRequest = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(422).json({
      detail: 'Validation failed',
      errors: errors.array()
    });
  }
  next();
};

// Apply to routes
app.post('/pay', paymentValidation, validateRequest, handlePayment);
app.get('/company/detail', companyDetailValidation, validateRequest, getCompanyDetail);
```

## Monitoring & Analytics

### Metrics Collection

```javascript
const prometheus = require('prom-client');

// Custom metrics
const httpRequestDuration = new prometheus.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code']
});

const paymentTransactions = new prometheus.Counter({
  name: 'payment_transactions_total',
  help: 'Total number of payment transactions',
  labelNames: ['status', 'amount_range']
});

const companyDataRequests = new prometheus.Counter({
  name: 'company_data_requests_total',
  help: 'Total number of company data requests',
  labelNames: ['tier', 'company_id']
});

// Middleware to collect metrics
const metricsMiddleware = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpRequestDuration
      .labels(req.method, req.route?.path || req.path, res.statusCode)
      .observe(duration);
  });
  
  next();
};

app.use(metricsMiddleware);

// Metrics endpoint
app.get('/metrics', (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(prometheus.register.metrics());
});
```

### Health Checks

```javascript
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    dependencies: {}
  };

  try {
    // Check database connection
    await db.query('SELECT 1');
    health.dependencies.database = 'healthy';
  } catch (error) {
    health.dependencies.database = 'unhealthy';
    health.status = 'degraded';
  }

  try {
    // Check Redis connection
    await redis.ping();
    health.dependencies.redis = 'healthy';
  } catch (error) {
    health.dependencies.redis = 'unhealthy';
    health.status = 'degraded';
  }

  try {
    // Check payment manager connection
    const response = await fetch(`${PAYMENT_MANAGER_URL}/health`);
    health.dependencies.payment_manager = response.ok ? 'healthy' : 'unhealthy';
  } catch (error) {
    health.dependencies.payment_manager = 'unhealthy';
    health.status = 'degraded';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});
```

## Testing

### Unit Tests

```javascript
const request = require('supertest');
const app = require('../src/app');

describe('Marketplace API', () => {
  describe('GET /company/basic', () => {
    it('should return company list without authentication', async () => {
      const response = await request(app)
        .get('/company/basic')
        .expect(200);

      expect(response.body).toHaveProperty('data');
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should filter companies by keyword', async () => {
      const response = await request(app)
        .get('/company/basic?keyword=ACME')
        .expect(200);

      expect(response.body.data).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ name: expect.stringContaining('ACME') })
        ])
      );
    });
  });

  describe('GET /company/detail', () => {
    it('should return 402 without payment token', async () => {
      const response = await request(app)
        .get('/company/detail?id=1')
        .expect(402);

      expect(response.body).toHaveProperty('price');
      expect(response.body.price).toBeGreaterThan(0);
    });

    it('should return company details with valid token', async () => {
      const response = await request(app)
        .get('/company/detail?id=1')
        .set('x-payment-token', 'valid-token')
        .expect(200);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('name');
      expect(response.body).toHaveProperty('financial_data');
    });
  });

  describe('POST /pay', () => {
    it('should process payment successfully', async () => {
      const response = await request(app)
        .post('/pay')
        .send({
          tokenId: 'valid-token',
          amount: 10
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body).toHaveProperty('transaction_id');
    });

    it('should reject invalid token', async () => {
      const response = await request(app)
        .post('/pay')
        .send({
          tokenId: 'invalid-token',
          amount: 10
        })
        .expect(401);

      expect(response.body.success).toBe(false);
    });
  });
});
```

### Integration Tests

```javascript
describe('Payment Integration', () => {
  it('should complete full payment workflow', async () => {
    // 1. Check price without token
    const priceCheck = await request(app)
      .get('/company/detail?id=1')
      .expect(402);

    const price = priceCheck.body.price;

    // 2. Create payment token (mock)
    const tokenResponse = await request(paymentManager)
      .post('/token')
      .send({
        budget: 50,
        voice_id: 'test_voice'
      });

    const tokenId = tokenResponse.body.token_id;

    // 3. Process payment
    const paymentResponse = await request(app)
      .post('/pay')
      .send({
        tokenId: tokenId,
        amount: price
      })
      .expect(200);

    expect(paymentResponse.body.success).toBe(true);

    // 4. Access data with paid token
    const dataResponse = await request(app)
      .get('/company/detail?id=1')
      .set('x-payment-token', tokenId)
      .expect(200);

    expect(dataResponse.body).toHaveProperty('financial_data');
  });
});
```

## Deployment

### Environment Configuration

```bash
# Server Configuration
PORT=3000
NODE_ENV=production

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/marketplace
REDIS_URL=redis://localhost:6379

# External Services
PAYMENT_MANAGER_URL=http://payment-manager:8001
UNIONPAY_API_URL=https://api.unionpay.com

# Security
API_KEY_SALT=your-secret-salt
JWT_SECRET=your-jwt-secret

# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
```

### Docker Configuration

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/

# Expose ports
EXPOSE 3000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

# Start application
CMD ["node", "src/app.js"]
```

### Production Considerations

1. **Load Balancing**: Deploy behind NGINX or AWS ALB
2. **Database**: Use PostgreSQL with read replicas
3. **Caching**: Implement Redis clustering
4. **CDN**: Use CloudFront for static content
5. **Monitoring**: Integrate with DataDog or New Relic
6. **Security**: Enable WAF and DDoS protection