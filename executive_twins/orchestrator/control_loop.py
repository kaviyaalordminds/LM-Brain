"""
Authoritative implementation of the Autonomous Control Loop.
Implements the bounded:
Perceive -> Retrieve Knowledge -> Reason / Plan -> Validate Plan -> Select Capabilities ->
Execute Step -> Observe -> Verify -> [Success: Deliver & Remember | Failure: Diagnose & Re-plan]
"""

from datetime import datetime, timezone
import os
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from executive_twins.client.agent_adapter import ISpecialistAgentAdapter
from executive_twins.client.registry_client import ISpecialistRegistryClient
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.memory.interfaces import IKnowledgeMemoryLayer
from executive_twins.orchestrator.interfaces import (
    IControlLoop,
    IMemoryWritebackHandler,
    IPerceptionEngine,
)
from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationState,
    OrchestrationStatus,
    StepExecutionRecord,
)
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.reasoning.interfaces import IReasoningService
from executive_twins.reasoning.models import (
    ReasoningMode,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
)
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    FailureState,
    SecurityContext,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    TypedEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.knowledge import (
    CompanyKnowledgeRequest,
    CompanyKnowledgeResponse,
    KnowledgeOutcomeStatus,
    ObsidianDocument,
)
from executive_twins.schemas.specialist import CapabilityRequirement, SpecialistSelectionResult
from executive_twins.utils.audit_logger import AuditLogger


class StandardPerceptionEngine(IPerceptionEngine):
    """
    Standard perception engine normalizes incoming requests and validates baseline parameters.
    """

    def perceive(
        self, request: OrchestrationRequest
    ) -> Tuple[bool, OrchestrationRequest, Optional[str]]:
        if not request.user_goal or not request.user_goal.strip():
            return False, request, "PERCEPTION_FAILED: user_goal cannot be empty."

        if not request.security_context.is_authenticated:
            return False, request, "SECURITY_DENIED: SecurityContext is unauthenticated."

        # Defense-in-depth check for raw execution injection
        goal_lower = request.user_goal.lower()
        forbidden_patterns = [
            "powershell",
            "cmd.exe",
            "cmd /c",
            "bash -c",
            "sh -c",
            "shell_exec",
            "os.system",
            "subprocess",
            "eval(",
            "exec(",
        ]
        for pattern in forbidden_patterns:
            if pattern in goal_lower:
                return (
                    False,
                    request,
                    f"SECURITY_VIOLATION: Request goal contains forbidden execution pattern '{pattern}'.",
                )

        normalized = OrchestrationRequest(
            request_id=request.request_id,
            user_goal=request.user_goal.strip(),
            context=dict(request.context),
            success_criteria=list(request.success_criteria) or ["Verify completion of all plan steps."],
            available_capabilities=list(request.available_capabilities),
            metadata=dict(request.metadata),
            security_context=request.security_context,
            require_twin_evaluation=request.require_twin_evaluation,
            require_memory_writeback=request.require_memory_writeback,
        )
        return True, normalized, None


