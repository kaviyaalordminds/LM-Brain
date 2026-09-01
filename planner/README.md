# Planner Agent

The **Planner Agent** is the planning service for the Autonomous AI Workforce. It ingests natural-language user requests and produces validated, dependency-resolved, structured execution plans for the future Master Orchestrator.

## Architectural Boundary

```
USER REQUEST
     ↓
PLANNER AGENT (this service)
     ↓
VALIDATED EXECUTION PLAN (READY)
     ↓
MASTER ORCHESTRATOR (future)
     ↓
SPECIALIST AGENTS (execution)
```

The Planner:
- **MUST NOT** execute tasks or tools
- **MUST NOT** call models or external LLMs
- **MUST NOT** call the Memory Agent directly
- **MUST NOT** call Jina or perform research directly
- **MUST NOT** modify physical storage outside the in-memory PlanStore

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health check endpoint |
| `POST` | `/api/v1/plans` | Create a validated execution plan |
| `GET` | `/api/v1/plans/{plan_id}` | Retrieve a plan by ID |
| `POST` | `/api/v1/plans/{plan_id}/validate` | Validate an existing plan against 15 rules |
| `GET` | `/api/v1/plans/{plan_id}/status` | Get plan status and progress summary |

## Running Locally

```powershell
cd C:\Lordminds\Multiagent\planner
python -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

## Running Tests

```powershell
cd C:\Lordminds\Multiagent\planner
python -m pytest tests/ -v
```
