"""
Memory Agent — Task Analyzer

Deconstructs natural language queries and tasks into structured TaskScope:
  - Task Type (website_creation, ad_campaign, app_dev, research, etc.)
  - Domain (e-commerce, healthcare, social_media_advertising, quantum_computing, etc.)
  - Entity (Lordminds, Tesla, Apple, etc. or None if generic)
  - Platform / Tech (Instagram, React, Next.js, Web, iOS, etc.)
  - Requirements (list of discrete technical or business requirements needed)
"""

from __future__ import annotations

import re
from typing import Any

from app.models.memory import TaskScope


# Known company / organizational entities
_KNOWN_ENTITIES = {
    "lordminds": "Lordminds",
    "tesla": "Tesla",
    "apple": "Apple",
    "microsoft": "Microsoft",
    "google": "Google",
    "amazon": "Amazon",
    "meta": "Meta",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "nike": "Nike",
    "openai": "OpenAI",
}

# Explicit specialized domain patterns (external/niche domains)
_DOMAIN_PATTERNS: list[tuple[str, list[str]]] = [
    ("e-commerce", ["ecommerce", "e-commerce", "online store", "shopping cart", "storefront", "product catalog"]),
    ("healthcare", ["healthcare", "health care", "health", "medical", "hospital", "clinic", "patient", "clinical", "hipaa", "telehealth", "pediatric", "sedation", "intubation"]),
    ("social_media_advertising", ["instagram ad", "instagram ads", "facebook ad", "facebook ads", "tiktok ad", "social media ad", "ad campaign", "creative ads", "ad creatives"]),
    ("fintech", ["fintech", "banking", "finance", "payments", "payment gateway", "crypto", "defi", "trading", "wallet"]),
    ("quantum_computing", ["quantum computing", "quantum computer", "quantum", "qubit", "qubits", "superposition"]),
    ("automotive", ["internal combustion engine", "camshaft timing", "transmission gearbox", "brake caliper", "hydraulic piston", "automotive"]),
    ("agriculture", ["hydroponic", "crop rotation", "greenhouse nutrient", "mycorrhizae", "wheat crop"]),
    ("company_portal", ["company profile", "about us", "internal portal", "corporate site"]),
]

# Platform / Technology patterns
_PLATFORM_PATTERNS: list[tuple[str, list[str]]] = [
    ("Instagram", ["instagram", "ig"]),
    ("Facebook", ["facebook", "meta ads"]),
    ("TikTok", ["tiktok"]),
    ("LinkedIn", ["linkedin"]),
    ("Twitter/X", ["twitter", " x "]),
    ("YouTube", ["youtube"]),
    ("React", ["react", "reactjs", "react.js"]),
    ("Next.js", ["nextjs", "next.js", "next"]),
    ("Vue", ["vue", "vuejs"]),
    ("Angular", ["angular"]),
    ("FastAPI", ["fastapi"]),
    ("Docker", ["docker", "container"]),
    ("Kubernetes", ["k8s", "kubernetes"]),
    ("iOS", ["ios", "swift", "iphone"]),
    ("Android", ["android", "kotlin"]),
    ("Web", ["website", "web app", "browser", "frontend"]),
]

# Task Type patterns
_TASK_PATTERNS: list[tuple[str, list[str]]] = [
    ("ad_campaign", ["ads", "ad ", "campaign", "marketing", "promotion", "creatives", "copywriting"]),
    ("website_creation", ["website", "landing page", "web site", "storefront", "portal", "homepage"]),
    ("application_development", ["dashboard", "application", "backend", "api", "microservice", "fullstack", "system"]),
    ("research", ["tell me about", "what is", "explain", "research", "overview", "study", "analysis", "compare"]),
    ("general_task", []),
]


