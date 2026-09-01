"""
Specialist Agent — Artifact Contract

Artifacts are typed outputs produced by specialist agents.
All artifact types are sub-classes of the base Artifact model.
The runtime never fabricates artifacts — all artifacts must
be backed by real production or explicitly labelled mock data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Supported artifact categories."""

    CODE = "code"
    IMAGE = "image"
    DOCUMENT = "document"
    REFERENCE = "reference"
    SCHEMA = "schema"
    CONFIG = "config"
    REPORT = "report"
    TEST_RESULT = "test_result"
    STRUCTURED = "structured"
    MOCK = "mock"  # Explicitly labels mock/test artifacts — never real production output


class Artifact(BaseModel):
    """
    Common artifact produced by any Specialist Agent.

    Fields
    ------
    artifact_id : Unique identifier.
    type        : ArtifactType enum value.
    path        : Filesystem path (for code, image, document, config).
    url         : URL (for reference artifacts).
    mime_type   : MIME type when applicable.
    content     : Inline content (short text/structured data).
    is_mock     : True if this is a test/mock artifact, never a real output.
    agent_id    : Which agent produced this artifact.
    task_id     : Task correlation.
    metadata    : Arbitrary extra metadata.
    created_at  : UTC creation timestamp.
    """

    model_config = {"populate_by_name": True}

    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType = Field(..., description="Artifact category.")
    path: str | None = Field(None, description="Filesystem path (code, image, document, config).")
    url: str | None = Field(None, description="URL (reference artifacts).")
    mime_type: str | None = Field(None, description="MIME type when applicable.")
    content: str | None = Field(None, description="Inline short content or summary.")
    is_mock: bool = Field(
        default=False,
        description=(
            "True when this artifact was produced by a mock/test implementation. "
            "NEVER set to False for mock output."
        ),
    )
    agent_id: str | None = Field(None, description="ID of the agent that produced this artifact.")
    task_id: str | None = Field(None, description="Task correlation ID.")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_real(self) -> bool:
        """Return True only if this is NOT a mock artifact."""
        return not self.is_mock


# ─────────────────────────────────────────────────────────────────────────────
# Typed factory helpers
# ─────────────────────────────────────────────────────────────────────────────


def make_code_artifact(
    path: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create a code artifact from a filesystem path."""
    return Artifact(
        type=ArtifactType.CODE,
        path=path,
        mime_type="text/plain",
        agent_id=agent_id,
        task_id=task_id,
        metadata=metadata or {},
    )


def make_image_artifact(
    path: str,
    mime_type: str = "image/png",
    agent_id: str | None = None,
    task_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create a real image artifact (must have a real path)."""
    return Artifact(
        type=ArtifactType.IMAGE,
        path=path,
        mime_type=mime_type,
        agent_id=agent_id,
        task_id=task_id,
        metadata=metadata or {},
        is_mock=False,
    )


def make_document_artifact(
    path: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create a document artifact."""
    return Artifact(
        type=ArtifactType.DOCUMENT,
        path=path,
        mime_type="text/markdown",
        agent_id=agent_id,
        task_id=task_id,
        metadata=metadata or {},
    )


def make_reference_artifact(
    url: str,
    agent_id: str | None = None,
    task_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Artifact:
    """Create a URL reference artifact (e.g. research evidence)."""
    return Artifact(
        type=ArtifactType.REFERENCE,
        url=url,
        agent_id=agent_id,
        task_id=task_id,
        metadata=metadata or {},
    )


def make_mock_artifact(
    label: str,
    agent_id: str | None = None,
    task_id: str | None = None,
) -> Artifact:
    """
    Create an explicitly-labelled mock artifact for testing.

    IMPORTANT: is_mock=True is always set — callers must not treat
    this as a real production artifact.
    """
    return Artifact(
        type=ArtifactType.MOCK,
        content=f"[MOCK ARTIFACT] {label}",
        is_mock=True,
        agent_id=agent_id,
        task_id=task_id,
        metadata={"label": label, "note": "This is a test-only artifact."},
    )
