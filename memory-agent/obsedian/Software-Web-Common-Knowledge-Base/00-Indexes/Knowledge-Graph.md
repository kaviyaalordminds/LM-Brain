---
title: "Knowledge Graph"
type: "Index"
---

# Knowledge Graph

A high-level Mermaid map connecting the major categories in this knowledge base. For topic-level
relationships, see each topic's "Related Topics" section.

```mermaid
graph TD
    Programming --> DataStructures[Data Structures]
    Programming --> Algorithms
    Programming --> ProgrammingConcepts[Programming Concepts]

    SoftwareEngineering[Software Engineering] --> DevelopmentPractices[Development Practices]
    SoftwareEngineering --> Methodologies
    SoftwareEngineering --> Architecture[Software Architecture]
    SoftwareEngineering --> Testing

    Architecture --> DesignPatterns[Design Patterns]
    Architecture --> SystemDesign[System Design]

    SystemDesign --> DistributedSystems[Distributed Systems]
    SystemDesign --> Networking

    Networking --> WebCommunication[Web Communication]
    WebCommunication --> APIs

    APIs --> DataFormats[Data Formats]
    APIs --> Authentication

    Authentication --> Authorization
    Authentication --> Security
    Authorization --> Security

    Databases --> Caching
    Databases --> SystemDesign

    Concurrency --> DistributedSystems
    DistributedSystems --> Messaging

    VersionControl[Version Control] --> DevOps
    Dependencies --> BuildAndRelease[Build and Release]
    BuildAndRelease --> DevOps

    DevOps --> Containers
    Containers --> Cloud
    Cloud --> Infrastructure

    DevOps --> Observability
    Observability --> Reliability
    Reliability --> Performance
    Reliability --> ProductionEngineering[Production Engineering]

    Documentation --> ProjectManagement[Project Management]

    APIs --> AIIntegration[AI Application Integration]
    Security --> AIIntegration
```

## Category Summary

| Category | Hub Topic | Feeds Into |
|----------|-----------|------------|
| Programming Fundamentals | [[Programming]] | Programming Concepts, Data Structures, Algorithms |
| Software Engineering | [[Software Engineering]] | Development Practices, Methodologies, Architecture |
| Architecture & System Design | [[Software Architecture]] | Design Patterns, System Design, Distributed Systems |
| Networking & Web | [[Computer Networking]] | Web Communication, APIs, Data Formats |
| Databases & Caching | [[Database Fundamentals]] | Caching, Performance, System Design |
| Security | [[Application Security]] | Authentication, Authorization |
| DevOps & Infrastructure | [[DevOps]] | Containers, Cloud, Infrastructure, Observability |
| Reliability & Production | [[Reliability and Resilience]] | Performance, Production Engineering |
| AI Integration | [[AI API Integration]] | Prompt Engineering, RAG, Vector Databases |
