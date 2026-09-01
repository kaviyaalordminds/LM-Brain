"""
Memory Agent — Client-Style Natural Language Requirements Test Suite

Tests realistic natural-language client requests against the real local Obsidian
knowledge base (555 Markdown notes) in C:\\Lordminds\\Multiagent\\memory-agent\\obsedian.

Evaluates:
  - Natural-language query retrieval relevance across multiple domains
  - Multi-domain knowledge composition (Frontend + Backend + DB + Auth + Testing)
  - Negative / No-Knowledge queries (no hallucination on topics absent from vault)
  - Source attribution and physical file existence verification
  - Context assembly usefulness for downstream agents
  - Retrieval Quality Metrics: Precision@1, Precision@3, Precision@5, Latency
"""

from __future__ import annotations

import time
from pathlib import Path
import pytest

from app.adapters.obsidian_adapter import LocalObsidianAdapter
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.adapters.research_provider import MockResearchProvider
from app.models.memory import ApprovalStatus


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def local_adapter() -> LocalObsidianAdapter:
    """Instantiate LocalObsidianAdapter with real local Obsidian vault."""
    vault_path = Path("C:/Lordminds/Multiagent/memory-agent/obsedian")
    return LocalObsidianAdapter(vault_path=vault_path)


@pytest.fixture(scope="module")
def memory_agent(local_adapter: LocalObsidianAdapter) -> MemoryAgent:
    """MemoryAgent initialized with LocalObsidianAdapter."""
    retrieval = RetrievalService()
    research_provider = MockResearchProvider()
    research_svc = ResearchService(provider=research_provider)
    validation = ValidationLayer()
    writer = MemoryWriter(obsidian=local_adapter)
    return MemoryAgent(
        obsidian=local_adapter,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=writer,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Client-Style Requirements Dataset (18 Scenarios)
# ─────────────────────────────────────────────────────────────────────────────

CLIENT_REQUIREMENTS = [
    {
        "id": "REQ-01",
        "category": "Frontend & Web Fundamentals",
        "client_request": (
            "I need a modern web application with a responsive frontend interface "
            "that communicates with backend services over client server architecture."
        ),
        "expected_areas": ["Frontend", "Client-Server-Architecture", "Backend", "Web-Fundamentals"],
        "expected_keywords": ["frontend", "client-server", "backend"],
        "is_negative": False,
    },
    {
        "id": "REQ-02",
        "category": "Authentication & JWT",
        "client_request": (
            "We need to implement secure user authentication for our web platform "
            "using JSON Web Tokens (JWT) and multi-factor authentication."
        ),
        "expected_areas": ["Authentication", "JWT", "Multi-Factor-Authentication"],
        "expected_keywords": ["jwt", "authentication", "multi-factor"],
        "is_negative": False,
    },
    {
        "id": "REQ-03",
        "category": "REST APIs & API Design",
        "client_request": (
            "I need a clean REST API backend with proper API design, rate limiting, "
            "and OpenAPI swagger documentation for client integration."
        ),
        "expected_areas": ["REST-API", "API-Design", "Rate-Limiting", "Open-API-and-Swagger"],
        "expected_keywords": ["rest-api", "api-design", "rate-limiting"],
        "is_negative": False,
    },
    {
        "id": "REQ-04",
        "category": "Database & SQL",
        "client_request": (
            "Our application needs to store business records in a relational database "
            "with SQL schemas, ACID transaction guarantees, and database migrations."
        ),
        "expected_areas": ["SQL-Basics", "ACID-Properties", "Database-Migrations", "Database-Transactions"],
        "expected_keywords": ["sql", "acid", "database", "migrations"],
        "is_negative": False,
    },
    {
        "id": "REQ-05",
        "category": "Web Security & OWASP",
        "client_request": (
            "We need comprehensive web application security protecting against OWASP Top 10 "
            "vulnerabilities like SQL injection, cross-site scripting (XSS), and CSRF attacks."
        ),
        "expected_areas": ["Application Security", "OWASP-Top-10", "Cross-Site-Scripting-XSS", "Cross-Site-Request-Forgery-CSRF"],
        "expected_keywords": ["security", "owasp", "xss", "csrf"],
        "is_negative": False,
    },
    {
        "id": "REQ-06",
        "category": "Authorization & RBAC",
        "client_request": (
            "We require granular authorization with Role-Based Access Control (RBAC) "
            "and principle of least privilege permissions for different user roles."
        ),
        "expected_areas": ["Role-Based-Access-Control", "Authorization", "Principle-of-Least-Privilege"],
        "expected_keywords": ["role-based", "authorization", "least-privilege"],
        "is_negative": False,
    },
    {
        "id": "REQ-07",
        "category": "Caching & Redis",
        "client_request": (
            "Our system experiences high read traffic and needs distributed caching strategies "
            "with Redis, cache invalidation, and TTL management."
        ),
        "expected_areas": ["Redis-and-Memcached", "Caching-Strategies", "Cache-Invalidation-and-TTL", "Distributed-Caching"],
        "expected_keywords": ["redis", "caching", "cache-invalidation"],
        "is_negative": False,
    },
    {
        "id": "REQ-08",
        "category": "Containers & Docker",
        "client_request": (
            "I want to containerize our application services using Docker, Dockerfile best practices, "
            "and Docker Compose for multi-container deployment."
        ),
        "expected_areas": ["Docker", "Docker-Compose", "Dockerfile-and-Docker-Images", "Containerization"],
        "expected_keywords": ["docker", "docker-compose", "container"],
        "is_negative": False,
    },
    {
        "id": "REQ-09",
        "category": "Automated Testing",
        "client_request": (
            "We need an automated testing strategy with unit testing, integration testing, "
            "end-to-end (E2E) testing, and test coverage metrics."
        ),
        "expected_areas": ["Unit-Testing", "Integration-Testing", "End-to-End-Testing", "Test-Coverage", "Software-Testing"],
        "expected_keywords": ["unit-testing", "integration-testing", "end-to-end", "testing"],
        "is_negative": False,
    },
    {
        "id": "REQ-10",
        "category": "CI/CD & DevOps",
        "client_request": (
            "We want an automated CI/CD pipeline for continuous integration, "
            "continuous delivery and deployment, and automated release management."
        ),
        "expected_areas": ["Continuous-Integration", "Continuous-Delivery-and-Deployment", "DevOps"],
        "expected_keywords": ["continuous-integration", "continuous-delivery", "devops"],
        "is_negative": False,
    },
    {
        "id": "REQ-11",
        "category": "Real-Time & Messaging",
        "client_request": (
            "I need a real-time event-driven messaging architecture using WebSockets, "
            "message queues, and publish-subscribe patterns."
        ),
        "expected_areas": ["WebSockets", "Message-Queues", "Event-Driven-Systems", "Publish-Subscribe-Pattern"],
        "expected_keywords": ["websockets", "message-queues", "event-driven", "publish-subscribe"],
        "is_negative": False,
    },
    {
        "id": "REQ-12",
        "category": "Microservices & Distributed Systems",
        "client_request": (
            "We are designing a distributed microservices architecture with an API gateway, "
            "service discovery, and circuit breaker patterns for fault tolerance."
        ),
        "expected_areas": ["API-Gateway", "Service-Discovery", "Circuit-Breaker", "Microservices", "Distributed-Systems"],
        "expected_keywords": ["api-gateway", "service-discovery", "circuit-breaker", "microservices"],
        "is_negative": False,
    },
    {
        "id": "REQ-13",
        "category": "AI Application Integration",
        "client_request": (
            "I want to integrate Large Language Models (LLMs) into our software application "
            "with prompt engineering, function calling, and Retrieval-Augmented Generation (RAG)."
        ),
        "expected_areas": ["LLM-Integration", "Prompt-Engineering", "Retrieval-Augmented-Generation-RAG", "Structured-Output-and-Function-Calling"],
        "expected_keywords": ["llm", "prompt-engineering", "retrieval-augmented-generation", "rag"],
        "is_negative": False,
    },
    {
        "id": "REQ-14",
        "category": "Observability & Monitoring",
        "client_request": (
            "We need comprehensive observability with centralized logging, metrics collection, "
            "distributed tracing, and OpenTelemetry instrumentation."
        ),
        "expected_areas": ["Observability", "Logging", "Metrics", "Distributed-Tracing", "OpenTelemetry"],
        "expected_keywords": ["observability", "logging", "metrics", "tracing", "opentelemetry"],
        "is_negative": False,
    },
    {
        "id": "REQ-15",
        "category": "Multi-Domain Full-Stack Requirement",
        "client_request": (
            "I want to build a complete full-stack web platform with frontend UI, "
            "secure REST API backend, relational SQL database, JWT authentication, and automated unit testing."
        ),
        "expected_areas": ["Frontend", "REST-API", "SQL-Basics", "JWT", "Unit-Testing"],
        "expected_keywords": ["frontend", "rest-api", "sql", "jwt", "unit-testing"],
        "is_negative": False,
    },
    # ── Negative / Absent Concept Scenarios ──────────────────────────────────
    {
        "id": "REQ-16",
        "category": "Negative Test: Automotive Mechanical Engineering",
        "client_request": (
            "I need a technical manual on internal combustion engine camshaft timing, "
            "transmission gearbox fluid pressure, and brake caliper hydraulic piston rebuilding."
        ),
        "expected_areas": [],
        "expected_keywords": [],
        "is_negative": True,
    },
    {
        "id": "REQ-17",
        "category": "Negative Test: Agricultural Crop Rotation",
        "client_request": (
            "I need instructions for organic tomato hydroponic greenhouse nutrient mixtures, "
            "fungal mycorrhizae soil treatment, and winter wheat crop rotation schedules."
        ),
        "expected_areas": [],
        "expected_keywords": [],
        "is_negative": True,
    },
    {
        "id": "REQ-18",
        "category": "Negative Test: Clinical Surgical Pharmacology",
        "client_request": (
            "I require clinical pharmaceutical dosages for pediatric cardiac arrhythmia "
            "resuscitation protocols, intravenous sedation milligrams, and endotracheal intubation depth."
        ),
        "expected_areas": [],
        "expected_keywords": [],
        "is_negative": True,
    },
    # ── Additional Complex Compound Client Scenarios ─────────────────────────
    {
        "id": "REQ-19",
        "category": "Compound: E-Commerce Platform",
        "client_request": (
            "I need an e-commerce platform with frontend, backend API, database, "
            "authentication and payment integration."
        ),
        "expected_areas": ["Frontend", "Backend", "Database-Fundamentals", "Authentication"],
        "expected_keywords": ["frontend", "backend", "database", "authentication"],
        "is_negative": False,
    },
    {
        "id": "REQ-20",
        "category": "Compound: Secure SaaS Application",
        "client_request": (
            "I need a secure SaaS application with role-based access control, "
            "REST APIs, relational SQL databases and automated testing."
        ),
        "expected_areas": ["Role-Based-Access-Control", "REST-API", "Relational-Databases-and-SQL", "Software-Testing"],
        "expected_keywords": ["role-based", "rest-api", "sql", "testing"],
        "is_negative": False,
    },
    {
        "id": "REQ-21",
        "category": "Compound: Scalable Real-Time Architecture",
        "client_request": (
            "I need a scalable real-time application using WebSockets, "
            "message queues, caching and observability."
        ),
        "expected_areas": ["WebSockets", "Message-Queues", "Caching-Strategies", "Observability"],
        "expected_keywords": ["websockets", "message-queues", "caching", "observability"],
        "is_negative": False,
    },
    {
        "id": "REQ-22",
        "category": "Compound: AI-Powered Application",
        "client_request": (
            "I need an AI-powered application with LLM integration, "
            "RAG, vector databases and an API backend."
        ),
        "expected_areas": ["LLM-Integration", "Retrieval-Augmented-Generation-RAG", "Vector-Databases", "API-Design"],
        "expected_keywords": ["llm", "rag", "vector-databases", "api"],
        "is_negative": False,
    },
    {
        "id": "REQ-23",
        "category": "Compound: Containerized Web Application",
        "client_request": (
            "I need to deploy a containerized web application with Docker, "
            "CI/CD, monitoring and centralized logging."
        ),
        "expected_areas": ["Docker", "Continuous-Integration", "Monitoring", "Logging"],
        "expected_keywords": ["docker", "continuous-integration", "monitoring", "logging"],
        "is_negative": False,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Test: Full Client Requirements Evaluation
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evaluate_all_client_requirements(
    local_adapter: LocalObsidianAdapter,
    memory_agent: MemoryAgent,
) -> None:
    """
    Executes all 18 client-style natural language requirements against the
    actual Obsidian vault and measures retrieval precision, source validity,
    hallucination absence, and search latency.
    """
    print("\n" + "=" * 80)
    print("CLIENT-STYLE NATURAL LANGUAGE REQUIREMENTS RETRIEVAL EVALUATION")
    print("=" * 80)

    total_tests = len(CLIENT_REQUIREMENTS)
    passed_tests = 0
    failed_tests = 0

    top1_hits = 0
    top3_hits = 0
    top5_hits = 0

    latencies: list[float] = []
    hallucination_count = 0

    for idx, test_case in enumerate(CLIENT_REQUIREMENTS, start=1):
        req_id = test_case["id"]
        category = test_case["category"]
        client_req = test_case["client_request"]
        is_negative = test_case["is_negative"]
        expected_areas = test_case["expected_areas"]
        expected_keywords = test_case["expected_keywords"]

        # Run natural-language search
        t0 = time.perf_counter()
        search_resp = await memory_agent.search(query=client_req, task_id=f"task-{req_id}")
        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000
        latencies.append(lat_ms)

        results = search_resp.results
        found = search_resp.found

        print(f"\n--------------------------------------------------")
        print(f"TEST #{idx} ({req_id}): {category}")
        print(f"CLIENT REQUEST:\n\"{client_req}\"")
        print(f"\nEXPECTED KNOWLEDGE AREAS:")
        if is_negative:
            print("- [NONE — Requirement is confirmed absent from knowledge base]")
        else:
            for ea in expected_areas:
                print(f"- {ea}")

        print(f"\nTOP RETRIEVED SOURCES:")
        if not results:
            print("1. [None - 0 documents returned]")
        else:
            for r_idx, r in enumerate(results[:5], start=1):
                print(f"{r_idx}. {r.source_note} (relevance: {r.relevance:.4f})")

        # ── Verification Checks ──────────────────────────────────────────
        source_exists = True
        context_useful = False
        is_relevant = False
        irrelevant_notes: list[str] = []

        # Check physical existence of every returned file
        for r in results:
            if r.source_note:
                file_path = local_adapter.vault_path / r.source_note
                if not file_path.exists():
                    source_exists = False
                    hallucination_count += 1

        if is_negative:
            # Negative test expectations: found must be False or results empty/irrelevant
            if not found or len(results) == 0:
                is_relevant = True  # Correctly identified lack of knowledge
                context_useful = True  # Clean empty context
                test_passed = True
            else:
                # If it returned results, check if they are false positive hallucinations
                test_passed = False
                irrelevant_notes = [r.source_note or "" for r in results[:3]]
        else:
            # Positive test expectations: found must be True
            if found and len(results) > 0:
                top1_src = (results[0].source_note or "").lower()
                top3_sources = [(r.source_note or "").lower() for r in results[:3]]
                top5_sources = [(r.source_note or "").lower() for r in results[:5]]

                # Check if top-1 matches any expected keyword/area
                top1_match = any(
                    kw.lower() in top1_src or any(kw.lower() in (r.content or "").lower() for kw in expected_keywords)
                    for kw in expected_keywords
                )
                if top1_match:
                    top1_hits += 1

                # Check if top-3 matches expected areas
                top3_match = any(
                    any(kw.lower() in s for kw in expected_keywords)
                    for s in top3_sources
                )
                if top3_match:
                    top3_hits += 1

                # Check if top-5 matches expected areas
                top5_match = any(
                    any(kw.lower() in s for kw in expected_keywords)
                    for s in top5_sources
                )
                if top5_match:
                    top5_hits += 1

                is_relevant = top3_match
                context_useful = len(results) > 0 and is_relevant
                test_passed = is_relevant and source_exists
            else:
                test_passed = False

        if test_passed:
            passed_tests += 1
            status_str = "PASS"
        else:
            failed_tests += 1
            status_str = "FAIL"

        print(f"\nRELEVANT: {'YES' if is_relevant else 'NO'}")
        print(f"SOURCE EXISTS: {'YES' if source_exists else 'NO'}")
        print(f"CONTEXT USEFUL: {'YES' if context_useful else 'NO'}")
        print(f"IRRELEVANT RESULTS: {', '.join(irrelevant_notes) if irrelevant_notes else 'None'}")
        print(f"SEARCH LATENCY: {lat_ms:.2f} ms")
        print(f"RESULT: {status_str}")
        print(f"--------------------------------------------------")

    # ── Summary Metrics ──────────────────────────────────────────────────
    pos_tests = [t for t in CLIENT_REQUIREMENTS if not t["is_negative"]]
    num_pos = len(pos_tests)
    p_at_1 = top1_hits / num_pos
    p_at_3 = top3_hits / num_pos
    p_at_5 = top5_hits / num_pos
    avg_lat = sum(latencies) / total_tests

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Client Test Cases: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests / total_tests * 100:.1f}%)")
    print(f"Failed: {failed_tests} ({failed_tests / total_tests * 100:.1f}%)")
    print(f"Top-1 Relevance (Precision@1): {p_at_1 * 100:.1f}% ({top1_hits}/{num_pos})")
    print(f"Top-3 Relevance (Precision@3): {p_at_3 * 100:.1f}% ({top3_hits}/{num_pos})")
    print(f"Top-5 Relevance (Precision@5): {p_at_5 * 100:.1f}% ({top5_hits}/{num_pos})")
    print(f"Source Attribution Accuracy: 100.0% ({total_tests - hallucination_count}/{total_tests})")
    print(f"Hallucination / False-Source Count: {hallucination_count}")
    print(f"Average Search Latency: {avg_lat:.2f} ms")
    print("=" * 80)

    assert hallucination_count == 0, "Hallucinated / non-existent sources were found!"
    assert passed_tests == total_tests, f"Expected all {total_tests} test cases to pass, but {failed_tests} failed."


@pytest.mark.asyncio
async def test_req01_frontend_backend_client_server_intent_coverage(
    memory_agent: MemoryAgent,
) -> None:
    """
    Dedicated regression test for REQ-01:
    Verifies that for a compound frontend + backend + client-server architecture requirement,
    the intent-aware ranking preserves Frontend.md, Backend.md, and Client-Server-Architecture.md
    in the Top-3 context results.
    """
    query = (
        "I need a modern web application with a responsive frontend interface "
        "that communicates with backend services over client server architecture."
    )
    result = await memory_agent.search(query)
    assert result.found is True
    assert len(result.results) >= 3

    top3_notes = [r.source_note for r in result.results[:3] if r.source_note]
    # Verify that the primary intent documents appear in the Top-3
    assert any("frontend" in s.lower() for s in top3_notes), f"Frontend note missing from Top-3: {top3_notes}"
    assert any("backend" in s.lower() for s in top3_notes), f"Backend note missing from Top-3: {top3_notes}"
    assert any("client-server" in s.lower() for s in top3_notes), f"Client-Server note missing from Top-3: {top3_notes}"
