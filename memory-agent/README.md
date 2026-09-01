# Memory Agent

Knowledge layer for the **Autonomous AI Workforce**.

Provides internal Obsidian search (with real local Markdown vault indexing), controlled external research, deterministic evidence validation, and approved-only memory writes.

---

## Architecture

```
User Query
    │
    ▼
Memory Agent
    │
    ├─► Internal Obsidian Search (Local Vault / Mock)
    │       │
    │       ├── FOUND ──► Return MemoryResult  (status: retrieved)
    │       │
    │       └── NOT FOUND
    │               │
    │               ▼
    │         Controlled External Research
    │               │
    │               ▼
    │         Collect Sources + Evidence  (status: unverified)
    │               │
    │               ▼
    │         Validation Layer (deterministic rules)
    │               │
    │       ┌───────┴───────┐
    │     APPROVED        REJECTED
    │       │               │
    │       ▼               ▼
    │   Write to         Do not store
    │   Obsidian
    │       │
    │       ▼
    │   Return MemoryResult  (status: approved)
    │
    ▼
API Response
```

### Trust Hierarchy

| Status | Meaning |
|---|---|
| `retrieved` | Directly read from Obsidian — highest internal trust |
| `unverified` | Raw external research — never auto-promoted |
| `validated` | Passed evidence rules — not yet written |
| `approved` | Written to Obsidian as trusted company knowledge |
| `rejected` | Failed validation — never stored |
| `pending` | Validation in progress |

---

## Folder Structure

```
memory-agent/
│
├── app/
│   ├── main.py                   # FastAPI app + adapter wiring + lifespan
│   ├── api/routes/memory.py      # 5 API route handlers (thin HTTP layer)
│   ├── core/
│   │   ├── memory_agent.py       # Central orchestrator
│   │   ├── retrieval.py          # Context ranking and assembly
│   │   ├── research.py           # External research pipeline
│   │   ├── validation.py         # Deterministic 6-rule validator
│   │   └── memory_writer.py      # Approved-only write guard
│   ├── adapters/
│   │   ├── obsidian_adapter.py   # LocalObsidianAdapter + MockObsidianAdapter
│   │   └── research_provider.py  # ResearchProvider ABC + MockResearchProvider
│   ├── models/memory.py          # Pydantic data contracts (CamelModel)
│   └── config/settings.py        # Environment-based configuration
│
├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── test_memory_agent.py      # Unit tests (17 tests)
│   ├── test_api.py               # API & E2E pipeline tests (18 tests)
│   └── test_local_retrieval.py   # Real local vault retrieval & benchmark tests (16 tests)
│
├── obsedian/                     # Local Obsidian knowledge base (555 Markdown notes)
├── .env                          # Local environment config
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Setup & Configuration

```bash
cd memory-agent

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
```

### Switching Adapters

In `.env`:

#### 1. Local Real Knowledge Base (Default)
Indexes and searches the actual 555 Markdown notes on disk with YAML frontmatter, headings, tags, and wikilinks:
```ini
OBSIDIAN_ADAPTER=local
OBSIDIAN_VAULT_PATH=C:\Lordminds\Multiagent\memory-agent\obsedian
RESEARCH_PROVIDER=mock
```

#### 2. In-Memory Mock Adapter (For isolated testing)
```ini
OBSIDIAN_ADAPTER=mock
RESEARCH_PROVIDER=mock
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development \| staging \| production` |
| `LOG_LEVEL` | `INFO` | `DEBUG \| INFO \| WARNING \| ERROR` |
| `OBSIDIAN_ADAPTER` | `local` | `local \| mock \| real` |
| `OBSIDIAN_VAULT_PATH` | `C:\Lordminds\Multiagent\memory-agent\obsedian` | Path to Obsidian vault directory |
| `RESEARCH_PROVIDER` | `mock` | `mock \| web` |
| `RESEARCH_API_KEY` | _(empty)_ | API key for external research (never log) |
| `RESEARCH_TIMEOUT_SECONDS` | `30` | Timeout for external research calls |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8001` | Server port |

---

## How Local Retrieval Works

The `LocalObsidianAdapter` implements high-performance lexical and metadata-aware retrieval:

1. **Discovery**: Recursively scans all `.md` files in the vault (skipping hidden and system directories).
2. **Metadata Parsing**: Extracts YAML frontmatter (`title`, `tags`, `category`, `type`, `aliases`, `related`), headings (`# Heading`), wikilinks (`[[target]]`), and body text.
3. **Inverted Indexing**: Builds an in-memory inverted index mapping tokens to document IDs with precomputed term frequencies (TF) and inverse document frequencies (IDF).
4. **Scoring & Ranking**:
   - Exact Title match (+50.0 boost)
   - Partial Title match (+25.0 boost)
   - Title Token Coverage (+15.0 boost)
   - Heading Match (+12.0 boost)
   - Tag / Alias Match (+8.0 boost)
   - Exact phrase in body (+10.0 boost)
   - BM25 term frequency / IDF scoring on body tokens
   - Normalized relevance score mapped to `[0.0, 1.0]`
5. **No Hallucination**: Queries for non-existent concepts return `found = false` and an empty list.

---

## Running the Application

```bash
# Development server (port 8001)
python -m uvicorn app.main:app --reload --port 8001
```

Swagger API documentation: `http://localhost:8001/docs`

---

## Running Tests & Benchmarks

```bash
# Run all 51 tests (unit, API, E2E, and local retrieval benchmarks)
python -m pytest tests/ -v -s
```

### Retrieval Quality Benchmark Results
- **Total Knowledge Files**: 555 Markdown documents (3.27 MB)
- **Top-1 Accuracy (Precision@1)**: **100.0%**
- **Top-3 Accuracy (Precision@3)**: **100.0%**
- **Average Search Latency**: **~10 ms**

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/memory/search` | Search internal Obsidian knowledge base |
| `POST` | `/api/v1/memory/research` | Controlled external research (returns UNVERIFIED) |
| `POST` | `/api/v1/memory/validate` | Validate evidence with deterministic rules |
| `POST` | `/api/v1/memory/write` | Write APPROVED knowledge to Obsidian |
| `GET` | `/api/v1/memory/context/{taskId}` | Retrieve task memory context |
| `GET` | `/health` | Health check |

---

## Future Semantic / Vector Retrieval Recommendations

The `ObsidianAdapter` ABC abstract interface isolates knowledge retrieval from the rest of the Autonomous AI Workforce.

When scaling beyond lexical indexing to dense semantic embeddings:
1. Create a `VectorObsidianAdapter(ObsidianAdapter)` subclass.
2. Connect a local vector embedding model (e.g. `nomic-embed-text` or `bge-small-en`) and local vector store (e.g. Chroma, Qdrant, or SQLite-VSS).
3. Hybrid ranking: combine BM25 lexical scores with cosine similarity vector scores (Reciprocal Rank Fusion / RRF).
4. No changes to `MemoryAgent`, `RetrievalService`, or API routes are needed because the `ObsidianAdapter` interface remains strictly locked.

---

## Memory Safety Rules

1. External research ≠ trusted memory
2. Validation must happen before approved write
3. Every stored research-derived item retains source/evidence references
4. Existing notes are never silently overwritten
5. Every write produces an audit record
6. The Memory Agent never hallucinates a retrieved note
7. If information is unavailable, `found=False` is returned explicitly
