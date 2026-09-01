"""
Planner — Verification Criteria Builder

Assigns specific, actionable verification criteria to each PlanStep
based on the specialist assigned to that step.

Also builds the GlobalVerificationCriteria for the overall plan.

The Orchestrator enforces these criteria after execution.
The Planner only DEFINES them.
"""
from __future__ import annotations

from app.models.plan import PlanStep, GlobalVerificationCriteria


# ---------------------------------------------------------------------------
# Per-specialist verification criteria templates
# ---------------------------------------------------------------------------

SPECIALIST_VERIFICATION: dict[str, list[str]] = {
    "web_development": [
        "Required UI component files exist and are non-empty",
        "Component structure is valid (no missing imports or exports)",
        "Responsive layout requirements are addressed",
        "No console errors in rendered output",
        "All interactive elements have appropriate event handlers",
    ],
    "backend": [
        "API endpoint implementations exist for all specified routes",
        "Request and response contracts are valid and documented",
        "Input validation is present on all endpoints",
        "Unit tests for endpoints are present and passing",
        "Error responses follow the defined error schema",
    ],
    "database": [
        "Database schema DDL is syntactically valid",
        "All required entity relationships are defined",
        "Foreign key constraints are present and correct",
        "Migration scripts are created and reversible",
        "Indexes are defined for query-critical fields",
    ],
    "api_integration": [
        "API client implementation handles authentication headers correctly",
        "JSON response parsing is implemented and typed",
        "HTTP error codes are handled (4xx and 5xx)",
        "Retry logic is present for transient failures",
        "API credentials are not hardcoded in source code",
    ],
    "security": [
        "Security audit report is produced and non-empty",
        "Critical and high-severity findings are identified",
        "Authentication mechanism is properly implemented",
        "Authorization rules enforce least-privilege access",
        "Input sanitization is present on all user-facing inputs",
    ],
    "testing": [
        "Test suite executes without unhandled exceptions",
        "Test coverage report is generated",
        "All critical paths have at least one test case",
        "Test failure reasons are recorded and actionable",
        "No tests are skipped without documented justification",
    ],
    "devops": [
        "Dockerfile is valid and builds successfully",
        "Docker Compose configuration is syntactically correct",
        "CI/CD pipeline definition file exists and is valid",
        "Deployment configuration covers all required services",
        "Health check endpoints are configured in deployment spec",
    ],
    "ai_ml": [
        "ML pipeline implementation is complete and documented",
        "Embedding and vector store configuration is correct",
        "Inference integration code handles model errors gracefully",
        "Model output schema is validated before downstream use",
        "Retrieval pipeline returns relevant results for test queries",
    ],
    "research": [
        "External evidence items are retrieved from real sources",
        "Source URLs are preserved and accessible",
        "Evidence provenance (domain, title, retrieved_at) is recorded",
        "Evidence is not used before passing ValidationLayer",
        "Findings are documented in a retrievable format",
    ],
    "image_generation": [
        "Image artifact file exists on disk with non-zero size",
        "Artifact format matches the requested output type",
        "Artifact is NOT falsely labelled as real if model is unavailable",
        "MODEL_UNAVAILABLE is reported cleanly when no model is configured",
    ],
}

DEFAULT_VERIFICATION: list[str] = [
    "Task output artifact exists and is non-empty",
    "Task completed without unhandled exceptions",
    "Output format matches the expected output specification",
]


def assign_verification_criteria(steps: list[PlanStep]) -> list[PlanStep]:
    """
    Assign specialist-specific verification criteria to each step.
    Returns the updated steps list.
    """
    for step in steps:
        criteria = SPECIALIST_VERIFICATION.get(step.specialist_id, DEFAULT_VERIFICATION)
        step.verification_criteria = list(criteria)
    return steps


def build_global_verification(steps: list[PlanStep]) -> GlobalVerificationCriteria:
    """
    Build global verification criteria summarising the whole plan.
    """
    custom: list[str] = [
        f"Step '{s.step_id}' ({s.specialist_id}) must reach COMPLETED status"
        for s in steps
    ]
    custom.append("No step may remain in FAILED status without an approved retry")
    custom.append("All required artifacts from all steps must be present")

    return GlobalVerificationCriteria(
        all_steps_completed=True,
        no_critical_verification_failure=True,
        all_required_artifacts_present=True,
        all_mandatory_dependencies_completed=True,
        custom_criteria=custom,
    )
