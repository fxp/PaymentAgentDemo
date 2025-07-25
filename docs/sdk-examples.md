# SDK Examples & Client Libraries

## Overview

This document provides comprehensive examples for integrating with the AI Research Agent Payment System using various programming languages and frameworks. The examples demonstrate common usage patterns, error handling, and best practices.

## Python SDK

### Installation

```bash
pip install httpx pydantic
```

### Basic Client Implementation

```python
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import uuid
import time

class ResearchClientError(Exception):
    """Base exception for Research Client errors."""
    pass

class PaymentRequiredError(ResearchClientError):
    """Raised when payment is required for premium data."""
    def __init__(self, price: int):
        self.price = price
        super().__init__(f"Payment required: ${price}")

class TaskRequest(BaseModel):
    theme: str
    budget: int
    voice_id: str

class TaskResponse(BaseModel):
    task_id: str

class ResearchClient:
    """Python client for the AI Research Agent Payment System."""
    
    def __init__(self, 
                 agent_url: str = "http://localhost:8000",
                 payment_url: str = "http://localhost:8001",
                 marketplace_url: str = "http://localhost:8002",
                 timeout: int = 30):
        self.agent_url = agent_url
        self.payment_url = payment_url
        self.marketplace_url = marketplace_url
        self.timeout = timeout
        
        # Initialize HTTP clients
        self.agent_client = httpx.Client(base_url=agent_url, timeout=timeout)
        self.payment_client = httpx.Client(base_url=payment_url, timeout=timeout)
        self.marketplace_client = httpx.Client(base_url=marketplace_url, timeout=timeout)
    
    def create_research_task(self, theme: str, budget: int, voice_id: str) -> str:
        """
        Create a new research task.
        
        Args:
            theme: Research topic or question
            budget: Maximum budget for the research
            voice_id: Voice authentication identifier
            
        Returns:
            str: Task ID for tracking the research
            
        Raises:
            ResearchClientError: If task creation fails
        """
        try:
            request = TaskRequest(theme=theme, budget=budget, voice_id=voice_id)
            response = self.agent_client.post("/tasks", json=request.dict())
            response.raise_for_status()
            
            task_response = TaskResponse(**response.json())
            return task_response.task_id
            
        except httpx.HTTPStatusError as e:
            raise ResearchClientError(f"Failed to create task: {e.response.text}")
        except Exception as e:
            raise ResearchClientError(f"Network error: {str(e)}")
    
    def create_payment_token(self, budget: int, voice_id: str) -> Dict[str, Any]:
        """
        Create a payment token for purchasing premium data.
        
        Args:
            budget: Available budget for the token
            voice_id: Voice authentication identifier
            
        Returns:
            dict: Token information including token_id and expire_in
        """
        try:
            response = self.payment_client.post("/token", json={
                "budget": budget,
                "voice_id": voice_id
            })
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise ResearchClientError(f"Failed to create payment token: {e.response.text}")
    
    def get_token_balance(self, token_id: str) -> int:
        """Get remaining balance for a payment token."""
        try:
            response = self.payment_client.get(f"/balance/{token_id}")
            response.raise_for_status()
            return response.json()["balance"]
            
        except httpx.HTTPStatusError as e:
            raise ResearchClientError(f"Failed to get balance: {e.response.text}")
    
    def search_companies(self, keyword: str = "") -> List[Dict[str, str]]:
        """Search for companies using free tier access."""
        try:
            response = self.marketplace_client.get("/company/basic", params={"keyword": keyword})
            response.raise_for_status()
            return response.json()["data"]
            
        except httpx.HTTPStatusError as e:
            raise ResearchClientError(f"Failed to search companies: {e.response.text}")
    
    def get_company_detail(self, company_id: str, payment_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed company information.
        
        Args:
            company_id: Company identifier
            payment_token: Optional payment token for premium access
            
        Returns:
            dict: Company details
            
        Raises:
            PaymentRequiredError: If payment is required and no token provided
        """
        try:
            headers = {}
            if payment_token:
                headers["x-payment-token"] = payment_token
            
            response = self.marketplace_client.get(
                "/company/detail",
                params={"id": company_id},
                headers=headers
            )
            
            if response.status_code == 402:
                price_info = response.json()
                raise PaymentRequiredError(price_info["price"])
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                price_info = e.response.json()
                raise PaymentRequiredError(price_info["price"])
            raise ResearchClientError(f"Failed to get company details: {e.response.text}")
    
    def process_payment(self, token_id: str, amount: int) -> Dict[str, Any]:
        """Process payment for premium data access."""
        try:
            response = self.marketplace_client.post("/pay", json={
                "tokenId": token_id,
                "amount": amount
            })
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise ResearchClientError(f"Payment failed: {e.response.text}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close all HTTP clients."""
        self.agent_client.close()
        self.payment_client.close()
        self.marketplace_client.close()
```

