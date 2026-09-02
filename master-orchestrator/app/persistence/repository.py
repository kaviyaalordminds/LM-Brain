from abc import ABC, abstractmethod
import json
import sqlite3
import threading
from typing import List, Optional

from app.models.execution import Execution
from app.models.dispatch import DispatchAttempt
from app.models.artifacts import LineageArtifact


class ExecutionRepository(ABC):
    @abstractmethod
    def save_execution(self, execution: Execution): pass
    @abstractmethod
    def get_execution(self, execution_id: str) -> Optional[Execution]: pass
    @abstractmethod
    def update_execution(self, execution: Execution): pass
    @abstractmethod
    def list_executions(self) -> List[Execution]: pass
    @abstractmethod
    def save_attempt(self, attempt: DispatchAttempt): pass
    @abstractmethod
    def get_attempts(self, execution_id: str) -> List[DispatchAttempt]: pass
    @abstractmethod
    def save_artifact(self, artifact: LineageArtifact): pass
    @abstractmethod
    def get_artifacts(self, execution_id: str) -> List[LineageArtifact]: pass
    @abstractmethod
    def save_plan_version(self, plan: dict): pass
    @abstractmethod
    def get_plan_versions(self, plan_id: str) -> List[dict]: pass


class InMemoryExecutionRepository(ExecutionRepository):
    def __init__(self):
        self.executions = {}
        self.attempts = []
        self.artifacts = []
        self.plans = []
        self._lock = threading.Lock()
    
    def save_execution(self, execution: Execution):
        with self._lock:
            self.executions[execution.execution_id] = execution
        
    def get_execution(self, execution_id: str) -> Optional[Execution]:
        with self._lock:
            return self.executions.get(execution_id)
        
    def update_execution(self, execution: Execution):
        with self._lock:
            self.executions[execution.execution_id] = execution
        
    def list_executions(self) -> List[Execution]:
        with self._lock:
            return list(self.executions.values())
        
    def save_attempt(self, attempt: DispatchAttempt):
        with self._lock:
            self.attempts.append(attempt)
        
    def get_attempts(self, execution_id: str) -> List[DispatchAttempt]:
        with self._lock:
            return [a for a in self.attempts if a.execution_id == execution_id]
        
    def save_artifact(self, artifact: LineageArtifact):
        with self._lock:
            self.artifacts.append(artifact)
        
    def get_artifacts(self, execution_id: str) -> List[LineageArtifact]:
        with self._lock:
            return [a for a in self.artifacts if a.execution_id == execution_id]
        
    def save_plan_version(self, plan: dict):
        with self._lock:
            self.plans.append(plan)
        
    def get_plan_versions(self, plan_id: str) -> List[dict]:
        with self._lock:
            return [p for p in self.plans if p.get("plan_id") == plan_id or p.get("planId") == plan_id]


class SQLiteExecutionRepository(ExecutionRepository):
    """
    SQLite-backed persistent repository for production & local durability.
    Survives application and server restarts.
    """

    def __init__(self, db_path: str = "orchestrator.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock, self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    idempotency_key TEXT UNIQUE NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plan_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_execution(self, execution: Execution):
        payload = execution.model_dump(mode="json")
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO executions (execution_id, data, updated_at) VALUES (?, ?, ?)",
                (execution.execution_id, json.dumps(payload), execution.updated_at)
            )
            conn.commit()

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        with self._lock, self._get_conn() as conn:
            row = conn.execute("SELECT data FROM executions WHERE execution_id = ?", (execution_id,)).fetchone()
            if row:
                return Execution.model_validate(json.loads(row["data"]))
            return None

    def update_execution(self, execution: Execution):
        self.save_execution(execution)

    def list_executions(self) -> List[Execution]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute("SELECT data FROM executions ORDER BY updated_at DESC").fetchall()
            return [Execution.model_validate(json.loads(r["data"])) for r in rows]

    def save_attempt(self, attempt: DispatchAttempt):
        payload = attempt.model_dump(mode="json")
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO attempts (attempt_id, execution_id, data, idempotency_key) VALUES (?, ?, ?, ?)",
                (attempt.attempt_id, attempt.execution_id, json.dumps(payload), attempt.idempotency_key)
            )
            conn.commit()

    def get_attempts(self, execution_id: str) -> List[DispatchAttempt]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute("SELECT data FROM attempts WHERE execution_id = ?", (execution_id,)).fetchall()
            return [DispatchAttempt.model_validate(json.loads(r["data"])) for r in rows]

    def save_artifact(self, artifact: LineageArtifact):
        payload = artifact.model_dump(mode="json")
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO artifacts (artifact_id, execution_id, data) VALUES (?, ?, ?)",
                (artifact.artifact_id, artifact.execution_id, json.dumps(payload))
            )
            conn.commit()

    def get_artifacts(self, execution_id: str) -> List[LineageArtifact]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute("SELECT data FROM artifacts WHERE execution_id = ?", (execution_id,)).fetchall()
            return [LineageArtifact.model_validate(json.loads(r["data"])) for r in rows]

    def save_plan_version(self, plan: dict):
        plan_id = plan.get("plan_id") or plan.get("planId") or "unknown"
        version = plan.get("plan_version") or plan.get("version") or 1
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT INTO plan_versions (plan_id, version, data) VALUES (?, ?, ?)",
                (plan_id, version, json.dumps(plan))
            )
            conn.commit()

    def get_plan_versions(self, plan_id: str) -> List[dict]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute("SELECT data FROM plan_versions WHERE plan_id = ? ORDER BY version ASC", (plan_id,)).fetchall()
            return [json.loads(r["data"]) for r in rows]

