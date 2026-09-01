# Software + Web Development — Common Knowledge Base

An Obsidian vault covering the **intersection** of general Software Development and Web Development —
286 topics across 38 categories, built for both human learning and local AI agent / RAG retrieval.

## Scope

This is deliberately a **common-topics-only** knowledge base. It excludes:
- Web-only presentation topics (HTML elements, CSS selectors/Flexbox/Grid, React/Vue/Angular component APIs, Bootstrap/Tailwind)
- Software-only topics with no web relevance (game dev, embedded systems, robotics, OS kernel development, pure ML research)

See `99-Audit/Knowledge-Base-Audit.md` for the full scope rationale, duplicate-consolidation log, and coverage report.

## Structure

```
Software-Web-Common-Knowledge-Base/
├── 00-Indexes/
│   ├── Master-Index.md          # all 286 topics grouped by category
│   ├── Learning-Path.md         # Beginner -> Expert progression
│   ├── Knowledge-Graph.md       # Mermaid map of how categories connect
│   ├── Glossary.md              # alphabetical list of every topic
│   └── <Category>-Index.md      # one index per category (38 files)
├── 01-Programming/ ... 38-AI-Application-Integration/   (286 topic files total)
├── 99-Audit/
│   └── Knowledge-Base-Audit.md  # coverage, exclusions, duplicates, validation status
└── README.md
```

Every topic file follows the same 24-section template: Definition, Why It Matters, Core Concepts, How
It Works, Architecture, Workflow (with a Mermaid diagram — including sequence diagrams for
authentication/request flows), a Practical Example, Code Example, Common Use Cases,
Advantages/Disadvantages, Common Mistakes, Best Practices, Security/Performance/Scalability/Production
Considerations, Testing, Debugging, Related Topics, Prerequisites, Next Topics, Interview Questions, and
a Quick Revision summary — with YAML frontmatter (`level`, `type`, `category`, `aliases`) and Obsidian
`[[wikilinks]]` throughout.

## Importing into Obsidian

1. Unzip `Software-Web-Common-Knowledge-Base.zip`.
2. Open Obsidian → **Open folder as vault** → select the extracted folder.
3. Open Graph View to see all 286 topics connected by their `[[wikilinks]]`.
4. Start from `00-Indexes/Master-Index.md` or `00-Indexes/Learning-Path.md`.
5. No community plugins required — core Markdown, YAML, Wikilinks, and Mermaid only.

## Using as a local AI agent / RAG source

Each file is a self-contained ~850–1,000 word chunk with numbered headings and structured YAML
metadata (`category`, `level`, `type`, `tags`, `related`) — good default chunk boundaries for embedding,
with metadata available for hybrid (vector + filter) retrieval. The `related:` frontmatter and each
file's "Related Topics" / "Prerequisites" / "Next Topics" sections form an explicit graph usable for
multi-hop retrieval in addition to plain similarity search.