### Usage Examples

```python
# Basic research task creation
def create_research_example():
    with ResearchClient() as client:
        task_id = client.create_research_task(
            theme="Tesla Inc financial analysis 2023",
            budget=100,
            voice_id="analyst_voice_001"
        )
        print(f"Research task created: {task_id}")

# Company data research with payment
def company_research_example():
    with ResearchClient() as client:
        # Search for companies
        companies = client.search_companies("Tesla")
        print(f"Found {len(companies)} companies")
        
        if companies:
            company_id = companies[0]["id"]
            
            try:
                # Try to get details (will require payment)
                details = client.get_company_detail(company_id)
                print(f"Company details: {details}")
                
            except PaymentRequiredError as e:
                print(f"Payment required: ${e.price}")
                
                # Create payment token
                token_info = client.create_payment_token(
                    budget=50,
                    voice_id="researcher_voice"
                )
                token_id = token_info["token_id"]
                
                # Process payment
                payment_result = client.process_payment(token_id, e.price)
                if payment_result["success"]:
                    print("Payment successful!")
                    
                    # Now get the details
                    details = client.get_company_detail(company_id, token_id)
                    print(f"Company details: {details}")

# Async version using httpx async client
import asyncio

class AsyncResearchClient:
    """Async version of the research client."""
    
    def __init__(self, **kwargs):
        self.agent_url = kwargs.get("agent_url", "http://localhost:8000")
        self.payment_url = kwargs.get("payment_url", "http://localhost:8001")
        self.marketplace_url = kwargs.get("marketplace_url", "http://localhost:8002")
        self.timeout = kwargs.get("timeout", 30)
    
    async def __aenter__(self):
        self.agent_client = httpx.AsyncClient(base_url=self.agent_url, timeout=self.timeout)
        self.payment_client = httpx.AsyncClient(base_url=self.payment_url, timeout=self.timeout)
        self.marketplace_client = httpx.AsyncClient(base_url=self.marketplace_url, timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        await self.agent_client.aclose()
        await self.payment_client.aclose()
        await self.marketplace_client.aclose()
    
    async def create_research_task(self, theme: str, budget: int, voice_id: str) -> str:
        response = await self.agent_client.post("/tasks", json={
            "theme": theme,
            "budget": budget,
            "voice_id": voice_id
        })
        response.raise_for_status()
        return response.json()["task_id"]

# Async usage example
async def async_research_example():
    async with AsyncResearchClient() as client:
        task_id = await client.create_research_task(
            theme="AI market analysis",
            budget=75,
            voice_id="ai_researcher"
        )
        print(f"Async task created: {task_id}")

# Run async example
# asyncio.run(async_research_example())
```

## JavaScript/Node.js SDK

### Installation

```bash
npm install axios
```

### Basic Client Implementation

