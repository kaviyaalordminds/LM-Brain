from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class ExecutionContext(BaseModel):
    """
    Canonical ExecutionContext.
    Preserves strict runtime identity across Master, Planner, Dispatcher,
    Specialist Agent, Verification, Lineage Artifacts, Events, and Persistence.
    No component should drop or lose execution identity.
    """
    execution_id: str
    plan_id: str = "unknown"
    plan_version: int = 1
    step_id: str = ""
    task_id: str = ""
    attempt_id: str = ""
    specialist_id: str = ""
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def derive_step_context(
        self,
        step_id: str,
        specialist_id: str,
        attempt_id: str = "",
        task_id: str = "",
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> "ExecutionContext":
        """Derive an immutable sub-context for a specific step or attempt."""
        new_meta = dict(self.metadata)
        if extra_metadata:
            new_meta.update(extra_metadata)

        return ExecutionContext(
            execution_id=self.execution_id,
            plan_id=self.plan_id,
            plan_version=self.plan_version,
            step_id=step_id,
            task_id=task_id or attempt_id or str(uuid.uuid4()),
            attempt_id=attempt_id,
            specialist_id=specialist_id,
            correlation_id=self.correlation_id,
            metadata=new_meta
        )
