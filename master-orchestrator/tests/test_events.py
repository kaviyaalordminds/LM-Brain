"""
Tests for Events system — EventType enumeration, ExecutionEvent structure, EventStore append/retrieve.
"""
from __future__ import annotations

import datetime
import uuid

import pytest

from app.models.events import EventType, ExecutionEvent
from app.persistence.event_store import InMemoryEventStore


def make_event(
    event_type: EventType = EventType.EXECUTION_CREATED,
    execution_id: str = "exec-1",
    step_id: str | None = None,
    payload: dict | None = None,
) -> ExecutionEvent:
    return ExecutionEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        execution_id=execution_id,
        step_id=step_id,
        correlation_id=execution_id,
        timestamp=datetime.datetime.utcnow().isoformat(),
        payload=payload or {},
    )


class TestEventTypes:
    def test_event_count_is_23(self):
        assert len(list(EventType)) == 23

    def test_lifecycle_events_present(self):
        lifecycle = [
            EventType.EXECUTION_CREATED, EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_FAILED, EventType.EXECUTION_CANCELLED,
            EventType.EXECUTION_PAUSED, EventType.EXECUTION_RESUMED,
        ]
        for e in lifecycle:
            assert e in EventType

    def test_step_events_present(self):
        step_events = [
            EventType.STEP_READY, EventType.STEP_QUEUED, EventType.STEP_DISPATCHED,
            EventType.STEP_STARTED, EventType.STEP_COMPLETED, EventType.STEP_FAILED,
        ]
        for e in step_events:
            assert e in EventType

    def test_verification_events_present(self):
        assert EventType.VERIFICATION_STARTED in EventType
        assert EventType.VERIFICATION_PASSED in EventType
        assert EventType.VERIFICATION_FAILED in EventType

    def test_recovery_events_present(self):
        assert EventType.RECOVERY_STARTED in EventType
        assert EventType.REPLAN_REQUESTED in EventType
        assert EventType.REPLAN_RECEIVED in EventType
        assert EventType.RETRY_SCHEDULED in EventType

    def test_memory_event_present(self):
        assert EventType.MEMORY_CONTEXT_FETCHED in EventType

    def test_artifact_event_present(self):
        assert EventType.ARTIFACT_CREATED in EventType


class TestExecutionEventStructure:
    def test_event_id_is_required(self):
        event = make_event()
        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_event_type_is_set(self):
        event = make_event(EventType.STEP_COMPLETED)
        assert event.event_type == EventType.STEP_COMPLETED

    def test_execution_id_is_set(self):
        event = make_event(execution_id="exec-99")
        assert event.execution_id == "exec-99"

    def test_optional_fields_default_none(self):
        event = make_event()
        assert event.step_id is None
        assert event.task_id is None
        assert event.attempt_id is None
        assert event.plan_id is None

    def test_step_id_can_be_set(self):
        event = make_event(step_id="step-1")
        assert event.step_id == "step-1"

    def test_payload_is_dict(self):
        event = make_event(payload={"user_request": "test", "plan_id": "plan-1"})
        assert isinstance(event.payload, dict)
        assert event.payload["user_request"] == "test"


class TestEventStore:
    def test_append_and_retrieve_events(self):
        store = InMemoryEventStore()
        event = make_event(EventType.EXECUTION_CREATED, "exec-1")
        store.append(event)
        events = store.get_events("exec-1")
        assert len(events) == 1
        assert events[0].event_type == EventType.EXECUTION_CREATED

    def test_events_filtered_by_execution_id(self):
        store = InMemoryEventStore()
        store.append(make_event(EventType.EXECUTION_CREATED, "exec-1"))
        store.append(make_event(EventType.EXECUTION_CREATED, "exec-2"))
        assert len(store.get_events("exec-1")) == 1
        assert len(store.get_events("exec-2")) == 1

    def test_multiple_events_same_execution(self):
        store = InMemoryEventStore()
        store.append(make_event(EventType.EXECUTION_CREATED, "exec-1"))
        store.append(make_event(EventType.STEP_READY, "exec-1", step_id="step-1"))
        store.append(make_event(EventType.STEP_COMPLETED, "exec-1", step_id="step-1"))
        events = store.get_events("exec-1")
        assert len(events) == 3

    def test_no_events_for_unknown_execution(self):
        store = InMemoryEventStore()
        events = store.get_events("nonexistent")
        assert events == []

    def test_event_order_preserved(self):
        store = InMemoryEventStore()
        store.append(make_event(EventType.EXECUTION_CREATED, "exec-1"))
        store.append(make_event(EventType.STEP_READY, "exec-1"))
        store.append(make_event(EventType.EXECUTION_COMPLETED, "exec-1"))
        events = store.get_events("exec-1")
        assert events[0].event_type == EventType.EXECUTION_CREATED
        assert events[-1].event_type == EventType.EXECUTION_COMPLETED

