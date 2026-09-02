"""
Tests for Master Orchestrator API endpoints using TestClient.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_ready_endpoint(client):
    resp = client.get("/api/v1/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "dependencies" in data
    assert "planner" in data["dependencies"]

def test_create_and_query_execution_lifecycle(client):
    # 1. Post new execution
    payload = {"user_request": "Build a simple web service", "context": {}}
    resp = client.post("/api/v1/executions", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert "execution_id" in data
    exec_id = data["execution_id"]
    assert exec_id != "exec-123"  # Must be dynamically generated
    
    # 2. Get status
    status_resp = client.get(f"/api/v1/executions/{exec_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["execution_id"] == exec_id
    assert "status" in status_data

    # 3. Get full details
    detail_resp = client.get(f"/api/v1/executions/{exec_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["execution_id"] == exec_id

    # 4. Get events
    events_resp = client.get(f"/api/v1/executions/{exec_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    assert events[0]["event_type"] == "EXECUTION_CREATED"

