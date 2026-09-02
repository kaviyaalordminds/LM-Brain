import os
from app.config.settings import settings
from app.core.state_manager import StateManager
from app.core.scheduler import Scheduler
from app.core.dispatcher import Dispatcher
from app.core.execution_engine import ExecutionEngine
from app.core.orchestrator import MasterOrchestrator
from app.core.recovery_manager import RecoveryManager
from app.core.replanner import Replanner
from app.core.event_bus import EventBus
from app.verification.result_verifier import ResultVerifier
from app.clients.planner_client import PlannerClient
from app.clients.memory_client import MemoryClient
from app.clients.specialist_client import SpecialistClient
from app.persistence.repository import SQLiteExecutionRepository, InMemoryExecutionRepository
from app.persistence.event_store import SQLiteEventStore, InMemoryEventStore

_orchestrator = None

def get_orchestrator() -> MasterOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        if settings.persistence_backend == 'sqlite':
            repo = SQLiteExecutionRepository(settings.sqlite_db_path)
            event_store = SQLiteEventStore(settings.sqlite_db_path)
        else:
            repo = InMemoryExecutionRepository()
            event_store = InMemoryEventStore()

        event_bus = EventBus()
        state_manager = StateManager()
        scheduler = Scheduler(max_concurrent_tasks=settings.max_concurrent_tasks)
        
        planner_client = PlannerClient(base_url=settings.planner_url)
        memory_client = MemoryClient(base_url=settings.memory_url)
        specialist_client = SpecialistClient(memory_client=memory_client)
        
        dispatcher = Dispatcher(specialist_client)
        verifier = ResultVerifier()
        recovery_manager = RecoveryManager()
        replanner = Replanner(planner_client)
        
        engine = ExecutionEngine(
            scheduler=scheduler,
            dispatcher=dispatcher,
            state_manager=state_manager,
            repo=repo,
            event_store=event_store,
            event_bus=event_bus,
            memory_client=memory_client,
            verifier=verifier,
            recovery_manager=recovery_manager,
            replanner=replanner
        )
        
        _orchestrator = MasterOrchestrator(
            repo=repo,
            engine=engine,
            planner=planner_client,
            event_store=event_store,
            event_bus=event_bus,
            replanner=replanner
        )
        
    return _orchestrator