```javascript
const axios = require('axios');

class ResearchClientError extends Error {
  constructor(message, statusCode = null) {
    super(message);
    this.name = 'ResearchClientError';
    this.statusCode = statusCode;
  }
}

class PaymentRequiredError extends ResearchClientError {
  constructor(price) {
    super(`Payment required: $${price}`, 402);
    this.price = price;
  }
}

class ResearchClient {
  constructor(options = {}) {
    this.agentUrl = options.agentUrl || 'http://localhost:8000';
    this.paymentUrl = options.paymentUrl || 'http://localhost:8001';
    this.marketplaceUrl = options.marketplaceUrl || 'http://localhost:8002';
    this.timeout = options.timeout || 30000;
    
    // Create axios instances
    this.agentClient = axios.create({
      baseURL: this.agentUrl,
      timeout: this.timeout
    });
    
    this.paymentClient = axios.create({
      baseURL: this.paymentUrl,
      timeout: this.timeout
    });
    
    this.marketplaceClient = axios.create({
      baseURL: this.marketplaceUrl,
      timeout: this.timeout
    });
    
    // Add response interceptors for error handling
    this._setupInterceptors();
  }
  
  _setupInterceptors() {
    const errorHandler = (error) => {
      if (error.response) {
        const { status, data } = error.response;
        if (status === 402 && data.price) {
          throw new PaymentRequiredError(data.price);
        }
        throw new ResearchClientError(
          data.detail || data.message || 'API Error',
          status
        );
      }
      throw new ResearchClientError(error.message);
    };
    
    this.agentClient.interceptors.response.use(
      response => response,
      errorHandler
    );
    
    this.paymentClient.interceptors.response.use(
      response => response,
      errorHandler
    );
    
    this.marketplaceClient.interceptors.response.use(
      response => response,
      errorHandler
    );
  }
  
  async createResearchTask(theme, budget, voiceId) {
    try {
      const response = await this.agentClient.post('/tasks', {
        theme,
        budget,
        voice_id: voiceId
      });
      
      return response.data.task_id;
    } catch (error) {
      throw new ResearchClientError(`Failed to create research task: ${error.message}`);
    }
  }
  
  async createPaymentToken(budget, voiceId) {
    try {
      const response = await this.paymentClient.post('/token', {
        budget,
        voice_id: voiceId
      });
      
      return response.data;
    } catch (error) {
      throw new ResearchClientError(`Failed to create payment token: ${error.message}`);
    }
  }
  
  async getTokenBalance(tokenId) {
    try {
      const response = await this.paymentClient.get(`/balance/${tokenId}`);
      return response.data.balance;
    } catch (error) {
      throw new ResearchClientError(`Failed to get token balance: ${error.message}`);
    }
  }
  
  async searchCompanies(keyword = '') {
    try {
      const response = await this.marketplaceClient.get('/company/basic', {
        params: { keyword }
      });
      return response.data.data;
    } catch (error) {
      throw new ResearchClientError(`Failed to search companies: ${error.message}`);
    }
  }
  
  async getCompanyDetail(companyId, paymentToken = null) {
    try {
      const headers = {};
      if (paymentToken) {
        headers['x-payment-token'] = paymentToken;
      }
      
      const response = await this.marketplaceClient.get('/company/detail', {
        params: { id: companyId },
        headers
      });
      
      return response.data;
    } catch (error) {
      if (error instanceof PaymentRequiredError) {
        throw error;
      }
      throw new ResearchClientError(`Failed to get company details: ${error.message}`);
    }
  }
  
  async processPayment(tokenId, amount) {
    try {
      const response = await this.marketplaceClient.post('/pay', {
        tokenId,
        amount
      });
      
      return response.data;
    } catch (error) {
      throw new ResearchClientError(`Payment failed: ${error.message}`);
    }
  }
}

module.exports = {
  ResearchClient,
  ResearchClientError,
  PaymentRequiredError
};
```

### Usage Examples

```javascript
const { ResearchClient, PaymentRequiredError } = require('./research-client');

// Basic research task creation
async function createResearchExample() {
  const client = new ResearchClient();
  
  try {
    const taskId = await client.createResearchTask(
      'Apple Inc market analysis',
      100,
      'analyst_voice_002'
    );
    
    console.log(`Research task created: ${taskId}`);
  } catch (error) {
    console.error('Error creating research task:', error.message);
  }
}

// Company research with payment flow
async function companyResearchExample() {
  const client = new ResearchClient();
  
  try {
    // Search for companies
    const companies = await client.searchCompanies('Apple');
    console.log(`Found ${companies.length} companies`);
    
    if (companies.length > 0) {
      const companyId = companies[0].id;
      
      try {
        // Try to get details (will require payment)
        const details = await client.getCompanyDetail(companyId);
        console.log('Company details:', details);
        
      } catch (error) {
        if (error instanceof PaymentRequiredError) {
          console.log(`Payment required: $${error.price}`);
          
          // Create payment token
          const tokenInfo = await client.createPaymentToken(
            50,
            'researcher_voice'
          );
          
          const tokenId = tokenInfo.token_id;
          
          // Process payment
          const paymentResult = await client.processPayment(tokenId, error.price);
          
          if (paymentResult.success) {
            console.log('Payment successful!');
            
            // Get the details with paid token
            const details = await client.getCompanyDetail(companyId, tokenId);
            console.log('Company details:', details);
          }
        } else {
          throw error;
        }
      }
    }
  } catch (error) {
    console.error('Error in company research:', error.message);
  }
}

// Promise-based usage with error handling
function promiseBasedExample() {
  const client = new ResearchClient();
  
  return client.searchCompanies('Tesla')
    .then(companies => {
      console.log('Found companies:', companies);
      
      if (companies.length > 0) {
        return client.getCompanyDetail(companies[0].id);
      }
      throw new Error('No companies found');
    })
    .then(details => {
      console.log('Company details:', details);
    })
    .catch(error => {
      if (error instanceof PaymentRequiredError) {
        console.log(`Payment required: $${error.price}`);
        // Handle payment flow...
      } else {
        console.error('Error:', error.message);
      }
    });
}

// ES6 Module syntax
// export { ResearchClient, ResearchClientError, PaymentRequiredError };
```

