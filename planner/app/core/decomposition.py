"""
Planner — Task Decomposition

Decomposes natural-language requests into discrete PlanStep objects.
Each step maps to exactly one specialist. The decomposer is deterministic
and works without any external LLM, API, or model.

Architecture:
  1. detect_capabilities()        — identifies what is needed
  2. assign_specialists()         — maps capabilities to specialist IDs
  3. decompose() (this module)    — builds PlanStep objects for each specialist

Memory / research flags are determined here based on detected signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.capability_detection import detect_capabilities, CAPABILITY_KEYWORDS
from app.core.specialist_assignment import assign_specialists, SpecialistAssignment
from app.models.plan import PlanStep, ExecutionMode, FailurePolicy, StepStatus


# ---------------------------------------------------------------------------
# Specialist metadata — titles, descriptions, capabilities, outputs
# ---------------------------------------------------------------------------

SPECIALIST_META: dict[str, dict] = {
    "web_development": {
        "title": "Frontend / UI Development",
        "description_template": "Implement the frontend and user interface components including {caps}.",
        "required_capabilities": ["frontend_development", "ui_implementation", "responsive_design"],
        "expected_inputs": ["Design specifications", "API contracts"],
        "expected_outputs": [
            "UI components source code",
            "Responsive layout implementation",
            "Component structure documentation",
        ],
    },
    "backend": {
        "title": "Backend / Server-side Development",
        "description_template": "Implement backend services and REST API endpoints for {caps}.",
        "required_capabilities": ["server_side_apis", "business_logic", "data_processing"],
        "expected_inputs": ["Database schema", "API design specification"],
        "expected_outputs": [
            "API endpoint implementations",
            "Request/response contract definitions",
            "Server application code",
        ],
    },
    "database": {
        "title": "Database Design and Implementation",
        "description_template": "Design and implement the database schema and data layer for {caps}.",
        "required_capabilities": ["database_schema", "sql_queries", "data_modeling"],
        "expected_inputs": ["Data requirements", "Entity relationships"],
        "expected_outputs": [
            "Database schema (DDL)",
            "Migration scripts",
            "Entity relationship diagram",
        ],
    },
    "api_integration": {
        "title": "Third-party API Integration",
        "description_template": "Integrate external services and third-party APIs for {caps}.",
        "required_capabilities": ["rest_api_integration", "external_service_integration", "error_handling"],
        "expected_inputs": ["API credentials specification", "Integration requirements"],
        "expected_outputs": [
            "API client implementation",
            "Authentication header construction",
            "Error handling and retry logic",
        ],
    },
    "security": {
        "title": "Security Implementation and Audit",
        "description_template": "Implement security measures and conduct security review for {caps}.",
        "required_capabilities": ["security_review", "authentication_implementation", "vulnerability_assessment"],
        "expected_inputs": ["Application architecture", "Security requirements"],
        "expected_outputs": [
            "Security audit report",
            "Authentication implementation",
            "Authorization rules",
        ],
    },
    "testing": {
        "title": "Testing and Quality Assurance",
        "description_template": "Create comprehensive test suite covering {caps}.",
        "required_capabilities": ["unit_testing", "integration_testing", "test_coverage"],
        "expected_inputs": ["Implementation artifacts", "Acceptance criteria"],
        "expected_outputs": [
            "Test suite source code",
            "Test coverage report",
            "Test execution results",
        ],
    },
    "devops": {
        "title": "DevOps, Deployment and Infrastructure",
        "description_template": "Configure deployment infrastructure and CI/CD pipeline for {caps}.",
        "required_capabilities": ["docker", "ci_cd", "deployment_configuration"],
        "expected_inputs": ["Application source", "Environment requirements"],
        "expected_outputs": [
            "Dockerfile and Docker Compose configuration",
            "CI/CD pipeline definition",
            "Deployment runbook",
        ],
    },
    "ai_ml": {
        "title": "AI / ML Integration",
        "description_template": "Design and implement AI/ML components including {caps}.",
        "required_capabilities": ["rag_embedding_integration", "model_integration", "vector_search"],
        "expected_inputs": ["Data sources", "Model requirements"],
        "expected_outputs": [
            "ML pipeline implementation",
            "Embedding and vector store configuration",
            "Inference integration code",
        ],
    },
    "research": {
        "title": "Research and Documentation Discovery",
        "description_template": "Research and retrieve authoritative documentation for {caps}.",
        "required_capabilities": ["external_research", "source_discovery", "evidence_validation"],
        "expected_inputs": ["Research queries", "Topic specifications"],
        "expected_outputs": [
            "Validated research evidence",
            "Authoritative source URLs",
            "Summarised findings",
        ],
    },
    "image_generation": {
        "title": "Image and Visual Asset Generation",
        "description_template": "Generate required visual assets and images for {caps}.",
        "required_capabilities": ["image_generation", "visual_asset_creation"],
        "expected_inputs": ["Visual design brief", "Brand guidelines"],
        "expected_outputs": [
            "Generated image artifacts",
            "Visual asset files",
        ],
    },
}

# Default capabilities for when no explicit cap matches a specialist
DEFAULT_SPECIALIST_CAPS: dict[str, list[str]] = {
    s: meta["required_capabilities"] for s, meta in SPECIALIST_META.items()
}


def _needs_memory(user_request: str, capabilities: list[str]) -> bool:
    """Heuristic: does this request reference existing project context?"""
    memory_signals = CAPABILITY_KEYWORDS.get("memory", [])
    text = user_request.lower()
    return any(sig in text for sig in memory_signals)


def _needs_research(capabilities: list[str]) -> bool:
    """Return True when research or external_docs capability is detected."""
    return "research" in capabilities or "external_docs" in capabilities


def _build_step_id(specialist_id: str, index: int) -> str:
    """Generate a stable, readable step ID."""
    return f"step-{index:02d}-{specialist_id}"


def _build_description(specialist_id: str, caps: list[str]) -> str:
    meta = SPECIALIST_META.get(specialist_id, {})
    template = meta.get("description_template", f"Execute {specialist_id} tasks.")
    cap_str = ", ".join(caps) if caps else specialist_id.replace("_", " ")
    return template.format(caps=cap_str)


def decompose(user_request: str) -> list[PlanStep]:
    """
    Decompose a natural-language request into an ordered list of PlanStep objects.

    Steps:
    1. Detect capabilities from the request text.
    2. Assign capabilities to specialists.
    3. Build a PlanStep for each specialist assignment.
    4. Set memory/research flags.
    5. Assign draft dependency structure (topological ordering done later).

    Returns a list with no cross-step dependency IDs yet
    (dependency_graph.py computes them).
    """
    capabilities = detect_capabilities(user_request)
    assignments: list[SpecialistAssignment] = assign_specialists(capabilities)

    memory_required = _needs_memory(user_request, capabilities)
    research_required = _needs_research(capabilities)

    # Natural dependency ordering for known specialists
    DEPENDENCY_ORDER = [
        "research",
        "database",
        "backend",
        "api_integration",
        "security",
        "web_development",
        "ai_ml",
        "image_generation",
        "testing",
        "devops",
    ]

    # Sort assignments by dependency order (specialists not in list go last)
    def _order_key(a: SpecialistAssignment) -> int:
        try:
            return DEPENDENCY_ORDER.index(a.specialist_id)
        except ValueError:
            return len(DEPENDENCY_ORDER)

    sorted_assignments = sorted(assignments, key=_order_key)

    steps: list[PlanStep] = []
    for idx, assignment in enumerate(sorted_assignments, start=1):
        meta = SPECIALIST_META.get(assignment.specialist_id, {})
        step_id = _build_step_id(assignment.specialist_id, idx)

        # Research steps require external research flag; memory steps set flag
        step_research = research_required and assignment.specialist_id == "research"
        step_memory = memory_required

        step = PlanStep(
            step_id=step_id,
            title=meta.get("title", assignment.specialist_id.replace("_", " ").title()),
            description=_build_description(assignment.specialist_id, assignment.capabilities),
            specialist_id=assignment.specialist_id,
            required_capabilities=assignment.capabilities or meta.get("required_capabilities", []),
            dependencies=[],  # Populated by dependency_graph.py
            execution_mode=ExecutionMode.SEQUENTIAL,  # Refined by execution_strategy.py
            memory_required=step_memory,
            research_required=step_research,
            expected_inputs=meta.get("expected_inputs", []),
            expected_outputs=meta.get("expected_outputs", []),
            verification_criteria=[],  # Populated by verification.py
            failure_policy=FailurePolicy(),
            status=StepStatus.PENDING,
        )
        steps.append(step)

    return steps
