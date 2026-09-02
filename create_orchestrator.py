import os

base_dir = r'C:\Lordminds\Multiagent\master-orchestrator'
directories = [
    "app/config", "app/api", "app/models", "app/policies",
    "app/clients", "app/registry", "app/core", "app/verification",
    "app/persistence", "tests"
]

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

files_content = {
    "app/models/execution.py": """
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ExecutionPhase(str, Enum):
    INTENT_NORMALIZATION = "INTENT_NORMALIZATION"
    PLANNING = "PLANNING"
    SCHEDULING = "SCHEDULING"
    DISPATCHING = "DISPATCHING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    FINALIZING = "FINALIZING"

class Execution(BaseModel):
    execution_id: str
    request_id: str
    user_request: str
    plan_id: Optional[str] = None
    plan_version: int = 1
    status: ExecutionStatus = ExecutionStatus.CREATED
    phase: ExecutionPhase = ExecutionPhase.INTENT_NORMALIZATION
    created_at: str
    updated_at: str
    completed_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    running_steps: List[str] = Field(default_factory=list)
    blocked_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    attempts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
""",
    "app/models/state.py": """
from enum import Enum

class StepLifecycle(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"

LEGAL_TRANSITIONS = {
    StepLifecycle.PENDING: {StepLifecycle.READY, StepLifecycle.BLOCKED},
    StepLifecycle.READY: {StepLifecycle.QUEUED, StepLifecycle.BLOCKED, StepLifecycle.SKIPPED},
    StepLifecycle.QUEUED: {StepLifecycle.DISPATCHED, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.DISPATCHED: {StepLifecycle.RUNNING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.RUNNING: {StepLifecycle.VERIFYING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.VERIFYING: {StepLifecycle.COMPLETED, StepLifecycle.FAILED},
    StepLifecycle.COMPLETED: set(),
    StepLifecycle.FAILED: {StepLifecycle.READY},
    StepLifecycle.BLOCKED: {StepLifecycle.READY},
    StepLifecycle.SKIPPED: set(),
}
""",
    "app/models/events.py": """
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class EventType(str, Enum):
    EXECUTION_CREATED = "EXECUTION_CREATED"
    PLAN_REQUESTED = "PLAN_REQUESTED"
    PLAN_RECEIVED = "PLAN_RECEIVED"
    STEP_READY = "STEP_READY"
    STEP_QUEUED = "STEP_QUEUED"
    STEP_DISPATCHED = "STEP_DISPATCHED"
    STEP_STARTED = "STEP_STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    REPLAN_REQUESTED = "REPLAN_REQUESTED"
    REPLAN_RECEIVED = "REPLAN_RECEIVED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    EXECUTION_PAUSED = "EXECUTION_PAUSED"
    EXECUTION_RESUMED = "EXECUTION_RESUMED"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    MEMORY_CONTEXT_FETCHED = "MEMORY_CONTEXT_FETCHED"

class ExecutionEvent(BaseModel):
    event_id: str
    event_type: EventType
    execution_id: str
    plan_id: Optional[str] = None
    plan_version: Optional[int] = None
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    attempt_id: Optional[str] = None
    correlation_id: str
    timestamp: str
    payload: Dict[str, Any]
""",
    "app/models/dispatch.py": """
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum

class AttemptStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"

class DispatchRequest(BaseModel):
    dispatch_id: str
    execution_id: str
    plan_id: str
    plan_version: int
    step_id: str
    task_id: str
    attempt_id: str
    specialist_id: str
    idempotency_key: str
    instruction: str
    memory_required: bool
    research_required: bool
    expected_outputs: Dict[str, Any]
    verification_criteria: List[str]
    metadata: Dict[str, Any]

class DispatchAttempt(BaseModel):
    attempt_id: str
    attempt_number: int
    step_id: str
    execution_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: AttemptStatus
    failure_type: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    idempotency_key: str
""",
    "app/models/artifacts.py": """
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class TrustState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    RETRIEVED = "RETRIEVED"

class LineageArtifact(BaseModel):
    artifact_id: str
    execution_id: str
    plan_id: str
    plan_version: int
    step_id: str
    task_id: str
    attempt_id: str
    specialist_id: str
    artifact_type: str
    path: str
    url: str
    content: str
    is_mock: bool
    parent_artifact_ids: List[str]
    source_evidence_refs: List[str]
    trust_state: TrustState
    verification_status: str
    created_at: str
    checksum: Optional[str] = None
""",
    "app/policies/failure_policy.py": """
from enum import Enum

class FailureType(str, Enum):
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"

class FailureClassifier:
    @staticmethod
    def classify(error: Exception | str, error_code: str = "") -> FailureType:
        error_str = str(error).lower()
        if "timeout" in error_str: return FailureType.TIMEOUT
        if "permission" in error_str: return FailureType.PERMISSION_DENIED
        if "verify" in error_str or "verification" in error_str: return FailureType.VERIFICATION_FAILED
        return FailureType.UNKNOWN
""",
    "app/policies/retry_policy.py": """
from .failure_policy import FailureType

NON_RETRYABLE = {
    FailureType.PERMISSION_DENIED,
    FailureType.CANCELLED,
}
REQUIRES_REPLAN = {
    FailureType.CONTRACT_VIOLATION,
    FailureType.VERIFICATION_FAILED,
}

class RetryPolicy:
    @staticmethod
    def should_retry(failure_type: FailureType, attempt_number: int, max_retries: int) -> bool:
        if failure_type in NON_RETRYABLE or failure_type in REQUIRES_REPLAN:
            return False
        return attempt_number < max_retries

    @staticmethod
    def backoff_seconds(attempt_number: int) -> float:
        return float(min(2 ** attempt_number, 30))
""",
    "app/policies/trust_policy.py": """
from app.models.artifacts import TrustState

class TrustPolicy:
    @staticmethod
    def can_use_as_context(trust_state: TrustState) -> bool:
        return trust_state in {TrustState.VALIDATED, TrustState.APPROVED, TrustState.RETRIEVED}

    @staticmethod
    def can_persist_to_memory(trust_state: TrustState) -> bool:
        return trust_state == TrustState.APPROVED

    @staticmethod
    def blocks_production_artifact(trust_state: TrustState) -> bool:
        return trust_state == TrustState.UNVERIFIED
""",
    "app/policies/permission_policy.py": """
class OrchestratorPermissions:
    @staticmethod
    def validate_permissions(permissions: list[str]) -> bool:
        return "ADMIN" not in permissions
""",
    "app/clients/planner_client.py": """
class PlannerUnavailableError(Exception): pass

class PlannerClient:
    async def create_plan(self, user_request: str, context: dict, request_id: str) -> dict:
        return {"plan_id": "dummy", "steps": []}
    
    async def create_recovery_plan(self, original_request: str, current_state: dict) -> dict:
        return {"plan_id": "dummy_recovery", "steps": []}
""",
    "app/clients/memory_client.py": """
class MemoryUnavailableError(Exception): pass

class MemoryClient:
    async def search(self, query: str, task_id: str) -> dict:
        return {}
    async def research(self, query: str, task_id: str) -> dict:
        return {}
    async def get_context(self, task_id: str) -> dict:
        return {}
""",
    "app/clients/specialist_client.py": """
class SpecialistUnavailableError(Exception): pass
class SpecialistDispatchError(Exception): pass

class SpecialistClient:
    async def dispatch(self, task_request: dict) -> dict:
        return {"status": "SUCCESS"}
    async def check_health(self, specialist_id: str) -> bool:
        return True
""",
    "app/registry/specialist_registry.py": """
class SpecialistRegistry:
    @staticmethod
    def get(specialist_id: str) -> dict:
        return {"specialist_id": specialist_id, "enabled": True}
    
    @staticmethod
    def is_enabled(specialist_id: str) -> bool:
        return True
""",
    "app/registry/capability_registry.py": """
class CapabilityRegistry:
    pass
""",
    "app/core/state_manager.py": """
import threading
from app.models.state import LEGAL_TRANSITIONS, StepLifecycle

class IllegalTransitionError(Exception): pass

class StateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.states = {}

    def transition(self, execution_id: str, step_id: str, new_state: StepLifecycle):
        with self._lock:
            key = f"{execution_id}:{step_id}"
            current_state = self.states.get(key, StepLifecycle.PENDING)
            if new_state not in LEGAL_TRANSITIONS[current_state] and new_state != current_state:
                raise IllegalTransitionError(f"Cannot transition from {current_state} to {new_state}")
            self.states[key] = new_state
            return current_state, new_state
""",
    "app/core/scheduler.py": """
class Scheduler:
    def tick(self, execution_id, step_states, plan_dependencies):
        return []
""",
    "app/core/dispatcher.py": """
class Dispatcher:
    async def dispatch(self, execution_id, step, attempt_number, memory_context):
        pass
""",
    "app/core/execution_engine.py": """
class ExecutionEngine:
    async def run(self, execution_id: str):
        pass
""",
    "app/core/recovery_manager.py": """
class RecoveryManager:
    def analyze_failure(self, step_id, failure_type, attempt_number, max_retries):
        pass
    def compute_recovery_context(self, execution):
        return {}
""",
    "app/core/replanner.py": """
class Replanner:
    async def request_recovery_plan(self, execution, failure_context):
        return {}
""",
    "app/core/event_bus.py": """
class EventBus:
    def publish(self, event):
        pass
    def subscribe(self, execution_id, callback):
        return "sub_id"
    def unsubscribe(self, subscription_id):
        pass
""",
    "app/verification/result_verifier.py": """
class VerificationGateResult:
    def __init__(self, passed, checks, reasons):
        self.passed = passed
        self.checks = checks
        self.reasons = reasons

class ResultVerifier:
    def verify(self, task_result, plan_step, attempt):
        return VerificationGateResult(True, [], [])
""",
    "app/persistence/repository.py": """
class ExecutionRepository:
    pass

class InMemoryExecutionRepository(ExecutionRepository):
    pass
""",
    "app/persistence/event_store.py": """
class EventStore:
    pass

class InMemoryEventStore(EventStore):
    pass
""",
    "app/api/executions.py": """
from fastapi import APIRouter
router = APIRouter()
@router.post("/api/v1/executions")
async def create_execution():
    return {"execution_id": "123", "status": "CREATED"}
""",
    "app/api/control.py": """
from fastapi import APIRouter
router = APIRouter()
""",
    "app/api/health.py": """
from fastapi import APIRouter
router = APIRouter()
@router.get("/api/v1/health")
async def health():
    return {"status": "healthy"}
""",
    "app/main.py": """
from fastapi import FastAPI
from app.api import executions, control, health

app = FastAPI()
app.include_router(executions.router)
app.include_router(control.router)
app.include_router(health.router)
""",
    "tests/test_models.py": """
def test_dummy():
    assert True
""",
    "requirements.txt": """
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
anyio>=4.3.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.14.0
""",
    "pyproject.toml": "",
    ".env.example": """
MASTER_ORCHESTRATOR_PORT=8000
PLANNER_URL=http://127.0.0.1:8002
MEMORY_URL=http://127.0.0.1:8001
MAX_CONCURRENT_TASKS=5
DEFAULT_TASK_TIMEOUT=300
DEFAULT_RETRY_LIMIT=3
LOG_LEVEL=INFO
PERSISTENCE_BACKEND=memory
""",
    ".gitignore": "*.pyc\\n__pycache__\\n.pytest_cache\\n",
    "README.md": "# Master Orchestrator"
}

for path, content in files_content.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\\n")
