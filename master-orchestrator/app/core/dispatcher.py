import uuid
import datetime
from typing import Any, Dict, List
from app.models.dispatch import DispatchAttempt, AttemptStatus

class Dispatcher:
    """
    Dispatches tasks to specialists with deterministic PlanStep → TaskRequest mapping.
    Ensures idempotency keys, correlation tracking, and attempt recording.
    """

    def __init__(self, specialist_client):
        self.specialist_client = specialist_client

    def _infer_artifact_types(self, expected_outputs: List[str]) -> List[str]:
        artifact_types = []
        for out in expected_outputs:
            out_lower = out.lower()
            if any(k in out_lower for k in ("code", "script", "component", "api", "endpoint", "backend", "frontend")):
                artifact_types.append("code")
            elif any(k in out_lower for k in ("image", "picture", "asset", "ui asset")):
                artifact_types.append("image")
            elif any(k in out_lower for k in ("schema", "ddl", "migration", "table", "database")):
                artifact_types.append("schema")
            elif any(k in out_lower for k in ("docker", "container", "pipeline", "ci/cd", "config")):
                artifact_types.append("config")
            elif any(k in out_lower for k in ("report", "audit", "security review", "findings")):
                artifact_types.append("report")
            elif any(k in out_lower for k in ("test", "suite", "qa")):
                artifact_types.append("test_result")
            elif any(k in out_lower for k in ("document", "docs", "guide", "readme")):
                artifact_types.append("document")
            else:
                artifact_types.append("document")
        return list(set(artifact_types)) if artifact_types else ["text"]

    async def dispatch(
        self,
        execution_id: str,
        step: dict,
        attempt_number: int,
        memory_context: dict,
        plan_id: str = "",
        plan_version: int = 1
    ) -> DispatchAttempt:
        attempt_id = str(uuid.uuid4())
        step_id = step.get("step_id") or step.get("stepId")
        specialist_id = step.get("specialist_id") or step.get("specialistId") or ""
        idempotency_key = f"{execution_id}:{step_id}:{attempt_number}"
        
        start_time = datetime.datetime.utcnow()
        attempt = DispatchAttempt(
            attempt_id=attempt_id,
            attempt_number=attempt_number,
            step_id=step_id,
            task_id=attempt_id,
            execution_id=execution_id,
            specialist_id=specialist_id,
            started_at=start_time.isoformat(),
            status=AttemptStatus.RUNNING,
            correlation_id=execution_id,
            idempotency_key=idempotency_key
        )
        
        try:
            # Deterministic PlanStep → TaskRequest mapping
            title = step.get("title", "")
            description = step.get("description", "")
            instruction = f"{title}: {description}" if title and description else (description or title or "Execute step")
            
            expected_outputs = step.get("expected_outputs") or step.get("expectedOutputs") or []
            artifact_types = self._infer_artifact_types(expected_outputs)
            
            failure_policy = step.get("failure_policy") or step.get("failurePolicy") or {}
            max_retries = failure_policy.get("max_retries") or failure_policy.get("maxRetries") or 2
            
            context_items = memory_context.get("items", []) if isinstance(memory_context, dict) else []
            trust_level = memory_context.get("trust_level", "RETRIEVED") if isinstance(memory_context, dict) else "RETRIEVED"

            task_request = {
                "task_id": attempt_id,
                "agent_type": specialist_id,
                "instruction": instruction,
                "context": {
                    "context_items": context_items,
                    "trust_level": trust_level,
                    "extra": {
                        "execution_id": execution_id,
                        "plan_id": plan_id,
                        "plan_version": plan_version,
                        "step_id": step_id,
                        "attempt_id": attempt_id,
                        "attempt_number": attempt_number,
                        "memory_context": memory_context
                    }
                },
                "constraints": {
                    "max_duration_seconds": 300,
                    "max_retries": max_retries,
                    "require_verification": True,
                    "dry_run": False
                },
                "expected_output": {
                    "output_type": "code" if "code" in artifact_types else "text",
                    "artifact_types": artifact_types,
                    "description": "; ".join(expected_outputs) if expected_outputs else "Completed task result"
                },
                "tools_allowed": [],
                "metadata": {
                    "execution_id": execution_id,
                    "plan_id": plan_id,
                    "plan_version": plan_version,
                    "step_id": step_id,
                    "attempt_id": attempt_id,
                    "attempt_number": attempt_number,
                    "idempotency_key": idempotency_key,
                    "verification_criteria": step.get("verification_criteria") or step.get("verificationCriteria") or []
                }
            }
            
            result = await self.specialist_client.dispatch(task_request)
            raw_status = str(result.get("status", "")).lower()
            if raw_status in ("completed", "success"):
                attempt.status = AttemptStatus.COMPLETED
            elif raw_status == "cancelled":
                attempt.status = AttemptStatus.CANCELLED
            else:
                attempt.status = AttemptStatus.FAILED
            
            attempt.result = result
            attempt.model_reference = result.get("metadata", {}).get("model_id") or result.get("model_name")
            attempt.result_reference = f"res:{attempt_id}"

            if attempt.status == AttemptStatus.FAILED:
                errors = result.get("errors", [])
                if errors and isinstance(errors, list):
                    first_err = errors[0]
                    attempt.failure_type = first_err.get("error_code")
                    attempt.error = first_err.get("message")
                else:
                    attempt.error = result.get("output") or "Specialist task failed"
            
            end_time = datetime.datetime.utcnow()
            attempt.completed_at = end_time.isoformat()
            attempt.duration_ms = (end_time - start_time).total_seconds() * 1000.0
        except Exception as e:
            end_time = datetime.datetime.utcnow()
            attempt.status = AttemptStatus.FAILED
            attempt.error = str(e)
            attempt.completed_at = end_time.isoformat()
            attempt.duration_ms = (end_time - start_time).total_seconds() * 1000.0
            
        return attempt


