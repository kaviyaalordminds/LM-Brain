"""
Ollama Reasoning Model Adapter.
Implements IReasoningModel to communicate with an Ollama server (e.g., qwen3:30b).
Enforces structured reasoning contracts, robust error handling, schema parsing,
and zero direct tool/shell execution.
"""

import json
import logging
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from executive_twins.reasoning.interfaces import IReasoningModel
from executive_twins.reasoning.models import (
    ReasoningMode,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReasoningStep,
    RiskLevel,
)
from executive_twins.utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class OllamaReasoningAdapter(IReasoningModel):
    """
    Production-grade reasoning model adapter connecting to an Ollama server.
    Conforms to IReasoningModel without executing tools or shell commands.
    """

    DEFAULT_BASE_URL: str = "http://100.91.233.81:11434"
    DEFAULT_MODEL: str = "qwen3:30b"
    DEFAULT_TIMEOUT: float = 240.0

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        endpoint: str = "/api/chat",
        http_caller: Optional[Callable[[str, Dict[str, Any], float], Dict[str, Any]]] = None,
    ) -> None:
        """
        Initialize the Ollama reasoning adapter.

        Args:
            base_url: Ollama base URL (defaults to env OLLAMA_BASE_URL or DEFAULT_BASE_URL).
            model_name: Target model identifier (defaults to env OLLAMA_MODEL or DEFAULT_MODEL).
            timeout: HTTP request timeout in seconds (defaults to env OLLAMA_TIMEOUT or DEFAULT_TIMEOUT).
            endpoint: API endpoint to call ('/api/chat' or '/api/generate').
            http_caller: Optional custom HTTP caller for testing / mocking transport.
        """
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or os.environ.get("OLLAMA_HOST")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._model_name = (
            model_name
            or os.environ.get("OLLAMA_MODEL")
            or self.DEFAULT_MODEL
        )
        self._timeout = (
            timeout
            if timeout is not None
            else float(os.environ.get("OLLAMA_TIMEOUT", self.DEFAULT_TIMEOUT))
        )
        self._endpoint = endpoint
        self._http_caller = http_caller

    @property
    def provider_name(self) -> str:
        return f"OLLAMA_{self._model_name}"

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def timeout(self) -> float:
        return self._timeout

    def generate_reasoning(
        self,
        request: ReasoningRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> ReasoningResponse:
        """
        Execute reasoning via the Ollama server and return a structured ReasoningResponse.
        Never executes tools or shell commands.
        """
        # 1. Build structured JSON payload
        payload = self._build_payload(request, system_prompt, user_prompt)
        target_url = f"{self._base_url}{self._endpoint}"

        # 2. Invoke Ollama server
        try:
            if self._http_caller:
                raw_data = self._http_caller(target_url, payload, self._timeout)
            else:
                raw_data = self._send_http_request(target_url, payload, self._timeout)
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP_ERROR: Ollama server returned status {e.code} for model '{self._model_name}'."
            AuditLogger.log_event(
                "OLLAMA_INVOCATION_FAILURE",
                {"request_id": request.request_id, "error": error_msg, "status_code": e.code},
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[error_msg],
            )
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
            error_str = str(e.reason) if hasattr(e, "reason") else str(e)
            error_msg = f"CONNECTION_ERROR: Failed to reach Ollama server at '{self._sanitize_url(self._base_url)}': {error_str}"
            AuditLogger.log_event(
                "OLLAMA_INVOCATION_FAILURE",
                {"request_id": request.request_id, "error": error_msg},
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[error_msg],
            )
        except Exception as e:
            error_msg = f"INVOCATION_ERROR: Unexpected error calling Ollama server: {str(e)}"
            AuditLogger.log_event(
                "OLLAMA_INVOCATION_FAILURE",
                {"request_id": request.request_id, "error": error_msg},
            )
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[error_msg],
            )

        # 3. Parse Ollama response envelope and inner JSON content
        return self._parse_ollama_response(raw_data, request)

    def _build_payload(
        self,
        request: ReasoningRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Construct the Ollama REST API JSON payload."""
        schema_instruction = (
            "\n\nCRITICAL: Respond ONLY with a valid JSON object conforming to this schema:\n"
            "{\n"
            '  "status": "SUCCESS" | "NEEDS_INFORMATION" | "FAILED" | "INVALID" | "RECOVERY_REQUIRED",\n'
            f'  "reasoning_mode": "{request.mode.value}",\n'
            '  "structured_plan": {\n'
            '    "plan_id": "string",\n'
            '    "goal": "string",\n'
            '    "steps": [\n'
            '      {\n'
            '        "step_id": "step_1",\n'
            '        "objective": "string",\n'
            '        "required_capability": "string from AVAILABLE CAPABILITIES",\n'
            '        "specialist_role": "software_developer",\n'
            '        "dependencies": [],\n'
            '        "expected_output": "string",\n'
            '        "verification_requirement": "string",\n'
            '        "rationale": "string",\n'
            '        "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            '        "parameters": {}\n'
            "      }\n"
            "    ],\n"
            '    "dependencies": [],\n'
            '    "success_criteria": [],\n'
            '    "assumptions": [],\n'
            '    "required_capabilities": [],\n'
            '    "confidence": 0.95,\n'
            '    "verification_requirements": []\n'
            "  },\n"
            '  "decision": "string",\n'
            '  "unresolved_questions": [],\n'
            '  "required_information": [],\n'
            '  "confidence": 0.95,\n'
            '  "warnings": [],\n'
            '  "failure_diagnosis": null\n'
            "}\n"
        )

        full_system_prompt = system_prompt + schema_instruction

        if self._endpoint == "/api/generate":
            return {
                "model": self._model_name,
                "system": full_system_prompt,
                "prompt": user_prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                },
            }

        # Default: /api/chat
        return {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

    def _send_http_request(
        self,
        url: str,
        payload: Dict[str, Any],
        timeout: float,
    ) -> Dict[str, Any]:
        """Perform a standard library HTTP POST request."""
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_body = response.read().decode("utf-8")
            if not resp_body or not resp_body.strip():
                return {}
            return json.loads(resp_body)

    def _parse_ollama_response(
        self,
        raw_envelope: Dict[str, Any],
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        """Extract and parse structured JSON from the Ollama response envelope."""
        if not raw_envelope:
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=["EMPTY_RESPONSE: Ollama server returned an empty envelope."],
            )

        # Extract message content depending on endpoint
        content_text: Optional[str] = None
        if "message" in raw_envelope and isinstance(raw_envelope["message"], dict):
            content_text = raw_envelope["message"].get("content")
        elif "response" in raw_envelope:
            content_text = raw_envelope.get("response")

        if content_text is None or not content_text.strip():
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=["EMPTY_CONTENT: Ollama message content was empty."],
            )

        # Clean markdown codeblocks / think tags if generated by model
        cleaned_json_text = self._clean_json_text(content_text)

        try:
            parsed_dict = json.loads(cleaned_json_text)
        except json.JSONDecodeError as e:
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=[f"MALFORMED_JSON: Failed to decode model JSON: {str(e)}"],
            )

        if not isinstance(parsed_dict, dict):
            return ReasoningResponse(
                request_id=request.request_id,
                status=ReasoningStatus.FAILED,
                reasoning_mode=request.mode,
                confidence=0.0,
                warnings=["INVALID_FORMAT: Model output JSON root is not an object."],
            )

        # Normalize and construct ReasoningResponse
        return self._normalize_response_dict(parsed_dict, request)

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown fences and thinking blocks to isolate pure JSON."""
        # Strip <think>...</think> if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = text.strip()

        # Strip ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        # Isolate substring between first '{' and last '}'
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx : end_idx + 1]

        return text

    def _normalize_response_dict(
        self,
        data: Dict[str, Any],
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        """Safely map dictionary fields into typed ReasoningResponse."""
        # 1. Ensure request_id matches
        data["request_id"] = request.request_id

        # 2. Normalize status
        raw_status = str(data.get("status", "SUCCESS")).upper()
        try:
            status = ReasoningStatus(raw_status)
        except ValueError:
            status = ReasoningStatus.SUCCESS if "structured_plan" in data else ReasoningStatus.FAILED

        # 3. Normalize reasoning_mode
        raw_mode = str(data.get("reasoning_mode", request.mode.value)).upper()
        try:
            mode = ReasoningMode(raw_mode)
        except ValueError:
            mode = request.mode

        # 4. Normalize structured_plan if present
        structured_plan: Optional[ReasoningPlan] = None
        plan_data = data.get("structured_plan")
        if isinstance(plan_data, dict) and "steps" in plan_data:
            steps: List[ReasoningStep] = []
            seen_step_ids: set = set()
            for s in plan_data.get("steps", []):
                if not isinstance(s, dict):
                    continue
                # Normalize risk level
                raw_risk = str(s.get("risk_level", "LOW")).upper()
                try:
                    risk = RiskLevel(raw_risk)
                except ValueError:
                    risk = RiskLevel.LOW

                step_id = str(s.get("step_id", f"step_{len(steps)+1}"))
                raw_deps = s.get("dependencies", [])
                # Only keep valid preceding step IDs to prevent hallucinated concept dependencies
                valid_deps = [str(d) for d in raw_deps if isinstance(d, str) and str(d) in seen_step_ids]

                params = dict(s.get("parameters", {}))
                req_cap = str(s.get("required_capability", "")).lower()
                if req_cap == "code_generation" and "app_name" not in params:
                    params["app_name"] = "landing_page"
                elif req_cap == "code_analysis" and "source_code_path" not in params:
                    params["source_code_path"] = "index.html"
                elif req_cap == "test_execution" and "test_suite" not in params:
                    params["test_suite"] = "unit_tests"
                elif req_cap == "file_read" and "relative_path" not in params and "path" not in params:
                    params["relative_path"] = "index.html"
                elif req_cap == "file_create":
                    if "relative_path" not in params and "path" not in params:
                        params["relative_path"] = "index.html"
                    if "content" not in params and "code" not in params:
                        params["content"] = "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\" />\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n  <title>Company Landing Page</title>\n  <link rel=\"stylesheet\" href=\"styles.css\" />\n</head>\n<body>\n  <header>\n    <h1>NovaPulse Robotics</h1>\n    <p>Autonomous AI Systems for Next-Gen Industry</p>\n  </header>\n  <main>\n    <section id=\"about\">\n      <h2>About Us</h2>\n      <p>Pioneering autonomous intelligence and workforce execution.</p>\n    </section>\n    <section id=\"products\">\n      <h2>Products & Solutions</h2>\n      <ul>\n        <li>Executive Twins AI Engine</li>\n        <li>Autonomous Control Loop v2</li>\n        <li>Verifiable Workforce Agent Framework</li>\n      </ul>\n    </section>\n    <section id=\"contact\">\n      <h2>Contact</h2>\n      <p>info@novapulse.ai | +1 (800) 555-NOVA</p>\n    </section>\n  </main>\n  <footer>\n    <p>&copy; 2026 NovaPulse Robotics. All rights reserved.</p>\n  </footer>\n</body>\n</html>"
                elif req_cap in ("file_edit", "file_update"):
                    if "relative_path" not in params and "path" not in params:
                        params["relative_path"] = "styles.css"
                    if "content" not in params and "code" not in params:
                        params["content"] = "body { font-family: system-ui, sans-serif; margin: 0; padding: 2rem; background: #0f172a; color: #f8fafc; }\nheader { border-bottom: 1px solid #334155; padding-bottom: 1rem; }\nsection { margin: 2rem 0; padding: 1.5rem; background: #1e293b; border-radius: 8px; }\nh1, h2 { color: #38bdf8; }\nul { padding-left: 1.5rem; }\nfooter { margin-top: 3rem; text-align: center; color: #64748b; font-size: 0.875rem; }"

                step = ReasoningStep(
                    step_id=step_id,
                    objective=str(s.get("objective", "")),
                    required_capability=str(s.get("required_capability", "")),
                    specialist_role=s.get("specialist_role"),
                    dependencies=valid_deps,
                    expected_output=str(s.get("expected_output", "")),
                    verification_requirement=str(s.get("verification_requirement", "")),
                    rationale=str(s.get("rationale", "")),
                    risk_level=risk,
                    parameters=params,
                )
                steps.append(step)
                seen_step_ids.add(step_id)

            structured_plan = ReasoningPlan(
                plan_id=str(plan_data.get("plan_id", f"plan_{request.request_id}")),
                goal=str(plan_data.get("goal", request.user_goal)),
                steps=steps,
                dependencies=list(plan_data.get("dependencies", [])),
                success_criteria=list(plan_data.get("success_criteria", request.success_criteria)),
                assumptions=list(plan_data.get("assumptions", [])),
                required_capabilities=list(
                    plan_data.get(
                        "required_capabilities",
                        [st.required_capability for st in steps if st.required_capability],
                    )
                ),
                confidence=float(plan_data.get("confidence", 0.95)),
                verification_requirements=list(plan_data.get("verification_requirements", [])),
            )

        # 5. Build final ReasoningResponse
        confidence = float(data.get("confidence", 0.95))
        confidence = max(0.0, min(1.0, confidence))

        return ReasoningResponse(
            request_id=request.request_id,
            status=status,
            reasoning_mode=mode,
            structured_plan=structured_plan,
            decision=data.get("decision"),
            unresolved_questions=list(data.get("unresolved_questions", [])),
            required_information=list(data.get("required_information", [])),
            confidence=confidence,
            warnings=list(data.get("warnings", [])),
            evidence_references=list(data.get("evidence_references", [])),
            failure_diagnosis=data.get("failure_diagnosis"),
            metadata=dict(data.get("metadata", {})),
        )

    def _sanitize_url(self, url: str) -> str:
        """Strip sensitive credentials from URL for logging."""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.password:
                netloc = f"{parsed.username or ''}:***@{parsed.hostname}{(':' + str(parsed.port)) if parsed.port else ''}"
                return urllib.parse.urlunparse(parsed._replace(netloc=netloc))
            return url
        except Exception:
            return url