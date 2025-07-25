import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from services.agent_orchestrator.main import app as orchestrator_app, TASKS
from services.payment_manager.main import app as payment_app
from services.token_issuer_mock.main import app as token_app
from services.marketplace_mock.main import app as marketplace_app

orchestrator_client = TestClient(orchestrator_app)
payment_client = TestClient(payment_app)
issuer_client = TestClient(token_app)
marketplace_client = TestClient(marketplace_app)


def test_full_flow(monkeypatch):
    # patch environment URLs to use local TestClient endpoints
    monkeypatch.setenv('MARKETPLACE_URL', marketplace_client.base_url)
    monkeypatch.setenv('PAYMENT_MANAGER_URL', payment_client.base_url)

    resp = orchestrator_client.post('/tasks', json={'theme': 'test', 'budget': 50, 'voice_id': 'v1'})
    assert resp.status_code == 200
    task_id = resp.json()['task_id']

    # trigger workflow synchronously for test
    from services.agent_orchestrator.main import run_workflow
    run_workflow(task_id, marketplace_client=marketplace_client, payment_client=payment_client)

    report = TASKS[task_id].get('report')
    assert report and 'ACME Corp' in report
