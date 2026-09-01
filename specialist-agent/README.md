# Specialist Agent Execution Layer

The **Specialist Agent Execution Layer** is the second tier of the Lordminds
Autonomous AI Workforce. It provides a generic, reusable agent runtime and
ten pre-defined specialist agents that can be independently executed and tested
before the Master Orchestrator is ready.

---

## Architecture

```
specialist-agent/
├── specialist_agent/        ← Python package (importable)
│   ├── core/               ← Generic runtime, lifecycle, executor, verifier, registry
│   ├── contracts/          ← Task, result, artifact, and event contracts
│   ├── agents/             ← 10 specialist definitions (all use same runtime)
│   ├── tools/              ← Tool abstraction + registry + implementations
│   ├── models/             ← Model provider abstraction + registry + discovery
│   ├── permissions/        ← Permission policy + enforcement
│   ├── integration/        ← Thin Memory Agent client
│   └── config/             ← Environment-driven settings
└── tests/                  ← Deterministic specialist agent tests
```

---

## CURRENTLY IMPLEMENTED

### Generic Runtime (`core/agent.py`)

`SpecialistAgent` is the **one** runtime used by all ten specialists.
It manages:

| Feature | Status |
|---------|--------|
| Identity (agent_id, agent_type) | ✅ |
| Lifecycle state machine | ✅ |
| Task assignment | ✅ |
| Context loading (Memory Agent) | ✅ |
| Tool resolution (ToolRegistry) | ✅ |
| Model resolution (ModelRegistry) | ✅ |
| Permission enforcement | ✅ |
| Verification | ✅ |
| Retry / reflection loop | ✅ |
| Event emission | ✅ |
| Termination | ✅ |

### Lifecycle

```
READY → SPAWNED → ASSIGNED → RUNNING → VERIFYING → COMPLETED → TERMINATED

Failure path:
RUNNING → VERIFYING → FAILED → REFLECTING → RETRYING → RUNNING
```

Invalid transitions are rejected with `InvalidTransitionError`.

### Task Contract (`contracts/task.py`)

```python
TaskRequest:
  task_id          str          (UUID auto-generated)
  agent_type       str          e.g. "image_generation"
  instruction      str          Natural-language task
  context          TaskContext  Pre-loaded memory context
  constraints      TaskConstraints  max_retries, require_verification, dry_run
  expected_output  ExpectedOutput   output_type, artifact_types
  tools_allowed    list[str]
  metadata         dict
```

### Result Contract (`contracts/result.py`)

```python
TaskResult:
  task_id         str
  agent_id        str
  agent_type      str
  status          TaskStatus  (pending | running | completed | failed | cancelled)
  progress        float 0.0–1.0
  output          str | None
  artifacts       list[Artifact]
  verification    VerificationOutcome
  errors          list[ErrorRecord]
  retry_count     int
  duration_seconds float | None
  metadata        dict
```

### Artifact Contract (`contracts/artifact.py`)

| Type | Fields |
|------|--------|
| `code` | `path`, `mime_type` |
| `image` | `path`, `mime_type`, `is_mock=False` for real |
| `document` | `path`, `mime_type` |
| `reference` | `url` |
| `mock` | `content`, `is_mock=True` — test only |

### Ten Specialist Agents

All ten are **instances of `SpecialistAgent`** with different `AgentConfig`.

| Agent Type | Role | Model | Tools | Permissions |
|-----------|------|-------|-------|-------------|
| `web_development` | Frontend Developer | CODE | filesystem, shell, http | READ, WRITE, WRITE_ARTIFACT, EXECUTE, NETWORK |
| `image_generation` | Image Generator | IMAGE_GENERATION | image_generation | READ, WRITE_ARTIFACT, NETWORK |
| `backend` | Backend Developer | CODE | filesystem, shell, database, http | READ, WRITE, WRITE_ARTIFACT, EXECUTE, DATABASE, NETWORK |
| `database` | Database Engineer | CODE | database, filesystem, shell | READ, WRITE, WRITE_ARTIFACT, DATABASE |
| `api_integration` | API Integration Engineer | CODE | http, filesystem, shell | READ, WRITE, WRITE_ARTIFACT, NETWORK |
| `security` | Security Auditor | CODE/REMOTE_LLM | filesystem | READ, AUDIT, WRITE_ARTIFACT |
| `testing` | QA Engineer | CODE | shell, filesystem, http | READ, WRITE_ARTIFACT, EXECUTE, NETWORK |
| `devops` | DevOps Engineer | CODE | filesystem, shell | READ, WRITE, WRITE_ARTIFACT, EXECUTE |
| `ai_ml` | AI/ML Engineer | CODE/REMOTE_LLM | filesystem, http | READ, WRITE_ARTIFACT, NETWORK |
| `research` | Research Analyst | REMOTE_LLM/CODE | research, http | READ, WRITE_ARTIFACT, NETWORK |

### Tool Registry

All tools implement `BaseTool` and are registered in `ToolRegistry`:

- `FilesystemTool` — read/write/list/stat files (requires READ or WRITE)
- `ShellTool` — controlled command execution with blocked pattern list (requires EXECUTE)
- `HttpTool` — HTTP GET/POST (requires NETWORK)
- `DatabaseTool` — SQL queries (requires DATABASE)
- `ImageGenerationTool` — image generation (requires WRITE_ARTIFACT; returns MODEL_UNAVAILABLE if unconfigured)
- `ResearchTool` — delegates to Memory Agent research (requires NETWORK)

### Model Registry

All model providers implement `ModelProvider` and are registered in `ModelRegistry`:

- `NotConfiguredProvider` — always returns `NOT_CONFIGURED` (sentinel)
- `MockModelProvider` — returns labelled mock responses for testing

