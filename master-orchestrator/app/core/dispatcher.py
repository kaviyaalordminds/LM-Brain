from app.models.dispatch import DispatchAttempt, AttemptStatus
import uuid
import datetime

class Dispatcher:
    def __init__(self, specialist_client):
        self.specialist_client = specialist_client

    async def dispatch(self, execution_id: str, step: dict, attempt_number: int, memory_context: dict) -> DispatchAttempt:
        attempt_id = str(uuid.uuid4())
        idempotency_key = f"{execution_id}:{step['step_id']}:{attempt_id}"
        
        attempt = DispatchAttempt(
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            step_id=step['step_id'],
            execution_id=execution_id,
            started_at=datetime.datetime.utcnow().isoformat(),
            status=AttemptStatus.RUNNING,
            idempotency_key=idempotency_key
        )
        
        try:
            # We assume step has necessary details, create TaskRequest
            task_request = {
                "task_id": attempt_id,
                "agent_type": step.get("specialist_id"),
                "instruction": step.get("description"),
                "context": {"context_items": [], "trust_level": "VALIDATED", "extra": memory_context},
                "constraints": {"max_duration_seconds": 300, "max_retries": 3, "require_verification": True, "dry_run": False},
                "expected_output": {"output_type": "text", "artifact_types": [], "description": "result"},
                "tools_allowed": [],
                "metadata": {}
            }
            
            result = await self.specialist_client.dispatch(task_request)
            attempt.status = AttemptStatus.COMPLETED
            attempt.result = result
            attempt.completed_at = datetime.datetime.utcnow().isoformat()
        except Exception as e:
            attempt.status = AttemptStatus.FAILED
            attempt.error = str(e)
            attempt.completed_at = datetime.datetime.utcnow().isoformat()
            
        return attempt
