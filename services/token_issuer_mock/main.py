"""Token Issuer mock service.

TODO (security):
- add JWT auth middleware
- enforce mTLS between internal services
"""
from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI(title="Token Issuer Mock")

class TokenResponse(BaseModel):
    token_id: str
    expire_in: int

@app.get('/token', response_model=TokenResponse)
async def issue_token(app_id: str, app_secret: str):
    # TODO: verify app_id & app_secret
    return TokenResponse(token_id=str(uuid.uuid4()), expire_in=3600)
