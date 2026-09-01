"""
Tests for Specialist Assignment and Capability Detection.
"""
from __future__ import annotations

import pytest

from app.core.capability_detection import detect_capabilities
from app.core.specialist_assignment import (
    assign_specialists,
    is_valid_specialist,
    CAPABILITY_TO_SPECIALIST,
)
from app.models.plan import KNOWN_SPECIALISTS


class TestSpecialistAssignment:
    def test_all_10_specialists_known(self):
        expected = {
            "web_development", "image_generation", "backend", "database",
            "api_integration", "security", "testing", "devops", "ai_ml", "research"
        }
        assert KNOWN_SPECIALISTS == expected
        for spec in expected:
            assert is_valid_specialist(spec) is True

    def test_invalid_specialist_rejected(self):
        assert is_valid_specialist("quantum_computing") is False
        assert is_valid_specialist("") is False
        assert is_valid_specialist("admin") is False

    def test_frontend_assigned_to_web_development(self):
        caps = ["frontend"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "web_development"
        assert assignments[0].is_known is True

    def test_backend_assigned_to_backend(self):
        caps = ["backend"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "backend"

    def test_database_assigned_to_database(self):
        caps = ["database"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "database"

    def test_api_integration_assigned_to_api_integration(self):
        caps = ["api_integration"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "api_integration"

    def test_security_assigned_to_security(self):
        caps = ["security", "authentication"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "security"

    def test_testing_assigned_to_testing(self):
        caps = ["testing"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "testing"

    def test_devops_assigned_to_devops(self):
        caps = ["docker", "cicd", "deployment"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "devops"

    def test_ai_ml_assigned_to_ai_ml(self):
        caps = ["ai_ml", "rag", "vector_database"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "ai_ml"

    def test_research_assigned_to_research(self):
        caps = ["research", "external_docs"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "research"

    def test_image_generation_assigned_to_image_generation(self):
        caps = ["image_generation"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "image_generation"

    def test_unknown_capability_fallback(self):
        caps = ["quantum_entanglement_computing"]
        assignments = assign_specialists(caps)
        assert len(assignments) == 1
        assert assignments[0].specialist_id == "research"

    def test_multiple_capabilities_grouping(self):
        caps = ["frontend", "backend", "database", "testing", "docker"]
        assignments = assign_specialists(caps)
        spec_ids = {a.specialist_id for a in assignments}
        assert spec_ids == {"web_development", "backend", "database", "testing", "devops"}


class TestCapabilityDetection:
    def test_detect_react_frontend(self):
        caps = detect_capabilities("Create a React frontend login page with Tailwind CSS")
        assert "frontend" in caps

    def test_detect_database_and_backend(self):
        caps = detect_capabilities("Build a FastAPI REST API with a PostgreSQL database schema")
        assert "backend" in caps
        assert "database" in caps

    def test_detect_docker_cicd(self):
        caps = detect_capabilities("Create a Docker container and GitHub Actions CI/CD pipeline")
        assert "docker" in caps or "cicd" in caps or "deployment" in caps

    def test_detect_rag_vector_db(self):
        caps = detect_capabilities("Build an AI application using RAG, embeddings and a vector database")
        assert "ai_ml" in caps or "rag" in caps or "vector_database" in caps

    def test_detect_image_generation(self):
        caps = detect_capabilities("Generate a hero image for the landing page")
        assert "image_generation" in caps

    def test_detect_research_documentation(self):
        caps = detect_capabilities("Find official documentation and latest security recommendations")
        assert "research" in caps or "external_docs" in caps or "security" in caps
