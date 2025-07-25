"""Payment Manager service.

TODO (security):
- replace in-memory token store with Hashicorp Vault
- add JWT auth middleware
- enforce mTLS between internal services
"""
from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI(title="Payment Manager")

class TokenRequest(BaseModel):
    budget: int
    voice_id: str

class TokenResponse(BaseModel):
    token_id: str
    expire_in: int

class BalanceResponse(BaseModel):
    balance: int

TOKENS = {}

@app.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    token_id = str(uuid.uuid4())
    TOKENS[token_id] = req.budget
    return TokenResponse(token_id=token_id, expire_in=3600)

@app.get("/balance/{token_id}", response_model=BalanceResponse)
async def get_balance(token_id: str):
    balance = TOKENS.get(token_id, 0)
    return BalanceResponse(balance=balance)
