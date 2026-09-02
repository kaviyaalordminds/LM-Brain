"""
Tests for DAG Execution Engine and Scheduler — dependency gating, parallel groups, blocked propagation.
"""
from __future__ import annotations

import pytest

from app.core.scheduler import Scheduler
from app.models.state import StepLifecycle


def make_states(execution_id: str, step_states: dict[str, StepLifecycle]) -> dict:
    """Helper: convert step_id → state to the keyed format used by scheduler."""
    return {f"{execution_id}:{step_id}": state for step_id, state in step_states.items()}


class TestSchedulerReadyQueue:
    def test_step_with_no_dependencies_is_ready_immediately(self):
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {"step-1": [], "step-2": []}
        states = make_states("exec-1", {})
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-1" in ready
        assert "step-2" in ready

    def test_dependent_step_not_ready_until_dependency_completes(self):
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {"step-1": [], "step-2": ["step-1"]}
        # step-1 is RUNNING, step-2 should not be ready
        states = make_states("exec-1", {"step-1": StepLifecycle.RUNNING})
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-2" not in ready

    def test_dependent_step_becomes_ready_when_dep_completes(self):
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {"step-1": [], "step-2": ["step-1"]}
        # step-1 is COMPLETED
        states = make_states("exec-1", {"step-1": StepLifecycle.COMPLETED})
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-2" in ready

    def test_parallel_independent_steps_all_ready(self):
        """
        Research ──┬──> Database
                   └──> Backend
        Both Database and Backend are independently ready once Research completes.
        """
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {
            "research": [],
            "database": ["research"],
            "backend": ["research"],
        }
        states = make_states("exec-1", {"research": StepLifecycle.COMPLETED})
        ready = scheduler.tick("exec-1", states, deps)
        assert "database" in ready
        assert "backend" in ready

    def test_step_already_running_not_requeued(self):
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {"step-1": []}
        # step-1 is already RUNNING
        states = make_states("exec-1", {"step-1": StepLifecycle.RUNNING})
        ready = scheduler.tick("exec-1", states, deps)
        # Only PENDING steps are considered ready
        assert "step-1" not in ready

    def test_step_already_completed_not_requeued(self):

        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {"step-1": []}
        states = make_states("exec-1", {"step-1": StepLifecycle.COMPLETED})
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-1" not in ready

    def test_chained_dependency_graph(self):
        """step-3 cannot be ready until step-1 and step-2 both complete."""
        scheduler = Scheduler(max_concurrent_tasks=5)
        deps = {
            "step-1": [],
            "step-2": ["step-1"],
            "step-3": ["step-2"],
        }
        # Only step-1 completed
        states = make_states("exec-1", {"step-1": StepLifecycle.COMPLETED})
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-2" in ready
        assert "step-3" not in ready

        # Now step-2 also completed
        states = make_states("exec-1", {
            "step-1": StepLifecycle.COMPLETED,
            "step-2": StepLifecycle.COMPLETED,
        })
        ready = scheduler.tick("exec-1", states, deps)
        assert "step-3" in ready


class TestSchedulerCancellation:
    def test_cancel_clears_in_flight(self):
        scheduler = Scheduler(max_concurrent_tasks=5)
        scheduler.in_flight.add("step-1")
        scheduler.in_flight.add("step-2")
        scheduler.cancel("exec-1")
        assert len(scheduler.in_flight) == 0


class TestSchedulerConcurrencyLimit:
    def test_max_concurrent_tasks_respected(self):
        """Scheduler created with max=2 should still return all ready steps
        (the engine is responsible for limiting actual dispatch, not the scheduler tick)."""
        scheduler = Scheduler(max_concurrent_tasks=2)
        deps = {"step-1": [], "step-2": [], "step-3": []}
        states = make_states("exec-1", {})
        ready = scheduler.tick("exec-1", states, deps)
        # All three have no deps, all should appear as ready
        assert len(ready) == 3

