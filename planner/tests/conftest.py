"""
Pytest configuration and fixtures for the Planner Agent test suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure planner root is on sys.path
PLANNER_ROOT = Path(__file__).resolve().parent.parent
if str(PLANNER_ROOT) not in sys.path:
    sys.path.insert(0, str(PLANNER_ROOT))

import pytest
from fastapi.testclient import TestClient

from app.core.store import InMemoryPlanStore
from app.main import app
from app.planner import Planner


@pytest.fixture
def plan_store() -> InMemoryPlanStore:
    return InMemoryPlanStore()


@pytest.fixture
def planner(plan_store: InMemoryPlanStore) -> Planner:
    return Planner(store=plan_store)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
