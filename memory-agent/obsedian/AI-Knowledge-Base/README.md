# AI Knowledge Base — Obsidian Vault

A complete, interconnected knowledge base covering **200 Artificial Intelligence topics**, organized
for both human learning in Obsidian and machine retrieval as a local RAG / AI-agent knowledge source.

## Structure

```
AI-Knowledge-Base/
├── 00-Index/
│   ├── AI-Master-Index.md        # all 200 topics grouped by category
│   ├── AI-Roadmap.md             # beginner -> research learning path
│   ├── AI-Concept-Map.md         # Mermaid map of how domains connect
│   ├── AI-Topic-Directory.md     # flat table: ID, topic, category, folder
│   └── VALIDATION-REPORT.md      # automated QC report (200/200 PASS)
├── 01-AI-Fundamentals/           (20 topics)
├── 02-Machine-Learning/          (20 topics)
├── 03-ML-Algorithms/             (20 topics)
├── 04-Deep-Learning/             (20 topics)
├── 05-NLP/                       (20 topics)
├── 06-Speech-Voice-AI/           (15 topics)
├── 07-Computer-Vision/           (20 topics)
├── 08-Generative-AI/             (15 topics)
├── 09-AI-Agents/                 (15 topics)
├── 10-Advanced-AI/               (15 topics)
├── 11-AI-Safety-Security-Ethics/ (15 topics)
├── 12-AI-Infrastructure-Future/  (5 topics)
└── README.md
```

Every topic file (e.g. `061-Deep-Learning.md`) follows the same 30-section structure: Definition,
Core Concepts, Architecture/Workflow (with a Mermaid diagram), Mathematical Concepts, a Mini Practical
Example, Related AI Topics, AI Agent Relevance, RAG/LLM Relevance, and a Summary — with YAML frontmatter
and Obsidian `[[wikilinks]]` throughout.

## Importing into Obsidian

1. Unzip `AI-Knowledge-Base-Obsidian.zip`.
2. Open Obsidian → **Open folder as vault** → select the extracted `AI-Knowledge-Base` folder.
3. Open **Graph View** (icon in the left ribbon, or `Ctrl/Cmd+G`) to see all 200 topics connected
   by their `[[wikilinks]]`.
4. Start from `00-Index/AI-Master-Index.md` or `00-Index/AI-Roadmap.md` for a guided path.
5. No community plugins are required — everything uses core Markdown, YAML frontmatter, Wikilinks,
   and Mermaid, all natively supported by Obsidian.

## Using the Vault as a Local AI Agent / RAG Knowledge Base

- **Chunking**: each `.md` file is already a self-contained, independently-understandable unit
  (~1,000–1,500 words) with numbered headings — a good default chunk boundary for embedding.
- **Metadata**: the YAML frontmatter (`id`, `category`, `tags`, `related`) can be indexed as
  structured metadata alongside the embedded text for hybrid (metadata + vector) retrieval.
- **Relationships**: the `related:` frontmatter field and `[[wikilinks]]` in each file's "Related AI
  Topics" section form an explicit knowledge graph — useful for graph-augmented retrieval or
  multi-hop RAG in addition to plain vector similarity search.
- **Ingestion example**: point any Markdown-aware loader (e.g. LangChain's `DirectoryLoader` /
  `UnstructuredMarkdownLoader`, or LlamaIndex's `SimpleDirectoryReader`) at this folder, embed each
  file (or each `##` section) into your vector store of choice, and use the frontmatter `category`
  field as a metadata filter.

## Notes on Scope and Accuracy

This vault distinguishes established, production techniques (e.g. Linear Regression, CNNs,
Transformers) from emerging or research-stage concepts (e.g. Neuro-Symbolic AI, World Models, AGI),
and avoids presenting speculative or fast-changing claims as settled fact. See each topic's own
content for the relevant caveats.
