"""
Tests for FastAPI HTTP Endpoints in app.api.routes.planning.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestPlanAPI:
    def test_health_check(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "planner"
        assert "version" in data

    def test_create_plan_valid(self, client: TestClient):
        payload = {
            "requestId": "req-api-001",
            "userRequest": "Build an e-commerce website with React frontend, REST backend, and PostgreSQL database",
            "context": {},
            "constraints": {},
            "expectedOutput": {},
        }
        response = client.post("/api/v1/plans", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["planId"].startswith("plan-")
        assert data["requestId"] == "req-api-001"
        assert data["status"] == "READY"
        assert len(data["steps"]) >= 3
        assert "executionOrder" in data
        assert "parallelGroups" in data
        assert "globalVerificationCriteria" in data

    def test_create_plan_empty_request_rejected(self, client: TestClient):
        payload = {
            "requestId": "req-api-bad",
            "userRequest": "",
        }
        response = client.post("/api/v1/plans", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data["errorCode"] == "INVALID_REQUEST"

    def test_create_plan_whitespace_request_rejected(self, client: TestClient):
        payload = {
            "requestId": "req-api-bad2",
            "userRequest": "    ",
        }
        response = client.post("/api/v1/plans", json=payload)
        assert response.status_code == 422

    def test_get_plan_existing(self, client: TestClient):
        # Create first
        create_res = client.post(
            "/api/v1/plans",
            json={"userRequest": "Create a React dashboard UI"},
        )
        assert create_res.status_code == 201
        plan_id = create_res.json()["planId"]

        # Retrieve
        get_res = client.get(f"/api/v1/plans/{plan_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["planId"] == plan_id
        assert data["status"] == "READY"

    def test_get_plan_not_found(self, client: TestClient):
        response = client.get("/api/v1/plans/plan-nonexistent-id-999")
        assert response.status_code == 404

    def test_validate_plan_endpoint(self, client: TestClient):
        create_res = client.post(
            "/api/v1/plans",
            json={"userRequest": "Implement secure JWT authentication in FastAPI"},
        )
        assert create_res.status_code == 201
        plan_id = create_res.json()["planId"]

        val_res = client.post(f"/api/v1/plans/{plan_id}/validate")
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["valid"] is True
        assert val_data["planId"] == plan_id
        assert val_data["errors"] == []

    def test_validate_plan_not_found(self, client: TestClient):
        response = client.post("/api/v1/plans/plan-ghost-404/validate")
        assert response.status_code == 404

    def test_get_plan_status(self, client: TestClient):
        create_res = client.post(
            "/api/v1/plans",
            json={"userRequest": "Deploy app with Docker and CI/CD pipeline"},
        )
        assert create_res.status_code == 201
        plan_id = create_res.json()["planId"]

        status_res = client.get(f"/api/v1/plans/{plan_id}/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["planId"] == plan_id
        assert status_data["status"] == "READY"
        assert status_data["stepCount"] >= 1
        assert status_data["completedSteps"] == 0

    def test_get_plan_status_not_found(self, client: TestClient):
        response = client.get("/api/v1/plans/plan-ghost-status/status")
        assert response.status_code == 404
