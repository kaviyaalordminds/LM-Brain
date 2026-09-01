"""
Planner — Capability Detection

Identifies technical capabilities mentioned in a natural-language request.
Capability detection is fully separate from specialist assignment.
The capability list is extensible via CAPABILITY_KEYWORDS.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Capability keyword map
# Each key is a canonical capability name; values are trigger keywords.
# All matching is case-insensitive and whole-word-aware.
# ---------------------------------------------------------------------------

CAPABILITY_KEYWORDS: dict[str, list[str]] = {
    # Frontend / UI
    "frontend": [
        "frontend", "front-end", "front end", "ui", "user interface",
        "react", "vue", "angular", "svelte", "html", "css", "tailwind",
        "bootstrap", "next.js", "nextjs", "nuxt", "web component",
        "responsive", "landing page", "login page", "dashboard", "page",
        "component", "spa", "single page",
    ],
    # Backend / Server
    "backend": [
        "backend", "back-end", "back end", "server", "api server",
        "rest api", "restful", "fastapi", "django", "flask", "express",
        "node", "spring", "laravel", "ruby on rails", "endpoint",
        "microservice", "service", "handler", "middleware",
    ],
    # Database
    "database": [
        "database", "db", "postgresql", "postgres", "mysql", "sqlite",
        "mongodb", "redis", "sql", "nosql", "schema", "table", "migration",
        "orm", "sqlalchemy", "prisma", "drizzle", "relational",
        "collection", "index", "query",
    ],
    # API / Third-party integration
    "api_integration": [
        "third-party", "third party", "external api", "stripe",
        "twilio", "sendgrid", "oauth", "webhook", "sdk", "client library",
        "integrate with", "connect to", "api key", "api client",
        "payment gateway", "google api", "github api",
    ],
    # Authentication
    "authentication": [
        "auth", "authentication", "login", "logout", "sign in", "sign up",
        "register", "jwt", "json web token", "session", "cookie",
        "oauth2", "openid", "passport", "credential",
    ],
    # Authorization
    "authorization": [
        "authorization", "authorisation", "permission", "role", "rbac",
        "acl", "access control", "policy", "privilege",
    ],
    # Security
    "security": [
        "security", "secure", "vulnerability", "penetration", "pentest",
        "owasp", "xss", "csrf", "injection", "audit", "threat",
        "encryption", "https", "tls", "ssl", "sanitize", "firewall",
    ],
    # Testing / QA
    "testing": [
        "test", "tests", "testing", "unit test", "integration test",
        "e2e", "end-to-end", "pytest", "jest", "cypress", "playwright",
        "qa", "quality assurance", "regression", "coverage", "mock",
        "test suite", "test plan",
    ],
    # Deployment / DevOps
    "deployment": [
        "deploy", "deployment", "release", "ship", "production",
        "staging", "kubernetes", "k8s", "helm", "terraform",
        "ansible", "nginx", "reverse proxy", "load balancer",
    ],
    # Docker
    "docker": [
        "docker", "container", "containerize", "dockerfile",
        "docker-compose", "docker compose", "image build",
    ],
    # CI/CD
    "cicd": [
        "ci/cd", "ci cd", "cicd", "github actions", "gitlab ci",
        "jenkins", "pipeline", "continuous integration",
        "continuous deployment", "continuous delivery",
    ],
    # Cloud
    "cloud": [
        "cloud", "aws", "azure", "gcp", "google cloud",
        "s3", "ec2", "lambda", "vercel", "netlify", "heroku",
        "render", "railway", "fly.io",
    ],
    # AI / ML
    "ai_ml": [
        "ai", "ml", "machine learning", "deep learning", "neural",
        "model", "train", "inference", "pytorch", "tensorflow",
        "scikit-learn", "sklearn", "huggingface", "transformers",
        "llm", "large language model", "gpt", "gemini", "claude",
        "openai", "anthropic",
    ],
    # RAG / Embeddings
    "rag": [
        "rag", "retrieval augmented generation", "retrieval-augmented",
        "embedding", "embeddings", "semantic search", "similarity search",
        "langchain", "llamaindex", "llama-index",
    ],
    # Vector database
    "vector_database": [
        "vector database", "vectordb", "vector store", "vector db",
        "pinecone", "weaviate", "chromadb", "qdrant", "milvus",
        "faiss", "annoy",
    ],
    # Research / Documentation
    "research": [
        "research", "find documentation", "official documentation",
        "find the latest", "discover", "look up", "find library",
        "find framework", "find package", "current best practice",
        "latest recommendation",
    ],
    # Image generation
    "image_generation": [
        "image", "generate image", "generate a picture", "hero image",
        "illustration", "graphic", "visual", "icon", "logo", "banner",
        "artwork", "dalle", "stable diffusion", "midjourney",
    ],
    # Memory / existing knowledge
    "memory": [
        "existing architecture", "company architecture", "our system",
        "existing codebase", "current project", "internal documentation",
        "knowledge base", "previous work", "our database",
        "company style", "brand guide",
    ],
    # External documentation
    "external_docs": [
        "documentation link", "official docs", "api documentation",
        "external documentation", "third-party docs",
    ],
}


def detect_capabilities(user_request: str) -> list[str]:
    """
    Return a deduplicated, sorted list of detected capability names.
    Matching is case-insensitive; partial word boundaries are respected.
    """
    text = user_request.lower()
    detected: set[str] = set()

    for capability, keywords in CAPABILITY_KEYWORDS.items():
        for kw in keywords:
            # Use word-boundary matching for single words; substring for phrases
            if " " in kw:
                if kw in text:
                    detected.add(capability)
                    break
            else:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text):
                    detected.add(capability)
                    break

    return sorted(detected)
