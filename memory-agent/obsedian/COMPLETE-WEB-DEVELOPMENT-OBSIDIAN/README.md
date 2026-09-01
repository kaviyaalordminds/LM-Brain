---
title: "README"
category: "Web Development"
level: "All"
type: "Meta"
status: "In Progress"
---

# Complete Web Development Knowledge Base

This vault is a structured, read-only Web Development knowledge base built for import into Obsidian and for use as a retrieval source by a local AI agent. It covers the Web Engineering field from absolute beginner through expert/production level.

## What This Contains

Every topic is its own Markdown file, following a fixed section structure (Definition, Why It Matters, Core Concepts, How It Works, Architecture, Mermaid Diagram, Example, Code Example, Real-World Usage, Advantages, Disadvantages, Common Mistakes, Best Practices, Security/Performance/Accessibility Considerations, Related Topics, Prerequisites, Advanced Concepts, Quick Revision, Interview Questions — sections included only where relevant).

Topics are cross-linked using Obsidian wiki-links (`[[Topic Name]]`), so the vault forms a connected knowledge graph rather than a flat file list. Diagrams use Mermaid (`flowchart`, `sequenceDiagram`, `erDiagram`, `classDiagram`, `stateDiagram-v2`) wherever a visual materially improves understanding.

## Folder Structure

Folders are numbered `00`–`70` plus `99-Metadata`, in rough learning order:

- `00` — top-level indexes (this is your entry point after README)
- `01–11` — Web fundamentals, networking, HTTP, HTML, accessibility, CSS, responsive design, JavaScript, TypeScript, browser architecture, DOM/Web APIs
- `12–18` — Frontend engineering, React, other frameworks, Next.js, UI engineering, animation, tooling
- `19–35` — Backend engineering, Node.js, backend frameworks, APIs, REST, GraphQL, real-time, databases, NoSQL, ORM, auth, authorization, security, files, search, caching, background jobs
- `36–41` — Performance, Core Web Vitals, SEO, PWA, i18n, testing
- `42–54` — Version control, tooling, debugging, DevOps, Docker, web servers, deployment, cloud, serverless, edge, monitoring, reliability, scalability
- `55–63` — Architecture, system design, microservices, message queues, multi-tenancy, production engineering, standards, cross-browser, advanced engineering
- `64–70` — Projects, roadmaps, glossary, patterns, anti-patterns, checklists, reference
- `99` — metadata/frontmatter documentation

## How To Use This In Obsidian

1. Open this folder as an Obsidian vault.
2. Start at `00-Web-Development-Index/Web-Development-Index.md`.
3. Follow wiki-links to move through related topics; use the graph view to see how concepts connect.
4. Each numbered folder can also be browsed directly for a linear beginner→expert read-through of that domain.

## Knowledge Graph & Linking

Every substantive topic links to prerequisite topics (`## Prerequisites`) and related/next topics (`## Related Topics`) using `[[wiki-links]]`. Cross-domain concepts (e.g. "Caching" used by both Frontend and Databases) live in one canonical file and are linked from everywhere else, rather than duplicated.

## Diagram System

Mermaid diagrams are embedded directly in the Markdown and render natively in Obsidian. They are used for request/response flows, architecture, authentication flows, database relationships, deployment pipelines, and system design — never decoratively.

## Status

This vault is being built incrementally, category by category. See `MASTER-INDEX.md` for which categories currently have complete content.
