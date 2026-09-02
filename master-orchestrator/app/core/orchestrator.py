from app.models.execution import Execution, ExecutionStatus

class MasterOrchestrator:
    def __init__(self, repo, engine, planner):
        self.repo = repo
        self.engine = engine
        self.planner = planner

    async def create_execution(self, user_request: str, context: dict) -> Execution:
        import uuid
        import datetime
        exec_id = str(uuid.uuid4())
        execution = Execution(
            execution_id=exec_id,
            request_id=str(uuid.uuid4()),
            user_request=user_request,
            created_at=datetime.datetime.utcnow().isoformat(),
            updated_at=datetime.datetime.utcnow().isoformat(),
            correlation_id=exec_id
        )
        self.repo.save_execution(execution)
        return execution

    async def start_execution(self, execution_id: str) -> None:
        execution = self.repo.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.RUNNING
            self.repo.update_execution(execution)
            await self.engine.run(execution_id)

    async def pause(self, execution_id: str) -> None:
        execution = self.repo.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.PAUSED
            self.repo.update_execution(execution)

    async def resume(self, execution_id: str) -> None:
        execution = self.repo.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.RUNNING
            self.repo.update_execution(execution)

    async def cancel(self, execution_id: str) -> None:
        execution = self.repo.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED
            self.repo.update_execution(execution)

    async def get_execution(self, execution_id: str) -> Execution:
        return self.repo.get_execution(execution_id)

    async def get_events(self, execution_id: str) -> list:
        return []

    async def health_check(self) -> dict:
        return {"status": "healthy", "services": {}}