Real providers (Ollama, vLLM, OpenAI, ComfyUI) can be registered when credentials are available.

### Server Model Discovery

The `ModelRegistry.inventory()` method returns `ModelInfo` for every registered provider:

```python
ModelInfo:
  provider         str
  model_name       str
  capability       ModelCapability
  is_local         bool
  endpoint         str | None
  gpu_required     bool
  status           ModelStatus  (AVAILABLE | NOT_CONFIGURED | UNAVAILABLE | UNKNOWN)
```

No models are downloaded automatically.

### Permission System

```
Permission:
  READ             — read-only file/data access
  WRITE            — create/modify files
  WRITE_ARTIFACT   — produce output artifacts
  EXECUTE          — run commands/processes
  NETWORK          — HTTP/external network
  DATABASE         — database read/write
  AUDIT            — security audit access
  ADMIN            — unrestricted (NOT granted to any specialist)
```

Checks happen via `PermissionPolicy.require(permission)` before every tool execution.

### Memory Agent Integration

Specialists communicate with the existing Memory Agent through `MemoryClient`:

```
Specialist Agent
      ↓
MemoryClient (integration/memory_client.py)
      ↓
Memory Agent HTTP API (MEMORY_AGENT_URL)
      ↓
Obsidian / Jina / ValidationLayer
```

Trust levels are always preserved:
- `search()` → `RETRIEVED` (from Obsidian, trusted)
- `research()` → `UNVERIFIED` (external, must validate)

No Jina logic is duplicated.

### Verification

`StandardVerifier.verify(task, result)` runs 6 checks:
1. `task_id_match`
2. `status_check`
3. `no_error_check`
4. `artifact_check` (if expected artifact types specified)
5. `output_present`
6. `no_fake_artifacts`

Returns `VerificationOutcome(verdict=PASS|FAIL, checks=[...], reason=...)`.

### Retry / Reflection

```
RUNNING → VERIFYING → FAIL → REFLECTING → RETRYING → RUNNING
```

- Default `max_retries = 2` (configurable per agent and per task)
- Every retry includes a `reflection` note explaining the failure
- Retry count tracked in `TaskResult.retry_count`
- No infinite loops — `RetryLimitExceededError` is raised after limit

### Termination

On `COMPLETED` or after retry limit:
```
COMPLETED → TERMINATED
or
FAILED → TERMINATED
```

The `TaskResult` remains available on `agent.result` after termination.

---

## Manual Testing

```bash
# List all agents
python -c "import sys; sys.path.insert(0,'specialist-agent'); from specialist_agent.run_test import main; main()" -- --list

# Test image generation (no model configured — will report MODEL_UNAVAILABLE)
python -c "import sys; sys.path.insert(0,'specialist-agent'); from specialist_agent.run_test import run_test; run_test('image_generation', 'Generate a futuristic electric car')"

# Test research agent
python -c "import sys; sys.path.insert(0,'specialist-agent'); from specialist_agent.run_test import run_test; run_test('research', 'Find current best practices for securing REST APIs')"

# Test web development agent
python -c "import sys; sys.path.insert(0,'specialist-agent'); from specialist_agent.run_test import run_test; run_test('web_development', 'Create a simple responsive company homepage')"
```

### Running Tests

```bash
# Specialist agent tests only
python -m pytest specialist-agent/tests/ -v

# Memory Agent regression tests
python -m pytest tests/ -v

# Both (separately — different conftest.py)
python -m pytest specialist-agent/tests/ -q
python -m pytest tests/ -q
```

---

## Configuration

All settings are environment-driven. No secrets are hardcoded.

```env
SPECIALIST_ENV=development

# Memory Agent connection
MEMORY_AGENT_URL=http://localhost:8001

# Image model (leave empty = MODEL_UNAVAILABLE)
IMAGE_MODEL_PROVIDER=
IMAGE_MODEL_NAME=
IMAGE_MODEL_ENDPOINT=

# Code model (leave empty = MODEL_UNAVAILABLE)
CODE_MODEL_PROVIDER=
CODE_MODEL_NAME=
CODE_MODEL_ENDPOINT=

# Execution defaults
SPECIALIST_MAX_RETRIES=2
SPECIALIST_TIMEOUT=300
```

---

## FUTURE INTEGRATION

### Master Orchestrator Integration

When the Master Orchestrator is ready, it will:

1. Import `SpecialistAgentRegistry`
2. Call `registry.get_agent(agent_type)` to check capabilities
3. Create `TaskRequest` objects
4. Call `executor.run_task(task)` or `registry.spawn_agent(agent_type)`
5. Consume `TaskResult` objects

**No redesign required** — the contracts are already orchestrator-ready.

### Real Model Providers

Register real providers in `ModelRegistry`:

```python
from specialist_agent.models.base import ModelProvider, ModelCapability, ModelStatus

class OllamaProvider(ModelProvider):
    @property
    def name(self): return "ollama"
    @property
    def capability(self): return ModelCapability.CODE
    def info(self): ...
    def ping(self): ...
    def generate(self, prompt, **kwargs): ...

registry.register(OllamaProvider())
```

### Event Stream

All `AgentEvent` objects (from `agent.events`) can be forwarded to the global Activity feed when it's implemented.

---

## Safety Rules

- ❌ No ADMIN permission granted to any specialist
- ❌ Research agent cannot write to Obsidian directly
- ❌ Image agent never fabricates images when model is unconfigured
- ❌ No models are downloaded automatically
- ❌ No secrets are hardcoded
- ❌ No Jina logic duplicated inside specialists
- ✅ All external evidence starts as UNVERIFIED
- ✅ Trust levels are preserved through the full pipeline
- ✅ Blocked shell commands are refused immediately
- ✅ Every tool execution is permission-checked before running
