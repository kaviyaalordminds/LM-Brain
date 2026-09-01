"""Contracts package — strongly typed task/result/artifact/event models."""
from specialist_agent.contracts.artifact import Artifact, ArtifactType
from specialist_agent.contracts.events import AgentEvent, EventType
from specialist_agent.contracts.result import TaskResult, TaskStatus, VerificationOutcome
from specialist_agent.contracts.task import TaskRequest

__all__ = [
    "Artifact",
    "ArtifactType",
    "AgentEvent",
    "EventType",
    "TaskResult",
    "TaskStatus",
    "VerificationOutcome",
    "TaskRequest",
]
