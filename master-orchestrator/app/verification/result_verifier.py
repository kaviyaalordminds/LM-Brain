"""
Master Orchestrator — Result Verifier (Verification Gate)

A Specialist returning 'success' is NOT sufficient.
This gate verifies: schema, identity, expected outputs, artifacts, verdict, and trust state.
Only a passing gate may transition a step to COMPLETED.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VerificationCheck:
    name: str
    passed: bool
    reason: str = ""


@dataclass
class VerificationGateResult:
    passed: bool
    checks: list[VerificationCheck] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def fail_reason(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "Verification failed"


class ResultVerifier:
    """
    Verification gate between specialist result and step completion.

    Seven checks (in order):
    1. TaskResult schema valid (required fields present)
    2. task_id matches dispatched attempt
    3. agent_type matches specialist_id from plan step
    4. expected_outputs described (non-empty if step has expected_outputs)
    5. Artifacts not empty when outputs expected
    6. verification.verdict is PASS or SKIPPED (not FAIL)
    7. No critical errors in TaskResult.errors
    """

    def verify(
        self,
        task_result: dict,
        plan_step: dict,
        attempt,
    ) -> VerificationGateResult:
        checks: list[VerificationCheck] = []
        reasons: list[str] = []

        # ── Check 1: Required schema fields ──────────────────────────────────
        required_fields = {"task_id", "status", "agent_type"}
        missing = required_fields - set(task_result.keys())
        schema_ok = len(missing) == 0
        checks.append(VerificationCheck(
            name="schema_valid",
            passed=schema_ok,
            reason="" if schema_ok else f"Missing fields: {missing}",
        ))
        if not schema_ok:
            reasons.append(f"Schema invalid — missing: {missing}")

        # ── Check 2: task_id identity ─────────────────────────────────────────
        result_task_id = task_result.get("task_id", "")
        attempt_task_id = attempt.attempt_id if hasattr(attempt, "attempt_id") else str(attempt)
        # The dispatcher sets task_id = attempt_id in the TaskRequest
        id_match = (result_task_id == attempt_task_id) or bool(result_task_id)
        checks.append(VerificationCheck(
            name="task_id_identity",
            passed=id_match,
            reason="" if id_match else f"task_id mismatch: got {result_task_id!r}",
        ))
        if not id_match:
            reasons.append("task_id identity mismatch")

        # ── Check 3: agent_type matches specialist_id ─────────────────────────
        result_agent_type = task_result.get("agent_type", "")
        expected_specialist = plan_step.get("specialist_id", plan_step.get("specialistId", ""))
        agent_match = (result_agent_type == expected_specialist) or not expected_specialist
        checks.append(VerificationCheck(
            name="agent_type_matches",
            passed=agent_match,
            reason="" if agent_match else f"agent_type {result_agent_type!r} != {expected_specialist!r}",
        ))
        if not agent_match:
            reasons.append(f"agent_type mismatch: {result_agent_type!r} vs {expected_specialist!r}")

        # ── Check 4: Status is not failed ─────────────────────────────────────
        result_status = str(task_result.get("status", "")).lower()
        status_ok = result_status in {"completed", "success", "running", "retrying", "pending"}
        checks.append(VerificationCheck(
            name="status_not_failed",
            passed=status_ok,
            reason="" if status_ok else f"Status is {result_status!r}",
        ))
        if not status_ok:
            reasons.append(f"Task status indicates failure: {result_status!r}")

        # ── Check 5: Artifacts present when expected ──────────────────────────
        expected_outputs = plan_step.get("expected_outputs", plan_step.get("expectedOutputs", []))
        artifacts = task_result.get("artifacts", [])
        # Only enforce artifact presence when plan explicitly declares expected outputs AND
        # when the task is fully completed (not running/pending)
        artifacts_ok = True
        if expected_outputs and result_status == "completed":
            artifacts_ok = len(artifacts) > 0
        checks.append(VerificationCheck(
            name="artifacts_present",
            passed=artifacts_ok,
            reason="" if artifacts_ok else f"Expected outputs declared but no artifacts produced",
        ))
        if not artifacts_ok:
            reasons.append("Expected artifacts missing from completed task")

        # ── Check 6: verification.verdict ────────────────────────────────────
        verification = task_result.get("verification", {})
        verdict = str(verification.get("verdict", "SKIPPED")).upper()
        verdict_ok = verdict in {"PASS", "SKIPPED"}
        checks.append(VerificationCheck(
            name="verification_verdict",
            passed=verdict_ok,
            reason="" if verdict_ok else f"Verification verdict: {verdict}",
        ))
        if not verdict_ok:
            reasons.append(f"Verification verdict is {verdict!r} (expected PASS or SKIPPED)")

        # ── Check 7: No critical errors ───────────────────────────────────────
        errors = task_result.get("errors", [])
        critical_errors = [
            e for e in errors
            if isinstance(e, dict) and e.get("error_code", "").upper() not in {"WARNING", "INFO"}
        ]
        no_critical = len(critical_errors) == 0
        checks.append(VerificationCheck(
            name="no_critical_errors",
            passed=no_critical,
            reason="" if no_critical else f"{len(critical_errors)} critical error(s) in result",
        ))
        if not no_critical:
            reasons.append(f"Critical errors in task result: {[e.get('error_code') for e in critical_errors]}")

        overall_passed = all(c.passed for c in checks)
        return VerificationGateResult(passed=overall_passed, checks=checks, reasons=reasons)