class StandardMemoryWritebackHandler(IMemoryWritebackHandler):
    """
    Persists approved workflow completion state and artifacts to Company Obsidian via Knowledge Layer.
    Never directly writes to the host filesystem outside the knowledge abstraction.
    """

    def __init__(self, knowledge_layer: Optional[IKnowledgeMemoryLayer] = None) -> None:
        self.knowledge_layer = knowledge_layer

    def writeback(
        self, result: OrchestrationResult, security_context: SecurityContext
    ) -> Tuple[bool, Optional[str]]:
        if not self.knowledge_layer:
            return True, "No knowledge layer attached; writeback skipped."

        if result.final_status != OrchestrationStatus.COMPLETED:
            return False, "Cannot write back non-completed workflow state to permanent knowledge."

        try:
            # Construct validated facts from completed steps
            facts: List[FactItem] = []
            for step in result.completed_steps:
                statement = f"Workflow '{result.request_id}' completed step '{step.step_id}' ({step.required_capability}): {step.objective}"
                facts.append(
                    FactItem(
                        statement=statement,
                        state=FactState.FACT,
                        source=f"workflow_execution_{result.request_id}",
                    )
                )

            # Build memory document
            doc_id = f"mem_workflow_{result.request_id}"
            doc = ObsidianDocument(
                document_id=doc_id,
                vault_path=f"company_knowledge/workflows/{doc_id}.md",
                title=f"Workflow Execution Memory: {result.request_id}",
                content=f"Workflow {result.request_id} executed successfully with {len(result.completed_steps)} completed steps.\nFinal message: {result.final_message}",
                facts=facts,
                confidence=1.0,
            )

            # Persist via obsidian adapter if available on knowledge layer
            if hasattr(self.knowledge_layer, "obsidian_adapter") and self.knowledge_layer.obsidian_adapter:
                persistence_res = self.knowledge_layer.obsidian_adapter.store_document(doc)
                if persistence_res.success:
                    return True, f"Successfully persisted execution state to Obsidian document '{doc_id}'."
                else:
                    return False, f"Obsidian persistence rejected: {persistence_res.error_message if hasattr(persistence_res, 'error_message') else 'Unknown error'}"

            return True, "Knowledge layer writeback acknowledged."
        except Exception as e:
            return False, f"Memory writeback exception: {str(e)}"


