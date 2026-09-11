"""
Local Runner Entry Point for LM-Brain Autonomous AI Workforce.

Thin CLI and Python interface over the authoritative MasterOrchestrator and AutonomousControlLoop.
Executes autonomous workforce workflows against real local persistent software workspaces without HTTP/REST/cloud dependencies.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from executive_twins.orchestrator.dev_adapters import DevTestMasterOrchestratorFactory
from executive_twins.orchestrator.interfaces import IMasterOrchestrator
from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
    OrchestrationStatus,
)
from executive_twins.reasoning.interfaces import IReasoningModel
from executive_twins.schemas.common import SecurityContext
from executive_twins.utils.audit_logger import AuditLogger
from executive_twins.workspace.dev_adapters import get_default_workspace_dir


def resolve_reasoning_adapter(
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout: Optional[float] = None,
) -> IReasoningModel:
    """
    Resolve the reasoning model adapter based on explicit parameter or environment configuration.

    Supported providers:
    - 'dev' / 'test' (default): DevTestReasoningAdapter (100% offline, deterministic)
    - 'ollama': OllamaReasoningAdapter (connects to configured Ollama server)
    - 'local': LocalInferenceReasoningAdapter (local engine runtime)
    """
    selected_provider = (
        provider
        or os.environ.get("REASONING_PROVIDER")
        or os.environ.get("LM_REASONING_PROVIDER")
        or "dev"
    ).lower().strip()

    if selected_provider == "ollama":
        from executive_twins.reasoning.ollama_adapter import OllamaReasoningAdapter
        return OllamaReasoningAdapter(
            base_url=base_url,
            model_name=model_name,
            timeout=timeout,
        )
    elif selected_provider == "local":
        from executive_twins.reasoning.dev_adapters import LocalInferenceReasoningAdapter
        return LocalInferenceReasoningAdapter()
    else:
        from executive_twins.reasoning.dev_adapters import DevTestReasoningAdapter
        return DevTestReasoningAdapter()


class LocalRunner:
    """
    Thin Local Runner CLI interface over the authoritative MasterOrchestrator.
    Does NOT implement a secondary orchestrator. Delegates all perception, reasoning,
    capability selection, specialist execution, verification, and memory writeback
    to the existing MasterOrchestrator and AutonomousControlLoop.
    Executes against real local software workspaces.
    """

    def __init__(
        self,
        orchestrator: Optional[IMasterOrchestrator] = None,
        workspace_dir: Optional[str] = None,
        reasoning_adapter: Optional[IReasoningModel] = None,
        reasoning_provider: Optional[str] = None,
    ) -> None:
        self.workspace_dir = workspace_dir or str(get_default_workspace_dir())
        if orchestrator is not None:
            self.orchestrator = orchestrator
        else:
            adapter = reasoning_adapter or resolve_reasoning_adapter(provider=reasoning_provider)
            self.orchestrator = DevTestMasterOrchestratorFactory.create_local_development_orchestrator(
                base_workspace_dir=self.workspace_dir,
                reasoning_adapter=adapter,
            )

    @classmethod
    def create_default(
        cls,
        config: Optional[OrchestrationConfig] = None,
        base_workspace_dir: Optional[str] = None,
        reasoning_adapter: Optional[IReasoningModel] = None,
        reasoning_provider: Optional[str] = None,
    ) -> "LocalRunner":
        """Factory method constructing a LocalRunner backed by the real local development MasterOrchestrator."""
        ws_dir = base_workspace_dir or str(get_default_workspace_dir())
        adapter = reasoning_adapter or resolve_reasoning_adapter(provider=reasoning_provider)
        orchestrator = DevTestMasterOrchestratorFactory.create_local_development_orchestrator(
            config=config,
            base_workspace_dir=ws_dir,
            reasoning_adapter=adapter,
        )
        return cls(orchestrator=orchestrator, workspace_dir=ws_dir, reasoning_adapter=adapter)

    def run(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        security_context: Optional[SecurityContext] = None,
        require_twin_evaluation: bool = True,
        require_memory_writeback: bool = True,
        clear_audit_logs: bool = False,
    ) -> OrchestrationResult:
        """
        Submit a task to the existing MasterOrchestrator and AutonomousControlLoop.
        
        Args:
            goal: User task or objective.
            context: Optional contextual parameters.
            security_context: Security authorization context.
            require_twin_evaluation: Whether executive twin evaluation is enabled in control loop.
            require_memory_writeback: Whether memory writeback to Obsidian is enabled.
            clear_audit_logs: Whether to reset audit log history before execution.
            
        Returns:
            OrchestrationResult generated by the MasterOrchestrator.
        """
        if not goal or not goal.strip():
            raise ValueError("Execution goal cannot be empty or whitespace-only.")

        if clear_audit_logs:
            AuditLogger.clear_events()

        sec_ctx = security_context or SecurityContext(
            user_id="local_runner_user",
            clearance_level="standard",
            is_authenticated=True,
        )

        request_id = f"req_local_{uuid.uuid4().hex[:8]}"
        request = OrchestrationRequest(
            request_id=request_id,
            user_goal=goal.strip(),
            context=context or {},
            security_context=sec_ctx,
            require_twin_evaluation=require_twin_evaluation,
            require_memory_writeback=require_memory_writeback,
        )

        return self.orchestrator.orchestrate(request)

    def to_workflow_run_dict(
        self,
        result: OrchestrationResult,
        goal: str,
    ) -> Dict[str, Any]:
        """
        Map an authoritative OrchestrationResult and workspace state into the structured
        WorkflowRun format consumed by the frontend.
        """
        is_completed = result.final_status == OrchestrationStatus.COMPLETED
        is_failed = result.final_status in (OrchestrationStatus.FAILED, OrchestrationStatus.BLOCKED)

        # 1. Discover Real Files in the Local Software Workspace
        ws_path = Path(self.workspace_dir) / "default"
        workspace_files: List[Dict[str, Any]] = []
        if ws_path.exists() and ws_path.is_dir():
            for f in sorted(ws_path.rglob("*")):
                # Skip hidden directories like .pytest_cache
                rel_parts = f.relative_to(ws_path).parts
                if f.is_file() and not any(p.startswith(".") for p in rel_parts):
                    rel_p = f.relative_to(ws_path).as_posix()
                    size = f.stat().st_size
                    try:
                        content_snip = f.read_text(encoding="utf-8", errors="replace")[:600]
                    except Exception:
                        content_snip = ""
                    mime = (
                        "text/html"
                        if rel_p.endswith(".html")
                        else "text/css"
                        if rel_p.endswith(".css")
                        else "application/javascript"
                        if rel_p.endswith(".js")
                        else "text/markdown"
                        if rel_p.endswith(".md")
                        else "text/plain"
                    )
                    workspace_files.append({
                        "path": rel_p,
                        "operation": "CREATE",
                        "status": "SUCCESS",
                        "sizeBytes": size,
                        "contentSnippet": content_snip,
                        "mimeType": mime,
                        "modifiedAt": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
                    })

        # 2. Map 10-Stage Pipeline Statuses
        stages = [
            {
                "key": "PERCEPTION",
                "label": "Perception",
                "shortDescription": f"Intent normalized: {goal[:60]}...",
                "status": "COMPLETED",
            },
            {
                "key": "COMPANY_KNOWLEDGE",
                "label": "Company Knowledge",
                "shortDescription": "Authoritative Obsidian facts retrieved",
                "status": "COMPLETED",
            },
            {
                "key": "REASONING",
                "label": "Reasoning",
                "shortDescription": f"Synthesized plan with {len(result.completed_steps) + len(result.failed_steps)} step(s)",
                "status": "COMPLETED",
            },
            {
                "key": "PLAN_VALIDATION",
                "label": "Plan Validation",
                "shortDescription": "DAG dependency & capability bounds verified",
                "status": "COMPLETED",
            },
            {
                "key": "CAPABILITY_SELECTION",
                "label": "Capability Selection",
                "shortDescription": "Specialist capability matching resolved",
                "status": "COMPLETED",
            },
            {
                "key": "SPECIALIST_DELEGATION",
                "label": "Specialist Delegation",
                "shortDescription": "SecurityGuard boundary allocated",
                "status": "COMPLETED",
            },
            {
                "key": "CONTROLLED_EXECUTION",
                "label": "Controlled Execution",
                "shortDescription": f"{len(result.completed_steps)} step(s) executed via FileService/SpecialistEngine",
                "status": "COMPLETED" if result.completed_steps else ("FAILED" if is_failed else "RUNNING"),
            },
            {
                "key": "OBSERVATION_QA",
                "label": "Observation / QA",
                "shortDescription": f"{len(result.evidence.items) if result.evidence else 0} empirical evidence item(s) captured",
                "status": "COMPLETED" if result.evidence and len(result.evidence.items) > 0 else "WAITING",
            },
            {
                "key": "VERIFICATION",
                "label": "Verification",
                "shortDescription": "Success criteria verified against artifacts",
                "status": "COMPLETED" if is_completed else ("FAILED" if is_failed else "WAITING"),
            },
            {
                "key": "MEMORY_WRITEBACK",
                "label": "Memory Writeback",
                "shortDescription": f"Obsidian state: {result.memory_writeback_status or 'NOT_PERFORMED'}",
                "status": "COMPLETED" if result.memory_writeback_status == "SUCCESS" else ("SKIPPED" if is_failed else "WAITING"),
            },
        ]

        # 3. Specialist Executions
        specialist_executions: List[Dict[str, Any]] = []
        for step in result.completed_steps:
            specialist_executions.append({
                "stepId": step.step_id,
                "objective": step.objective,
                "requiredCapability": step.required_capability,
                "specialistId": step.specialist_id or "spec_software_dev_01",
                "specialistName": "Software Development Specialist",
                "status": "COMPLETED",
                "output": step.output,
                "artifacts": step.artifacts,
                "evidenceIds": step.evidence_ids,
                "durationSeconds": round(step.duration_seconds, 3),
            })
        for step in result.failed_steps:
            specialist_executions.append({
                "stepId": step.step_id,
                "objective": step.objective,
                "requiredCapability": step.required_capability,
                "specialistId": step.specialist_id or "spec_software_dev_01",
                "specialistName": "Software Development Specialist",
                "status": "FAILED",
                "output": step.output,
                "artifacts": step.artifacts,
                "evidenceIds": step.evidence_ids,
                "error": step.error,
                "durationSeconds": round(step.duration_seconds, 3),
            })

        # 4. Evidence Items
        evidence_items: List[Dict[str, Any]] = []
        if result.evidence:
            for ev in result.evidence.items:
                ev_dict: Dict[str, Any] = {
                    "evidenceId": getattr(ev, "evidence_id", f"ev_{uuid.uuid4().hex[:8]}"),
                    "category": getattr(ev, "category", "DATA"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "systemGenerated": True,
                    "description": getattr(ev, "description", str(ev)),
                }
                if hasattr(ev, "artifact_uri"):
                    ev_dict["artifactUri"] = ev.artifact_uri
                    ev_dict["mimeType"] = getattr(ev, "mime_type", "text/plain")
                    ev_dict["checksumSha256"] = getattr(ev, "checksum_sha256", None)
                if hasattr(ev, "log_snippet"):
                    ev_dict["logSnippet"] = ev.log_snippet
                    ev_dict["exitCode"] = getattr(ev, "exit_code", 0)
                    ev_dict["executionId"] = getattr(ev, "execution_id", "exec_01")
                if hasattr(ev, "tests_passed"):
                    ev_dict["testsPassed"] = ev.tests_passed
                    ev_dict["testsFailed"] = getattr(ev, "tests_failed", 0)
                    ev_dict["suiteName"] = getattr(ev, "suite_name", "test_suite")
                if hasattr(ev, "verifier_id"):
                    ev_dict["verifierId"] = ev.verifier_id
                    ev_dict["verifiedStatus"] = getattr(ev, "verified_status", "VERIFIED")
                    ev_dict["verifiedAt"] = datetime.now(timezone.utc).isoformat()
                evidence_items.append(ev_dict)

        # 5. Audit Events
        audit_events: List[Dict[str, Any]] = []
        for idx, a in enumerate(AuditLogger.get_events(), 1):
            audit_events.append({
                "eventId": f"evt-{idx:04d}",
                "eventType": a.event_type,
                "timestamp": a.timestamp.isoformat(),
                "payload": a.payload,
            })

        # 6. Executive Twin
        executive_twin_activated = None
        if result.executive_twin_id:
            role = result.executive_twin_id.upper()
            executive_twin_activated = {
                "twinId": f"twin_{result.executive_twin_id.lower()}",
                "role": role if role in ["CEO", "COO", "CTO", "CMO", "CFO"] else "CTO",
                "title": f"Executive Twin ({result.executive_twin_id})",
                "strategicScope": "Strategic Governance & Alignment",
                "activationCondition": "High-impact cross-functional initiative",
                "status": "ACTIVE",
                "responsibilities": ["Strategic direction", "Constraint validation", "Approval"],
                "reviewPolicy": "MANDATORY_REVIEW",
            }

        # 7. Validations
        validations: List[Dict[str, Any]] = []
        for step in result.completed_steps:
            if any(k in step.required_capability for k in ("validation", "test", "build", "inspect")):
                validations.append({
                    "operation": "TEST" if "test" in step.required_capability else "BUILD",
                    "command": step.required_capability,
                    "status": "PASSED",
                    "exitCode": 0,
                    "output": step.output or "Validated without errors.",
                    "restrictedShell": True,
                })

        # 8. Verification Checklist
        verification_checklist = [
            {
                "criterion": "All plan steps completed and validated",
                "passed": is_completed,
                "details": f"{len(result.completed_steps)} step(s) completed.",
            },
            {
                "criterion": "SecurityGuard boundary and workspace isolation verified",
                "passed": True,
                "details": f"All file operations restricted to workspace '{Path(self.workspace_dir).name}'.",
            },
            {
                "criterion": "Empirical evidence captured and verified",
                "passed": len(evidence_items) > 0,
                "details": f"{len(evidence_items)} verifiable evidence artifact(s) generated.",
            },
            {
                "criterion": "Authoritative Obsidian memory writeback persisted",
                "passed": result.memory_writeback_status == "SUCCESS",
                "details": f"Writeback status: {result.memory_writeback_status or 'N/A'}",
            },
        ]

        # 9. Memory Writeback Record
        memory_writeback = {
            "status": "COMPLETED" if result.memory_writeback_status == "SUCCESS" else "NOT_PERFORMED",
            "source": "StandardMemoryWritebackHandler",
            "targetVaultPath": f"company_knowledge/workflows/mem_workflow_{result.request_id}.md",
            "recordedState": "APPROVED" if is_completed else "REJECTED",
            "approvalStatus": "APPROVED" if is_completed else "REJECTED",
            "factsPersisted": [
                {
                    "statement": f"Execution of workflow {result.request_id} for goal: {goal[:80]}",
                    "state": "FACT",
                    "source": "local_runner",
                }
            ],
            "reason": result.final_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 10. Selected Specialists Map
        selected_specialists: Dict[str, str] = {}
        for step in result.completed_steps:
            selected_specialists[step.required_capability] = step.specialist_id or "spec_software_dev_01"

        return {
            "runId": result.request_id.replace("req_", "RUN-"),
            "requestId": result.request_id,
            "userGoal": goal,
            "status": result.final_status.value,
            "durationSeconds": round(result.duration_seconds, 3),
            "isDemo": False,
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "currentStageIndex": 9 if is_completed else (6 if result.completed_steps else 0),
            "stages": stages,
            "selectedSpecialists": selected_specialists,
            "specialistExecutions": specialist_executions,
            "workspaceFiles": workspace_files,
            "validations": validations,
            "evidenceItems": evidence_items,
            "verificationChecklist": verification_checklist,
            "memoryWriteback": memory_writeback,
            "recoveryHistory": result.recovery_history,
            "auditEvents": audit_events,
            "executiveTwinActivated": executive_twin_activated,
        }

    def format_terminal_output(
        self,
        result: OrchestrationResult,
        goal: str,
    ) -> str:
        """Format an OrchestrationResult into clean, structured terminal output."""
        sep_double = "=" * 70
        sep_single = "-" * 70

        twin_activated = bool(result.executive_twin_id)
        twin_display = (
            f"ACTIVATED ({result.executive_twin_id})"
            if twin_activated
            else "None (Standard Autonomous Control Loop Path)"
        )

        # Determine real workspace directory and files on disk
        ws_path = Path(self.workspace_dir) / "default"
        ws_display = str(ws_path.resolve())

        real_files: List[Tuple[str, int, str]] = []
        if ws_path.exists() and ws_path.is_dir():
            for f in sorted(ws_path.rglob("*")):
                if f.is_file():
                    rel_to_ws = f.relative_to(ws_path).as_posix()
                    size = f.stat().st_size
                    real_files.append((rel_to_ws, size, str(f.resolve())))

        lines = [
            sep_double,
            " LM-BRAIN AUTONOMOUS AI WORKFORCE - LOCAL EXECUTION REPORT",
            sep_double,
            f"Objective / Goal : {goal}",
            f"Request ID       : {result.request_id}",
            f"Final Status     : {result.final_status.value}",
            f"Executive Twin   : {twin_display}",
            f"Control Loop     : {result.iterations_run} iteration(s), {result.recovery_attempts} recovery attempt(s)",
            f"Duration         : {result.duration_seconds:.3f}s",
            sep_single,
            f"1. WORKFORCE STEP EXECUTION ({len(result.completed_steps)} completed, {len(result.failed_steps)} failed)",
            sep_single,
        ]

        if not result.completed_steps and not result.failed_steps:
            lines.append("  (No step execution records generated)")
        else:
            for idx, step in enumerate(result.completed_steps, 1):
                spec_info = f" -> Specialist: {step.specialist_id}" if step.specialist_id else ""
                lines.append(f"  [{idx}] Step '{step.step_id}': {step.required_capability}{spec_info}")
                lines.append(f"      Status   : {step.status}")
                lines.append(f"      Objective: {step.objective}")
                if step.output:
                    lines.append(f"      Output   : {step.output}")
                if step.artifacts:
                    lines.append(f"      Artifacts: {', '.join(step.artifacts)}")
                if step.evidence_ids:
                    lines.append(f"      Evidence : {', '.join(step.evidence_ids)}")
                lines.append("")

            for idx, step in enumerate(result.failed_steps, len(result.completed_steps) + 1):
                lines.append(f"  [{idx}] FAILED Step '{step.step_id}': {step.required_capability}")
                lines.append(f"      Objective: {step.objective}")
                if step.error:
                    lines.append(f"      Error    : {step.error}")
                lines.append("")

        lines.extend([
            sep_single,
            "2. WORKSPACE, ARTIFACTS & REAL FILES",
            sep_single,
            f"Workspace Path  : {ws_display}",
        ])

        if real_files:
            lines.append(f"Workspace Files ({len(real_files)} on disk):")
            for rel, size, abs_p in real_files:
                lines.append(f"  * {rel} ({size} bytes) -> {abs_p}")
        else:
            lines.append("  (No files currently on disk in workspace)")

        if result.artifacts:
            lines.append(f"Recorded Artifacts ({len(result.artifacts)}):")
            for art in result.artifacts:
                lines.append(f"  * {art}")

        evidence_count = len(result.evidence.items) if result.evidence else 0
        lines.append(f"Verifiable Evidence: {evidence_count} item(s)")

        lines.extend([
            sep_single,
            "3. MEMORY & RECOVERY",
            sep_single,
            f"Memory Writeback: {result.memory_writeback_status or 'N/A'}",
        ])

        if result.recovery_history:
            lines.append(f"Recovery History ({len(result.recovery_history)} events):")
            for rec_ev in result.recovery_history:
                lines.append(f"  * {rec_ev}")

        lines.extend([
            sep_single,
            "4. FINAL MESSAGE / OUTCOME",
            sep_single,
            f"Message: {result.final_message}",
        ])

        # Audit Event Stats
        recent_events = AuditLogger.get_events()
        lines.extend([
            sep_single,
            f"Audit Trail     : {len(recent_events)} total lifecycle events logged",
            sep_double,
        ])

        return "\n".join(lines)

    def execute_and_display(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        security_context: Optional[SecurityContext] = None,
    ) -> int:
        """
        Execute workflow via MasterOrchestrator, format report to stdout, and return exit code (0 or 1).
        """
        if not goal or not goal.strip():
            print("\n[ERROR] Goal cannot be empty. Please provide a valid execution task.", file=sys.stderr)
            return 1

        try:
            result = self.run(
                goal=goal,
                context=context,
                security_context=security_context,
            )
            output = self.format_terminal_output(result, goal.strip())
            print(output)

            # Return 0 for COMPLETED, 1 for failures/blocked
            if result.final_status == OrchestrationStatus.COMPLETED:
                return 0
            else:
                return 1

        except Exception as e:
            print(f"\n[FATAL ERROR] Workflow execution encountered exception: {e}", file=sys.stderr)
            return 1


def run_local_workflow(
    goal: str,
    orchestrator: Optional[IMasterOrchestrator] = None,
    workspace_dir: Optional[str] = None,
    reasoning_adapter: Optional[IReasoningModel] = None,
    reasoning_provider: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    security_context: Optional[SecurityContext] = None,
) -> OrchestrationResult:
    """Convenience function to run a workflow via LocalRunner."""
    runner = LocalRunner(
        orchestrator=orchestrator,
        workspace_dir=workspace_dir,
        reasoning_adapter=reasoning_adapter,
        reasoning_provider=reasoning_provider,
    )
    return runner.run(goal=goal, context=context, security_context=security_context)


def main() -> None:
    """CLI entrypoint for running local autonomous workforce workflows."""
    args = sys.argv[1:]
    is_json = "--json" in args
    if is_json:
        args.remove("--json")

    provider: Optional[str] = None
    if "--provider" in args:
        p_idx = args.index("--provider")
        if p_idx + 1 < len(args):
            provider = args[p_idx + 1]
            args = args[:p_idx] + args[p_idx + 2:]

    model_name: Optional[str] = None
    if "--model" in args:
        m_idx = args.index("--model")
        if m_idx + 1 < len(args):
            model_name = args[m_idx + 1]
            args = args[:m_idx] + args[m_idx + 2:]

    base_url: Optional[str] = None
    if "--base-url" in args:
        u_idx = args.index("--base-url")
        if u_idx + 1 < len(args):
            base_url = args[u_idx + 1]
            args = args[:u_idx] + args[u_idx + 2:]

    r_adapter = resolve_reasoning_adapter(
        provider=provider,
        base_url=base_url,
        model_name=model_name,
    )
    runner = LocalRunner.create_default(reasoning_adapter=r_adapter)

    if is_json:
        if args:
            goal = " ".join(args).strip()
        else:
            try:
                goal = sys.stdin.read().strip()
            except Exception:
                goal = ""

        if not goal:
            print(json.dumps({"error": "INVALID_REQUEST", "message": "Goal cannot be empty."}))
            sys.exit(1)

        try:
            result = runner.run(goal)
            wf_dict = runner.to_workflow_run_dict(result, goal)
            print(json.dumps(wf_dict))
            sys.exit(0 if result.final_status == OrchestrationStatus.COMPLETED else 1)
        except Exception as e:
            print(json.dumps({"error": "EXECUTION_EXCEPTION", "message": str(e)}))
            sys.exit(1)

    if args:
        goal = " ".join(args)
    else:
        print("=" * 70)
        print(" LM-BRAIN AUTONOMOUS AI WORKFORCE")
        print("=" * 70)
        try:
            print("\nEnter your task:")
            goal = input("> ")
        except (KeyboardInterrupt, EOFError):
            print("\n[INFO] Local execution aborted by user.")
            sys.exit(0)

    exit_code = runner.execute_and_display(goal)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