## React/Frontend Integration

### React Hook for Research Client

```jsx
import { useState, useEffect, useCallback } from 'react';

// Custom hook for research client functionality
export function useResearchClient(options = {}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [companyDetails, setCompanyDetails] = useState(null);
  
  const baseUrl = options.baseUrl || 'http://localhost:8002';
  
  const searchCompanies = useCallback(async (keyword = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${baseUrl}/company/basic?keyword=${encodeURIComponent(keyword)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setCompanies(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);
  
  const getCompanyDetail = useCallback(async (companyId, paymentToken = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (paymentToken) {
        headers['x-payment-token'] = paymentToken;
      }
      
      const response = await fetch(
        `${baseUrl}/company/detail?id=${encodeURIComponent(companyId)}`,
        { headers }
      );
      
      if (response.status === 402) {
        const priceInfo = await response.json();
        throw new PaymentRequiredError(priceInfo.price);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const details = await response.json();
      setCompanyDetails(details);
      return details;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);
  
  return {
    loading,
    error,
    companies,
    companyDetails,
    searchCompanies,
    getCompanyDetail
  };
}

// Payment Required Error class
class PaymentRequiredError extends Error {
  constructor(price) {
    super(`Payment required: $${price}`);
    this.name = 'PaymentRequiredError';
    this.price = price;
  }
}

// React component example
function CompanySearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [paymentRequired, setPaymentRequired] = useState(null);
  
  const {
    loading,
    error,
    companies,
    companyDetails,
    searchCompanies,
    getCompanyDetail
  } = useResearchClient();
  
  const handleSearch = async (e) => {
    e.preventDefault();
    await searchCompanies(searchTerm);
  };
  
  const handleCompanySelect = async (company) => {
    setSelectedCompany(company);
    setPaymentRequired(null);
    
    try {
      await getCompanyDetail(company.id);
    } catch (error) {
      if (error instanceof PaymentRequiredError) {
        setPaymentRequired(error.price);
      }
    }
  };
  
  const handlePayment = async () => {
    // Implement payment flow
    console.log(`Processing payment of $${paymentRequired}`);
    // After successful payment, retry getting company details
    if (selectedCompany) {
      await getCompanyDetail(selectedCompany.id, 'payment-token-here');
    }
  };
  
  return (
    <div className="company-search">
      <h2>Company Research</h2>
      
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search companies..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      
      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}
      
      {companies.length > 0 && (
        <div className="company-list">
          <h3>Search Results</h3>
          {companies.map(company => (
            <div
              key={company.id}
              className="company-item"
              onClick={() => handleCompanySelect(company)}
            >
              {company.name}
            </div>
          ))}
        </div>
      )}
      
      {paymentRequired && (
        <div className="payment-required">
          <h3>Premium Data Access</h3>
          <p>Detailed information requires payment of ${paymentRequired}</p>
          <button onClick={handlePayment}>
            Pay ${paymentRequired}
          </button>
        </div>
      )}
      
      {companyDetails && (
        <div className="company-details">
          <h3>{companyDetails.name}</h3>
          <p>{companyDetails.description}</p>
          {companyDetails.financial_data && (
            <div className="financial-data">
              <h4>Financial Information</h4>
              <p>Annual Revenue: ${companyDetails.financial_data.annual_revenue.toLocaleString()}</p>
              <p>Growth Rate: {companyDetails.financial_data.growth_rate}%</p>
              <p>Profit Margin: {companyDetails.financial_data.profit_margin}%</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CompanySearch;
```