class AutonomousControlLoop(IControlLoop):
    """
    Bounded Autonomous Control Loop orchestrating multi-agent workforce tasks.
    """

    def __init__(
        self,
        reasoning_service: IReasoningService,
        registry_client: ISpecialistRegistryClient,
        agent_adapter: ISpecialistAgentAdapter,
        knowledge_layer: Optional[IKnowledgeMemoryLayer] = None,
        twin_orchestrator: Optional[TwinOrchestrator] = None,
        perception_engine: Optional[IPerceptionEngine] = None,
        writeback_handler: Optional[IMemoryWritebackHandler] = None,
    ) -> None:
        self.reasoning_service = reasoning_service
        self.registry_client = registry_client
        self.agent_adapter = agent_adapter
        self.knowledge_layer = knowledge_layer
        self.twin_orchestrator = twin_orchestrator
        self.perception_engine = perception_engine or StandardPerceptionEngine()
        self.writeback_handler = writeback_handler or StandardMemoryWritebackHandler(knowledge_layer)

    def run(
        self, request: OrchestrationRequest, config: OrchestrationConfig
    ) -> OrchestrationResult:
        """
        Execute the complete autonomous control loop.
        """
        start_time = time.time()

        # 1. Audit Log: ORCHESTRATION_STARTED
        AuditLogger.log_event(
            "ORCHESTRATION_STARTED",
            {
                "request_id": request.request_id,
                "goal": request.user_goal,
                "security_clearance": request.security_context.clearance_level,
            },
        )

        state = OrchestrationState(request=request)

        # 2. PERCEIVE / INTENT
        state.current_status = OrchestrationStatus.PERCEIVING
        is_perceived, norm_req, perc_err = self.perception_engine.perceive(request)
        if not is_perceived:
            AuditLogger.log_event(
                "ORCHESTRATION_FAILED",
                {"request_id": request.request_id, "reason": perc_err, "stage": "perception"},
            )
            return self._build_final_result(
                state, OrchestrationStatus.FAILED, perc_err or "Perception failed.", start_time
            )

        state.request = norm_req
        AuditLogger.log_event(
            "PERCEPTION_COMPLETED",
            {"request_id": norm_req.request_id, "goal": norm_req.user_goal},
        )

        # 3. EXECUTIVE TWIN EVALUATION (Conditional)
        if norm_req.require_twin_evaluation and self.twin_orchestrator:
            twin = self.twin_orchestrator.resolve_twin(norm_req.user_goal)
            if twin:
                AuditLogger.log_event(
                    "twin.activated",
                    {"twin_id": twin.config.twin_id, "role": twin.config.role},
                )
                twin_rec = self.twin_orchestrator.process_request(
                    request_text=norm_req.user_goal,
                    context=norm_req.context,
                    security_context=norm_req.security_context,
                )
                state.executive_twin_recommendation = twin_rec

                # If Twin encountered missing capabilities, fail early
                if twin_rec.missing_capabilities:
                    AuditLogger.log_event(
                        "ORCHESTRATION_FAILED",
                        {
                            "request_id": norm_req.request_id,
                            "reason": f"Twin missing capabilities: {twin_rec.missing_capabilities}",
                        },
                    )
                    return self._build_final_result(
                        state,
                        OrchestrationStatus.BLOCKED,
                        f"Executive Twin identified missing capabilities: {twin_rec.missing_capabilities}",
                        start_time,
                    )

        # 4. RETRIEVE KNOWLEDGE
        retrieved_facts: List[FactItem] = []
        if self.knowledge_layer:
            knowledge_req = CompanyKnowledgeRequest(
                request_id=f"k_{norm_req.request_id}",
                task_context=norm_req.user_goal,
                required_knowledge=norm_req.user_goal,
                min_confidence=config.min_confidence,
            )
            k_resp = self.knowledge_layer.request_company_knowledge(knowledge_req)
            if k_resp.status == KnowledgeOutcomeStatus.KNOWLEDGE_FOUND and k_resp.facts:
                retrieved_facts = [f for f in k_resp.facts if f.state == FactState.FACT]
                AuditLogger.log_event(
                    "KNOWLEDGE_RETRIEVED",
                    {
                        "request_id": norm_req.request_id,
                        "facts_count": len(retrieved_facts),
                    },
                )

        # 5. DISCOVER REGISTERED CAPABILITIES
        available_caps = list(norm_req.available_capabilities)
        if not available_caps:
            # Fetch all capabilities from registry client
            all_specialists = []
            if hasattr(self.registry_client, "list_all_specialists"):
                all_specialists = self.registry_client.list_all_specialists()
            elif hasattr(self.registry_client, "get_all_specialists"):
                all_specialists = self.registry_client.get_all_specialists()
            for spec in all_specialists:
                for cap in spec.capabilities:
                    if cap.name not in available_caps:
                        available_caps.append(cap.name)

        # 6. REASON / PLAN
        state.current_status = OrchestrationStatus.PLANNING
        AuditLogger.log_event(
            "REASONING_STARTED",
            {"request_id": norm_req.request_id, "capabilities_count": len(available_caps)},
        )

        reasoning_req = ReasoningRequest(
            request_id=norm_req.request_id,
            user_goal=norm_req.user_goal,
            context=norm_req.context,
            available_capabilities=available_caps,
            relevant_company_knowledge=retrieved_facts,
            success_criteria=norm_req.success_criteria,
            mode=ReasoningMode.PLAN,
            security_context=norm_req.security_context,
            metadata=norm_req.metadata,
        )

        reasoning_resp = self.reasoning_service.reason(reasoning_req)

        # 7. VALIDATE PLAN & HANDLE REASONING OUTCOME
        state.current_status = OrchestrationStatus.VALIDATING
        if reasoning_resp.status == ReasoningStatus.NEEDS_INFORMATION:
            state.unresolved_information = reasoning_resp.required_information or reasoning_resp.unresolved_questions
            AuditLogger.log_event(
                "ORCHESTRATION_COMPLETED",
                {"request_id": norm_req.request_id, "status": "NEEDS_INFORMATION"},
            )
            return self._build_final_result(
                state,
                OrchestrationStatus.NEEDS_INFORMATION,
                f"Workflow requires additional information: {state.unresolved_information}",
                start_time,
            )

        if reasoning_resp.status != ReasoningStatus.SUCCESS:
            AuditLogger.log_event(
                "ORCHESTRATION_FAILED",
                {
                    "request_id": norm_req.request_id,
                    "reason": reasoning_resp.warnings or "Reasoning model failed to generate plan.",
                },
            )
            return self._build_final_result(
                state,
                OrchestrationStatus.FAILED,
                f"Reasoning failure: {reasoning_resp.warnings}",
                start_time,
            )

        if not reasoning_resp.structured_plan:
            # Decision only
            state.final_result = reasoning_resp.decision or "Reasoning decision generated."
            AuditLogger.log_event(
                "ORCHESTRATION_COMPLETED",
                {"request_id": norm_req.request_id, "status": "COMPLETED"},
            )
            return self._build_final_result(
                state, OrchestrationStatus.COMPLETED, state.final_result, start_time
            )

        state.current_plan = reasoning_resp.structured_plan
        AuditLogger.log_event(
            "PLAN_VALIDATED",
            {
                "request_id": norm_req.request_id,
                "plan_id": state.current_plan.plan_id,
                "steps_count": len(state.current_plan.steps),
            },
        )

        # 8. EXECUTION LOOP
        state.current_status = OrchestrationStatus.EXECUTING

        while (
            state.current_plan
            and state.current_step_index < len(state.current_plan.steps)
            and state.iteration_count < config.max_iterations
        ):
            # Check timeout
            if time.time() - start_time > config.timeout_seconds:
                AuditLogger.log_event(
                    "ORCHESTRATION_FAILED",
                    {"request_id": norm_req.request_id, "reason": "TIMEOUT_EXCEEDED"},
                )
                return self._build_final_result(
                    state,
                    OrchestrationStatus.FAILED,
                    f"Workflow exceeded timeout limit of {config.timeout_seconds}s.",
                    start_time,
                )

            # Check consecutive failure limit
            if state.consecutive_failure_count >= config.max_consecutive_failures:
                AuditLogger.log_event(
                    "ORCHESTRATION_FAILED",
                    {
                        "request_id": norm_req.request_id,
                        "reason": f"Consecutive failure limit ({config.max_consecutive_failures}) exceeded.",
                    },
                )
                break

            state.iteration_count += 1
            step = state.current_plan.steps[state.current_step_index]
            step_record = StepExecutionRecord(
                step_id=step.step_id,
                objective=step.objective,
                required_capability=step.required_capability,
                started_at=datetime.now(timezone.utc),
            )

            # Step 8A: Capability Selection
            state.current_status = OrchestrationStatus.SELECTING_CAPABILITIES
            req_cap = CapabilityRequirement(
                capability_name=step.required_capability,
                description=step.objective or f"Execute {step.required_capability}",
            )
            sel_results = self.registry_client.discover_specialists(
                [req_cap], norm_req.security_context
            )

            selected_specialist = None
            if sel_results and sel_results[0].selected_specialist:
                selected_specialist = sel_results[0].selected_specialist
                step_record.specialist_id = selected_specialist.specialist_id
                state.selected_specialists[step.required_capability] = selected_specialist.specialist_id

                AuditLogger.log_event(
                    "CAPABILITY_SELECTED",
                    {
                        "step_id": step.step_id,
                        "capability": step.required_capability,
                        "specialist_id": selected_specialist.specialist_id,
                    },
                )
            else:
                step_record.status = "FAILED"
                step_record.error = f"NO_REGISTERED_SPECIALIST_AVAILABLE for capability '{step.required_capability}'."
                step_record.completed_at = datetime.now(timezone.utc)
                state.failed_steps.append(step_record)
                state.consecutive_failure_count += 1

                AuditLogger.log_event(
                    "SPECIALIST_SELECTION_FAILED",
                    {"step_id": step.step_id, "capability": step.required_capability},
                )

                # Attempt recovery or break
                if not self._handle_step_failure(state, step_record, norm_req, config, available_caps, retrieved_facts):
                    break
                continue

            # Step 8B: Specialist Execution
            state.current_status = OrchestrationStatus.EXECUTING
            step_inputs = dict(step.parameters)
            if "workspace_id" not in step_inputs:
                step_inputs["workspace_id"] = "default"
            if step.required_capability == "file_list":
                rel = step_inputs.get("relative_path", step_inputs.get("path", ""))
                if "." in os.path.basename(rel) and not rel.endswith("."):
                    step_inputs["relative_path"] = ""
                else:
                    step_inputs["relative_path"] = "" if rel == "." else rel
                step_inputs["path"] = step_inputs["relative_path"]
            else:
                if "relative_path" not in step_inputs and "path" in step_inputs:
                    step_inputs["relative_path"] = step_inputs["path"]
                if "path" not in step_inputs and "relative_path" in step_inputs:
                    step_inputs["path"] = step_inputs["relative_path"]
            if "content" not in step_inputs and "code" in step_inputs:
                step_inputs["content"] = step_inputs["code"]
            if "code" not in step_inputs and "content" in step_inputs:
                step_inputs["code"] = step_inputs["content"]

            del_req = DelegationRequest(
                delegation_id=f"del_{uuid.uuid4().hex[:8]}",
                parent_task_id=norm_req.request_id,
                executive_twin_id="master_orchestrator",
                specialist_id=selected_specialist.specialist_id,
                objective=step.objective,
                task=step.objective,
                required_capabilities=[step.required_capability],
                expected_output=step.expected_output or "Step execution output",
                success_criteria=[step.verification_requirement] if step.verification_requirement else ["Exit code 0"],
                inputs=step_inputs,
                security_context=norm_req.security_context,
            )

            AuditLogger.log_event(
                "SPECIALIST_DELEGATED",
                {
                    "delegation_id": del_req.delegation_id,
                    "specialist_id": del_req.specialist_id,
                    "step_id": step.step_id,
                },
            )

            step_start = time.time()
            if hasattr(self.agent_adapter, "execute_delegation"):
                del_result = self.agent_adapter.execute_delegation(del_req)
            elif hasattr(self.agent_adapter, "dispatch_delegation"):
                del_result = self.agent_adapter.dispatch_delegation(del_req)
            else:
                raise AttributeError("Agent adapter has neither execute_delegation nor dispatch_delegation method.")
            step_record.duration_seconds = time.time() - step_start
            step_record.completed_at = datetime.now(timezone.utc)

            # Step 8C: Observe & Verify
            state.current_status = OrchestrationStatus.OBSERVING
            step_record.output = del_result.output
            step_record.artifacts = list(del_result.artifacts)
            step_record.evidence_ids = [e.evidence_id for e in del_result.evidence.items]

            # Ingest evidence into state
            for ev in del_result.evidence.items:
                state.evidence_set.items.append(ev)
                state.observations.append(ev)

            for art in del_result.artifacts:
                if art not in state.artifacts:
                    state.artifacts.append(art)

            AuditLogger.log_event(
                "EXECUTION_COMPLETED",
                {
                    "step_id": step.step_id,
                    "delegation_id": del_req.delegation_id,
                    "status": del_result.status.value if hasattr(del_result.status, "value") else str(del_result.status),
                    "evidence_count": len(del_result.evidence.items),
                },
            )

            AuditLogger.log_event(
                "OBSERVATION_RECORDED",
                {
                    "step_id": step.step_id,
                    "output_snippet": (del_result.output or "")[:100],
                    "artifacts": del_result.artifacts,
                },
            )

            state.current_status = OrchestrationStatus.VERIFYING
            is_successful = (
                del_result.status == "SUCCESS"
                and del_result.verification_status != VerificationStatus.FAILED
                and not del_result.errors
            )
            if is_successful:
                step_record.status = "COMPLETED"
                state.completed_steps.append(step_record)
                state.consecutive_failure_count = 0
                state.outputs[step.step_id] = del_result.output
                state.current_step_index += 1

                AuditLogger.log_event(
                    "VERIFICATION_COMPLETED",
                    {"step_id": step.step_id, "status": "VERIFIED"},
                )
            else:
                step_record.status = "FAILED"
                step_record.error = (
                    del_result.errors[0] if del_result.errors else (del_result.output or "Specialist execution failed.")
                )
                state.failed_steps.append(step_record)
                state.consecutive_failure_count += 1

                AuditLogger.log_event(
                    "VERIFICATION_COMPLETED",
                    {"step_id": step.step_id, "status": "FAILED", "error": step_record.error},
                )

                # Attempt Failure Recovery
                if not self._handle_step_failure(state, step_record, norm_req, config, available_caps, retrieved_facts):
                    break

        # 9. OUTCOME DETERMINATION
        total_steps = len(state.current_plan.steps) if state.current_plan else 0
        completed_count = len(state.completed_steps)
        failed_count = len(state.failed_steps)

        # Collect skipped steps if plan was partially executed
        if state.current_plan and state.current_step_index < total_steps:
            for i in range(state.current_step_index, total_steps):
                skipped_step = state.current_plan.steps[i]
                if not any(s.step_id == skipped_step.step_id for s in state.completed_steps + state.failed_steps):
                    state.skipped_steps.append(
                        StepExecutionRecord(
                            step_id=skipped_step.step_id,
                            objective=skipped_step.objective,
                            required_capability=skipped_step.required_capability,
                            status="SKIPPED",
                        )
                    )

        if state.current_step_index >= total_steps and total_steps > 0:
            final_status = OrchestrationStatus.COMPLETED
            recovery_suffix = f" (after {state.recovery_count} recovery attempt(s))." if state.recovery_count > 0 else "."
            msg = f"All {total_steps} plan step(s) completed and verified successfully{recovery_suffix}"
        elif completed_count > 0:
            final_status = OrchestrationStatus.PARTIAL
            msg = f"Workflow completed partially: {completed_count} succeeded, {failed_count} failed, {len(state.skipped_steps)} skipped."
        else:
            final_status = OrchestrationStatus.FAILED
            msg = f"Workflow failed: {failed_count} step(s) failed."

        # 10. WRITEBACK TO OBSIDIAN (Remember)
        result = self._build_final_result(state, final_status, msg, start_time)

        if final_status == OrchestrationStatus.COMPLETED and norm_req.require_memory_writeback:
            wb_success, wb_msg = self.writeback_handler.writeback(result, norm_req.security_context)
            result.memory_writeback_status = "SUCCESS" if wb_success else "FAILED"
            AuditLogger.log_event(
                "MEMORY_WRITEBACK_COMPLETED",
                {"request_id": norm_req.request_id, "status": result.memory_writeback_status, "message": wb_msg},
            )

        # 11. Final Audit Log
        if final_status == OrchestrationStatus.COMPLETED:
            AuditLogger.log_event(
                "ORCHESTRATION_COMPLETED",
                {
                    "request_id": norm_req.request_id,
                    "completed_steps": completed_count,
                    "duration_seconds": result.duration_seconds,
                },
            )
        else:
            AuditLogger.log_event(
                "ORCHESTRATION_FAILED",
                {
                    "request_id": norm_req.request_id,
                    "status": final_status.value,
                    "completed_steps": completed_count,
                    "failed_steps": failed_count,
                },
            )

        return result

    def _handle_step_failure(
        self,
        state: OrchestrationState,
        step_record: StepExecutionRecord,
        norm_req: OrchestrationRequest,
        config: OrchestrationConfig,
        available_caps: List[str],
        retrieved_facts: List[FactItem],
    ) -> bool:
        """
        Handle a failed execution step by attempting evidence-driven re-planning.
        Returns True if a revised plan was generated and execution can continue, False otherwise.
        """
        if state.recovery_count >= config.max_recovery_attempts:
            AuditLogger.log_event(
                "RECOVERY_LIMIT_EXCEEDED",
                {
                    "request_id": norm_req.request_id,
                    "recovery_count": state.recovery_count,
                    "max_attempts": config.max_recovery_attempts,
                },
            )
            return False

        state.current_status = OrchestrationStatus.RECOVERING
        state.recovery_count += 1

        AuditLogger.log_event(
            "RECOVERY_STARTED",
            {
                "request_id": norm_req.request_id,
                "step_id": step_record.step_id,
                "recovery_attempt": state.recovery_count,
                "error": step_record.error,
            },
        )

        # Build empirical failure evidence
        failure_ev_items: List[TypedEvidence] = [
            ExecutionLogEvidence(
                evidence_id=f"ev_fail_log_{state.recovery_count}",
                execution_id=step_record.step_id,
                log_snippet=step_record.error or "Step execution failed",
                exit_code=1,
            )
        ]
        failure_set = EvidenceSet(items=failure_ev_items)

        state.current_status = OrchestrationStatus.REPLANNING
        replan_req = ReasoningRequest(
            request_id=f"{norm_req.request_id}_rec_{state.recovery_count}",
            user_goal=norm_req.user_goal,
            context=norm_req.context,
            available_capabilities=available_caps,
            relevant_company_knowledge=retrieved_facts,
            current_state={"failed_step": step_record.step_id, "error": step_record.error},
            previous_actions=[{"step_id": s.step_id, "status": s.status} for s in state.completed_steps],
            observations=state.observations + failure_ev_items,
            failures=[{"step_id": step_record.step_id, "error": step_record.error}],
            success_criteria=norm_req.success_criteria,
            mode=ReasoningMode.RECOVER,
            security_context=norm_req.security_context,
            metadata={"recovery_iteration": state.recovery_count},
        )

        replan_resp = self.reasoning_service.replan_from_failure(
            request=replan_req,
            failure_evidence=failure_set,
            failure_reason=step_record.error or "Unknown failure",
            current_iteration=state.recovery_count,
        )

        if replan_resp.status == ReasoningStatus.SUCCESS and replan_resp.structured_plan:
            AuditLogger.log_event(
                "REPLAN_GENERATED",
                {
                    "request_id": norm_req.request_id,
                    "plan_id": replan_resp.structured_plan.plan_id,
                    "steps_count": len(replan_resp.structured_plan.steps),
                },
            )
            # Replace remaining plan with recovery plan
            state.current_plan = replan_resp.structured_plan
            state.current_step_index = 0
            state.consecutive_failure_count = 0
            return True

        AuditLogger.log_event(
            "REPLAN_FAILED",
            {
                "request_id": norm_req.request_id,
                "reason": replan_resp.warnings or "Recovery plan generation failed",
            },
        )
        return False

    def _build_final_result(
        self,
        state: OrchestrationState,
        status: OrchestrationStatus,
        message: str,
        start_time: float,
    ) -> OrchestrationResult:
        state.current_status = status
        duration = time.time() - start_time

        failures: List[Dict[str, Any]] = [
            {"step_id": s.step_id, "error": s.error, "capability": s.required_capability}
            for s in state.failed_steps
        ]
        twin_id = None
        if state.executive_twin_recommendation:
            twin_id = state.executive_twin_recommendation.executive_twin_id

        return OrchestrationResult(
            request_id=state.request.request_id,
            final_status=status,
            completed_steps=list(state.completed_steps),
            failed_steps=list(state.failed_steps),
            skipped_steps=list(state.skipped_steps),
            outputs=dict(state.outputs),
            artifacts=list(state.artifacts),
            evidence=state.evidence_set,
            failures=failures,
            recovery_history=[],
            final_message=message,
            memory_writeback_status=state.memory_writeback_status,
            iterations_run=state.iteration_count,
            recovery_attempts=state.recovery_count,
            duration_seconds=duration,
            executive_twin_id=twin_id,
        )