class TaskAnalyzer:
    """Analyzes queries and task contexts to extract structured TaskScope."""

    @staticmethod
    def analyze(query: str, context: str | None = None) -> TaskScope:
        combined = f"{query} {context or ''}".strip()
        combined_lower = combined.lower()

        # 1. Entity Extraction
        entity: str | None = None
        for key, canonical in _KNOWN_ENTITIES.items():
            if re.search(rf"\b{re.escape(key)}\b", combined_lower):
                entity = canonical
                break

        if not entity:
            entity_match = re.search(r"(?:for|by|company|startup|brand)\s+([A-Z][a-zA-Z0-9_\-]+)", combined)
            if entity_match:
                candidate = entity_match.group(1).strip()
                excluded_candidates = {
                    "E-commerce", "Ecommerce", "Instagram", "Facebook", "TikTok", "React", "Next",
                    "Healthcare", "Web", "Mobile", "Modern", "Creative", "Advanced", "Digital",
                    "An", "The", "Our", "All"
                }
                if candidate not in excluded_candidates:
                    entity = candidate

        # 2. Domain Extraction
        domain: str | None = None
        for dom_name, keywords in _DOMAIN_PATTERNS:
            if any(re.search(rf"\b{re.escape(kw)}\b", combined_lower) for kw in keywords):
                domain = dom_name
                break

        # Check explicit category pattern (e.g., "imaginary technology category XYZ123")
        if not domain:
            match_category = re.search(r"(?:category|domain|field)\s+([a-zA-Z0-9_\-]+)", combined_lower)
            if match_category:
                cand = match_category.group(1)
                if cand not in {"web", "software", "backend", "frontend", "general"}:
                    domain = cand

        # 3. Platform Extraction
        platform: str | None = None
        for plat_name, keywords in _PLATFORM_PATTERNS:
            if any(re.search(rf"\b{re.escape(kw)}\b", combined_lower) for kw in keywords):
                platform = plat_name
                break

        # 4. Task Type Extraction
        task_type = "general_task"
        for t_type, keywords in _TASK_PATTERNS:
            if any(re.search(rf"\b{re.escape(kw)}\b", combined_lower) for kw in keywords):
                task_type = t_type
                break

        # 5. Extract Core Discriminators
        discriminators = TaskAnalyzer._extract_discriminators(query, domain, entity, platform)

        # 6. Derive Requirements
        requirements = TaskAnalyzer._derive_requirements(task_type, domain, entity, platform, query)

        return TaskScope(
            task_type=task_type,
            domain=domain,
            entity=entity,
            platform=platform,
            discriminators=discriminators,
            requirements=requirements,
            raw_query=query,
        )

    @staticmethod
    def _extract_discriminators(
        query: str,
        domain: str | None,
        entity: str | None,
        platform: str | None,
    ) -> list[str]:
        """
        Extract key discriminative tokens from query that define the specific subject.
        Filters out generic intent/filler words (create, build, using, technology, etc.).
        """
        _GENERIC_ACTION_WORDS = {
            "create", "build", "make", "implement", "develop", "design", "need", "want",
            "using", "used", "use", "with", "for", "technology", "technologies", "tech",
            "system", "platform", "application", "solution", "project", "client", "modern",
            "complete", "proper", "an", "a", "the", "my", "our", "in", "to", "of", "and",
            "is", "it", "at", "by", "as", "or", "on", "from", "creative", "advanced",
        }
        tokens = re.findall(r"[a-zA-Z0-9_\-]+", query.lower())
        discriminators: list[str] = []
        for t in tokens:
            clean = t.strip("-")
            if len(clean) > 1 and clean not in _GENERIC_ACTION_WORDS:
                if clean not in discriminators:
                    discriminators.append(clean)

        if entity and entity.lower() not in [d.lower() for d in discriminators]:
            discriminators.append(entity.lower())
        if domain and domain.lower() not in [d.lower() for d in discriminators]:
            discriminators.append(domain.lower())
        if platform and platform.lower() not in [d.lower() for d in discriminators]:
            discriminators.append(platform.lower())

        return discriminators

    @staticmethod
    def _derive_requirements(
        task_type: str,
        domain: str | None,
        entity: str | None,
        platform: str | None,
        raw_query: str,
    ) -> list[str]:
        reqs: list[str] = []

        if entity:
            reqs.append(f"{entity} company profile, vision, and core standards")
            reqs.append(f"{entity} brand guidelines and service architecture")

        if domain == "e-commerce":
            reqs.append("e-commerce product catalog and category structure")
            reqs.append("shopping cart, state management, and checkout workflow")
            reqs.append("payment gateway integration and transaction security")
            reqs.append("responsive e-commerce user interface and conversion patterns")
        elif domain == "social_media_advertising" or (platform == "Instagram" and (task_type == "ad_campaign" or "ad" in raw_query.lower())):
            reqs.append(f"{platform or 'Social Media'} ad creative specifications (format, dimensions, duration)")
            reqs.append(f"{platform or 'Social Media'} visual storytelling and hook design")
            reqs.append("campaign copy, value proposition, and call-to-action guidelines")
            reqs.append("ad conversion tracking and audience targeting best practices")
        elif domain == "healthcare":
            reqs.append("healthcare compliance standards (HIPAA / GDPR / clinical data privacy)")
            reqs.append("patient metrics and clinical data visualization architecture")
            reqs.append("secure healthcare access control and audit logging")
        elif domain == "quantum_computing":
            reqs.append("quantum computing core principles (qubits, superposition, entanglement)")
            reqs.append("quantum gate operations and circuit design")
            reqs.append("practical quantum algorithms and industry use cases")
        elif domain in {"automotive", "agriculture"}:
            reqs.append(f"{domain} technical domain manual and specifications")
        elif domain == "company_portal" and not entity:
            reqs.append("corporate website layout and brand identity")
            reqs.append("service offerings and case study presentations")
        else:
            if domain:
                reqs.append(f"{domain.replace('_', ' ')} domain architecture and industry best practices")
                reqs.append(f"{domain.replace('_', ' ')} core specifications and workflow standards")
            if platform:
                reqs.append(f"{platform} platform implementation guidelines and UI/UX patterns")
            if not reqs:
                reqs.append(f"Domain knowledge and requirements for '{raw_query.strip()}'")

        return reqs