## Go SDK

### Basic Implementation

```go
package researchclient

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "time"
)

type Client struct {
    AgentURL      string
    PaymentURL    string
    MarketplaceURL string
    HTTPClient    *http.Client
}

type TaskRequest struct {
    Theme   string `json:"theme"`
    Budget  int    `json:"budget"`
    VoiceID string `json:"voice_id"`
}

type TaskResponse struct {
    TaskID string `json:"task_id"`
}

type TokenRequest struct {
    Budget  int    `json:"budget"`
    VoiceID string `json:"voice_id"`
}

type TokenResponse struct {
    TokenID  string `json:"token_id"`
    ExpireIn int    `json:"expire_in"`
}

type CompanyBasic struct {
    ID   string `json:"id"`
    Name string `json:"name"`
}

type CompanyDetail struct {
    ID           string                 `json:"id"`
    Name         string                 `json:"name"`
    Description  string                 `json:"description"`
    Industry     string                 `json:"industry"`
    Founded      string                 `json:"founded"`
    Employees    string                 `json:"employees"`
    Revenue      string                 `json:"revenue"`
    Headquarters string                 `json:"headquarters"`
    Website      string                 `json:"website"`
    FinancialData map[string]interface{} `json:"financial_data"`
}

type PaymentRequiredError struct {
    Price int
}

func (e PaymentRequiredError) Error() string {
    return fmt.Sprintf("payment required: $%d", e.Price)
}

func NewClient() *Client {
    return &Client{
        AgentURL:       "http://localhost:8000",
        PaymentURL:     "http://localhost:8001",
        MarketplaceURL: "http://localhost:8002",
        HTTPClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *Client) CreateResearchTask(theme string, budget int, voiceID string) (string, error) {
    reqBody := TaskRequest{
        Theme:   theme,
        Budget:  budget,
        VoiceID: voiceID,
    }
    
    jsonData, err := json.Marshal(reqBody)
    if err != nil {
        return "", fmt.Errorf("failed to marshal request: %w", err)
    }
    
    resp, err := c.HTTPClient.Post(
        c.AgentURL+"/tasks",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return "", fmt.Errorf("failed to make request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return "", fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }
    
    var taskResp TaskResponse
    if err := json.NewDecoder(resp.Body).Decode(&taskResp); err != nil {
        return "", fmt.Errorf("failed to decode response: %w", err)
    }
    
    return taskResp.TaskID, nil
}

func (c *Client) CreatePaymentToken(budget int, voiceID string) (*TokenResponse, error) {
    reqBody := TokenRequest{
        Budget:  budget,
        VoiceID: voiceID,
    }
    
    jsonData, err := json.Marshal(reqBody)
    if err != nil {
        return nil, fmt.Errorf("failed to marshal request: %w", err)
    }
    
    resp, err := c.HTTPClient.Post(
        c.PaymentURL+"/token",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to make request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }
    
    var tokenResp TokenResponse
    if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }
    
    return &tokenResp, nil
}

func (c *Client) SearchCompanies(keyword string) ([]CompanyBasic, error) {
    reqURL := c.MarketplaceURL + "/company/basic"
    if keyword != "" {
        reqURL += "?keyword=" + url.QueryEscape(keyword)
    }
    
    resp, err := c.HTTPClient.Get(reqURL)
    if err != nil {
        return nil, fmt.Errorf("failed to make request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }
    
    var result struct {
        Data []CompanyBasic `json:"data"`
    }
    
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }
    
    return result.Data, nil
}

func (c *Client) GetCompanyDetail(companyID string, paymentToken *string) (*CompanyDetail, error) {
    reqURL := c.MarketplaceURL + "/company/detail?id=" + url.QueryEscape(companyID)
    
    req, err := http.NewRequest("GET", reqURL, nil)
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }
    
    if paymentToken != nil {
        req.Header.Set("x-payment-token", *paymentToken)
    }
    
    resp, err := c.HTTPClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("failed to make request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode == 402 {
        var priceInfo struct {
            Price int `json:"price"`
        }
        if err := json.NewDecoder(resp.Body).Decode(&priceInfo); err == nil {
            return nil, PaymentRequiredError{Price: priceInfo.Price}
        }
        return nil, PaymentRequiredError{Price: 0}
    }
    
    if resp.StatusCode != http.StatusOK {
        body, _ := io.ReadAll(resp.Body)
        return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
    }
    
    var company CompanyDetail
    if err := json.NewDecoder(resp.Body).Decode(&company); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }
    
    return &company, nil
}

// Usage example
func ExampleUsage() {
    client := NewClient()
    
    // Create research task
    taskID, err := client.CreateResearchTask(
        "Tesla Inc financial analysis",
        100,
        "analyst_voice",
    )
    if err != nil {
        fmt.Printf("Error creating task: %v\n", err)
        return
    }
    
    fmt.Printf("Task created: %s\n", taskID)
    
    // Search companies
    companies, err := client.SearchCompanies("Tesla")
    if err != nil {
        fmt.Printf("Error searching companies: %v\n", err)
        return
    }
    
    fmt.Printf("Found %d companies\n", len(companies))
    
    if len(companies) > 0 {
        // Try to get company details
        company := companies[0]
        details, err := client.GetCompanyDetail(company.ID, nil)
        
        if paymentErr, ok := err.(PaymentRequiredError); ok {
            fmt.Printf("Payment required: $%d\n", paymentErr.Price)
            
            // Create payment token and retry...
            tokenResp, err := client.CreatePaymentToken(50, "researcher_voice")
            if err != nil {
                fmt.Printf("Error creating payment token: %v\n", err)
                return
            }
            
            // Now get details with payment token
            details, err = client.GetCompanyDetail(company.ID, &tokenResp.TokenID)
        }
        
        if err != nil {
            fmt.Printf("Error getting company details: %v\n", err)
            return
        }
        
        fmt.Printf("Company: %s - %s\n", details.Name, details.Description)
    }
}
```

