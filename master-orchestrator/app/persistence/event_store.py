from abc import ABC, abstractmethod
import json
import sqlite3
import threading
from typing import List

from app.models.events import ExecutionEvent


class EventStore(ABC):
    @abstractmethod
    def append(self, event: ExecutionEvent): pass
    
    @abstractmethod
    def get_events(self, execution_id: str) -> List[ExecutionEvent]: pass
    
    @abstractmethod
    def get_events_by_type(self, execution_id: str, event_type: str) -> List[ExecutionEvent]: pass


class InMemoryEventStore(EventStore):
    def __init__(self):
        self.events: List[ExecutionEvent] = []
        self._lock = threading.Lock()
        
    def append(self, event: ExecutionEvent):
        with self._lock:
            self.events.append(event)
        
    def get_events(self, execution_id: str) -> List[ExecutionEvent]:
        with self._lock:
            return [e for e in self.events if e.execution_id == execution_id]
        
    def get_events_by_type(self, execution_id: str, event_type: str) -> List[ExecutionEvent]:
        with self._lock:
            return [e for e in self.events if e.execution_id == execution_id and (e.event_type == event_type or getattr(e.event_type, "value", None) == event_type)]


class SQLiteEventStore(EventStore):
    """
    SQLite-backed append-only audit event store.
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
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_exec ON events(execution_id)
            """)
            conn.commit()

    def append(self, event: ExecutionEvent):
        payload = event.model_dump(mode="json")
        ev_type = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO events (event_id, execution_id, event_type, timestamp, data) VALUES (?, ?, ?, ?, ?)",
                (event.event_id, event.execution_id, ev_type, event.timestamp, json.dumps(payload))
            )
            conn.commit()

    def get_events(self, execution_id: str) -> List[ExecutionEvent]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute(
                "SELECT data FROM events WHERE execution_id = ? ORDER BY id ASC",
                (execution_id,)
            ).fetchall()
            return [ExecutionEvent.model_validate(json.loads(r["data"])) for r in rows]

    def get_events_by_type(self, execution_id: str, event_type: str) -> List[ExecutionEvent]:
        with self._lock, self._get_conn() as conn:
            rows = conn.execute(
                "SELECT data FROM events WHERE execution_id = ? AND event_type = ? ORDER BY id ASC",
                (execution_id, event_type)
            ).fetchall()
            return [ExecutionEvent.model_validate(json.loads(r["data"])) for r in rows]

