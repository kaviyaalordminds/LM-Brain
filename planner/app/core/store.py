"""
Planner — In-Memory Plan Store

Thread-safe in-memory store for Plan objects.
Supports create, get, update, exists, and list operations.
Uses a clean abstract interface so persistent storage (e.g. SQLite, PostgreSQL)
can be swapped in later without modifying caller code.
"""
from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Sequence

from app.models.plan import Plan


class BasePlanStore(ABC):
    """Abstract interface for plan storage."""

    @abstractmethod
    def create(self, plan: Plan) -> Plan:
        """Store a new plan. Raises ValueError if plan_id already exists."""

    @abstractmethod
    def get(self, plan_id: str) -> Plan | None:
        """Retrieve a plan by ID. Returns None if not found."""

    @abstractmethod
    def update(self, plan: Plan) -> Plan:
        """Update an existing plan. Raises KeyError if plan_id not found."""

    @abstractmethod
    def exists(self, plan_id: str) -> bool:
        """Check whether a plan with plan_id exists."""

    @abstractmethod
    def list_all(self, limit: int = 100) -> Sequence[Plan]:
        """List recently stored plans."""


class InMemoryPlanStore(BasePlanStore):
    """
    Thread-safe in-memory plan store.
    Suitable for development, testing, and initial standalone deployment.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._plans: dict[str, Plan] = {}

    def create(self, plan: Plan) -> Plan:
        with self._lock:
            if plan.plan_id in self._plans:
                raise ValueError(f"Plan with ID '{plan.plan_id}' already exists.")
            self._plans[plan.plan_id] = plan
            return plan

    def get(self, plan_id: str) -> Plan | None:
        with self._lock:
            return self._plans.get(plan_id)

    def update(self, plan: Plan) -> Plan:
        with self._lock:
            if plan.plan_id not in self._plans:
                raise KeyError(f"Plan with ID '{plan.plan_id}' not found.")
            self._plans[plan.plan_id] = plan
            return plan

    def exists(self, plan_id: str) -> bool:
        with self._lock:
            return plan_id in self._plans

    def list_all(self, limit: int = 100) -> Sequence[Plan]:
        with self._lock:
            return list(self._plans.values())[:limit]

    def clear(self) -> None:
        """Clear all stored plans (useful in test teardown)."""
        with self._lock:
            self._plans.clear()