## CLI Tool Examples

### Python CLI

```python
#!/usr/bin/env python3
"""
Research Agent CLI Tool
"""
import click
import json
from research_client import ResearchClient, PaymentRequiredError

@click.group()
@click.option('--agent-url', default='http://localhost:8000', help='Agent Orchestrator URL')
@click.option('--payment-url', default='http://localhost:8001', help='Payment Manager URL')
@click.option('--marketplace-url', default='http://localhost:8002', help='Marketplace API URL')
@click.pass_context
def cli(ctx, agent_url, payment_url, marketplace_url):
    """AI Research Agent CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = ResearchClient(
        agent_url=agent_url,
        payment_url=payment_url,
        marketplace_url=marketplace_url
    )

@cli.command()
@click.argument('theme')
@click.option('--budget', '-b', type=int, default=100, help='Research budget')
@click.option('--voice-id', '-v', required=True, help='Voice authentication ID')
@click.pass_context
def research(ctx, theme, budget, voice_id):
    """Create a new research task"""
    client = ctx.obj['client']
    
    try:
        with client:
            task_id = client.create_research_task(theme, budget, voice_id)
            click.echo(f"✅ Research task created: {task_id}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@cli.command()
@click.argument('keyword', required=False)
@click.pass_context
def search(ctx, keyword):
    """Search for companies"""
    client = ctx.obj['client']
    
    try:
        with client:
            companies = client.search_companies(keyword or "")
            
            if companies:
                click.echo(f"Found {len(companies)} companies:")
                for company in companies:
                    click.echo(f"  {company['id']}: {company['name']}")
            else:
                click.echo("No companies found")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@cli.command()
@click.argument('company_id')
@click.option('--pay/--no-pay', default=False, help='Automatically pay if required')
@click.option('--voice-id', '-v', help='Voice ID for payment')
@click.pass_context
def company(ctx, company_id, pay, voice_id):
    """Get detailed company information"""
    client = ctx.obj['client']
    
    try:
        with client:
            try:
                details = client.get_company_detail(company_id)
                click.echo(json.dumps(details, indent=2))
                
            except PaymentRequiredError as e:
                if pay and voice_id:
                    click.echo(f"💳 Payment required: ${e.price}")
                    
                    # Create payment token
                    token_info = client.create_payment_token(e.price + 10, voice_id)
                    token_id = token_info['token_id']
                    
                    # Process payment
                    payment_result = client.process_payment(token_id, e.price)
                    
                    if payment_result['success']:
                        click.echo("✅ Payment successful!")
                        
                        # Get details with paid token
                        details = client.get_company_detail(company_id, token_id)
                        click.echo(json.dumps(details, indent=2))
                    else:
                        click.echo("❌ Payment failed", err=True)
                else:
                    click.echo(f"💳 Payment required: ${e.price}")
                    click.echo("Use --pay --voice-id <voice_id> to automatically pay")
                    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

if __name__ == '__main__':
    cli()
```

