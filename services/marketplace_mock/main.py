from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Marketplace Mock")

class PayRequest(BaseModel):
    tokenId: str
    amount: int

DETAIL = {"1": {"id": "1", "name": "ACME Corp", "description": "A company"}}

@app.get('/company/basic')
async def get_basic(keyword: str = ''):
    data = [
        {"id": cid, "name": info["name"]}
        for cid, info in DETAIL.items()
        if keyword.lower() in info["name"].lower()
    ]
    return {"data": data}

@app.get('/company/detail')
async def get_detail(id: str, x_payment_token: str = Header(None)):
    if not x_payment_token:
        raise HTTPException(status_code=402, detail={"price": 10})
    return DETAIL.get(id)

@app.post('/pay')
async def pay(req: PayRequest):
    return {"success": True}
