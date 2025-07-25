"""Agent Orchestrator service.

TODO (security):
- replace in-memory token store with Hashicorp Vault
- add JWT auth middleware
- enforce mTLS between internal services
"""
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
import os
import httpx

app = FastAPI(title="Agent Orchestrator")

class TaskRequest(BaseModel):
    theme: str
    budget: int
    voice_id: str

class TaskResponse(BaseModel):
    task_id: str

# In-memory tasks storage for demo purposes
TASKS = {}

@app.post("/tasks", response_model=TaskResponse)
async def create_task(req: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = req.dict()
    background_tasks.add_task(run_workflow, task_id)
    return TaskResponse(task_id=task_id)

def run_workflow(task_id: str, marketplace_client: httpx.Client | None = None, payment_client: httpx.Client | None = None):
    """Simple demo workflow calling Marketplace API with payment."""
    marketplace_url = os.getenv("MARKETPLACE_URL", "http://localhost:8002")
    payment_url = os.getenv("PAYMENT_MANAGER_URL", "http://localhost:8001")
    task = TASKS.get(task_id)
    if not task:
        return
    theme = task["theme"]
    detail_path = "/company/detail?id=1"
    if marketplace_client is None:
        marketplace_client = httpx.Client(base_url=marketplace_url)
    if payment_client is None:
        payment_client = httpx.Client(base_url=payment_url)
    r = marketplace_client.get(detail_path)
    if r.status_code == 402:
        price = r.json().get("price", 0)
        token_resp = payment_client.post("/token", json={"budget": price, "voice_id": task["voice_id"]})
        token_id = token_resp.json()["token_id"]
        marketplace_client.post("/pay", json={"tokenId": token_id, "amount": price})
        r = marketplace_client.get(detail_path, headers={"x-payment-token": token_id})
    TASKS[task_id]["report"] = f"## {theme}\n\n{r.text}"
