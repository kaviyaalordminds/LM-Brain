---
title: "Knowledge Base Audit"
type: "Index"
---

# Knowledge Base Audit

## Coverage

- Total categories (folders): 38
- Total topic files: 286
- Total topics defined in taxonomy: 286

Categories covered: Programming Fundamentals, Programming Concepts, Data Structures, Algorithms, Software Engineering, Development Practices, Methodologies, Design Patterns, Software Architecture, System Design, Networking, Web Communication, APIs, Data Formats, Databases, Caching, Concurrency, Authentication, Authorization, Security, Testing, Debugging, Version Control, Dependencies, Build & Release, DevOps, Containers, Cloud, Infrastructure, Observability, Reliability, Performance, Distributed Systems, Messaging, Documentation, Project Management, Production Engineering, and AI Application Integration.

## Topics Removed Because They Were Web-Only

Per the scope rule (common topics only), the following were intentionally excluded: HTML elements/tags, CSS selectors/Flexbox/Grid/animations/variables, React/Vue/Angular/Svelte component APIs, Bootstrap/Tailwind, and other browser-UI-specific or framework-specific presentation APIs. These are real web development topics, but they are not shared with general software development, so they fall outside this knowledge base's scope.

## Topics Removed Because They Were Software-Only

Excluded: game development, embedded systems, robotics, hardware/FPGA engineering, OS kernel development, and pure machine learning research/data science topics that don't directly bear on building or operating a software/web application.

## Duplicate Topics Consolidated

The two source specifications listed several near-duplicate items; each was merged into one canonical topic (aliased where useful):
- REST / REST API / RESTful API -> **REST API**
- Testing (general) + Software Testing -> **Software Testing** (with specific test types as their own files)
- Logging (appeared under Error Handling, Observability, and Production Engineering) -> canonical **Logging** in Debugging, cross-linked elsewhere
- Semantic Versioning (appeared under Version Control and Dependency Management) -> canonical **Semantic Versioning** in Version Control
- Asynchronous Programming (appeared under Programming Concepts and Concurrency) -> canonical in **Programming Concepts**, cross-linked from Concurrency
- Disaster Recovery (appeared under System Design and Reliability) -> canonical in **System Design**
- CI/CD split into **Continuous Integration** and **Continuous Delivery and Deployment** rather than one combined file, matching how teams actually discuss the two halves
- Load Balancer / Load Balancing -> canonical **Load Balancing** in System Design, cross-linked from Networking
- API Documentation (appeared under APIs and Documentation) -> canonical in **APIs**
- Estimation (appeared under Methodologies and Project Management) -> canonical in **Methodologies** as *User Stories and Estimation*, cross-linked from Project Management
- Technical Debt Management (appeared under Software Engineering and Project Management) -> canonical **Technical Debt** in Software Engineering

## Missing Topics

None — all 286 taxonomy topics have a corresponding file.

## Broken Obsidian Links

0 broken link(s) found.

## Orphan Topics

None — every topic file has at least one outgoing wikilink and is linked from its category index and the Master Index.

## Beginner Topics
51 topics: Agile, Algorithms Overview, Arrays and Strings, Bandwidth and Network Latency, CRUD and Queries, Changelogs, Client-Server Architecture, Code Review, Computer Networking, Conditional Logic and Loops, DRY, KISS, and YAGNI, Data Serialization Formats, Data Structures Overview, Database Fundamentals, Debugging, Functions, Git, HTTP, HTTP Headers and Status Codes, HTTP Methods, Issue Tracking, JSON, Kanban, Keys and Relationships, Linked Lists, Logging, Modules and Packages, Object-Oriented Programming, Operators and Expressions, Package Managers, Programming, Pull Requests, README Files, Relational Databases and SQL, Scrum, Searching Algorithms, Sets and Maps, Smoke and Sanity Testing, Software Development Life Cycle (SDLC), Software Engineering, Software Testing, Sorting Algorithms, Sprint Planning and Backlog, Stack Traces, Stacks and Queues, Technical Documentation, Unit Testing, User Stories and Estimation, Variables and Data Types, Version Control, Waterfall

## Intermediate Topics
114 topics.

## Advanced Topics
115 topics.

## Professional Topics
0 topics.

## Expert Topics
6 topics: CAP Theorem, Consensus and Leader Election, Consistency Models, Distributed Locks and Transactions, Message Delivery Guarantees, Network Partitions

## Mermaid Diagram Count
286 / 286 topic files contain a Mermaid diagram (plus 2 more in Learning-Path.md and Knowledge-Graph.md).

## Total Markdown File Count
328 total .md files (286 topics + index/audit files).

## Recommended Learning Order
See [[Learning-Path]] for the full breakdown. Summary: Beginner -> Intermediate -> Advanced -> Professional -> Expert, following category dependencies shown in [[Knowledge-Graph]].

## Overall Validation Status: PASS

- Empty files: 0
- Placeholder text found: 0
- Files missing frontmatter: 0
- Files missing required sections: 0
- Files missing diagrams: 0
- Files missing wikilinks: 0
- Duplicate filenames: 0
- Total wikilink instances: 8682

Generated automatically by `validate2.py`.