### Usage Examples

```bash
# Install the CLI tool
pip install click

# Create a research task
python research_cli.py research "Tesla financial analysis" --budget 100 --voice-id analyst_001

# Search for companies
python research_cli.py search Tesla

# Get company details with automatic payment
python research_cli.py company 1 --pay --voice-id researcher_voice

# Use custom service URLs
python research_cli.py --agent-url http://prod-agent:8000 search Apple
```

## Best Practices

### Error Handling

```python
# Comprehensive error handling example
def robust_research_workflow():
    client = ResearchClient()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            with client:
                # Search for companies
                companies = client.search_companies("OpenAI")
                
                if not companies:
                    print("No companies found")
                    return
                
                company_id = companies[0]["id"]
                
                # Try to get details
                try:
                    details = client.get_company_detail(company_id)
                    print(f"Successfully retrieved details for {details['name']}")
                    return details
                    
                except PaymentRequiredError as e:
                    print(f"Payment required: ${e.price}")
                    
                    # Create payment token with buffer
                    token_info = client.create_payment_token(
                        budget=e.price + 20,  # Add buffer
                        voice_id="research_user"
                    )
                    
                    # Process payment
                    payment_result = client.process_payment(
                        token_info["token_id"],
                        e.price
                    )
                    
                    if payment_result["success"]:
                        # Retry with payment token
                        details = client.get_company_detail(
                            company_id,
                            token_info["token_id"]
                        )
                        print(f"Successfully retrieved paid details for {details['name']}")
                        return details
                    else:
                        raise Exception("Payment failed")
                        
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print("Max retries exceeded")
                raise
            
            # Exponential backoff
            time.sleep(2 ** attempt)
```

### Configuration Management

```python
# Configuration class for different environments
import os
from dataclasses import dataclass

@dataclass
class ResearchConfig:
    agent_url: str
    payment_url: str
    marketplace_url: str
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls):
        return cls(
            agent_url=os.getenv('RESEARCH_AGENT_URL', 'http://localhost:8000'),
            payment_url=os.getenv('RESEARCH_PAYMENT_URL', 'http://localhost:8001'),
            marketplace_url=os.getenv('RESEARCH_MARKETPLACE_URL', 'http://localhost:8002'),
            timeout=int(os.getenv('RESEARCH_TIMEOUT', '30')),
            max_retries=int(os.getenv('RESEARCH_MAX_RETRIES', '3'))
        )
    
    @classmethod
    def development(cls):
        return cls(
            agent_url='http://localhost:8000',
            payment_url='http://localhost:8001',
            marketplace_url='http://localhost:8002'
        )
    
    @classmethod
    def production(cls):
        return cls(
            agent_url='https://agent.company.com',
            payment_url='https://payment.company.com',
            marketplace_url='https://marketplace.company.com',
            timeout=60,
            max_retries=5
        )

# Usage
config = ResearchConfig.from_env()
client = ResearchClient(
    agent_url=config.agent_url,
    payment_url=config.payment_url,
    marketplace_url=config.marketplace_url,
    timeout=config.timeout
)
```

### Logging and Monitoring

```python
import logging
import time
from functools import wraps

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def log_api_calls(func):
    """Decorator to log API calls with timing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__} with args={args[1:]} kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {duration:.2f}s: {e}")
            raise
    
    return wrapper

# Enhanced client with logging
class LoggingResearchClient(ResearchClient):
    @log_api_calls
    def create_research_task(self, theme, budget, voice_id):
        return super().create_research_task(theme, budget, voice_id)
    
    @log_api_calls
    def search_companies(self, keyword=""):
        return super().search_companies(keyword)
    
    @log_api_calls
    def get_company_detail(self, company_id, payment_token=None):
        return super().get_company_detail(company_id, payment_token)
```